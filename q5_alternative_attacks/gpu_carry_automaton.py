#!/usr/bin/env python3
"""
GPU Carry Automaton Width Profiler

Key question from the Rotation Frontier Theorem: does carry automaton
width grow polynomially or exponentially with N?

At N=4: 49 collisions, ~49 carry states (from carry entropy theorem)
At N=8: 260 collisions, ~260 carry states

This tool directly measures the carry automaton WIDTH at each bit
position by evaluating ALL collision solutions' carry patterns.

Uses the N=8 collision data (260 solutions from cascade DP) to:
1. Extract carry vectors for each collision
2. At each bit position, count distinct carry states
3. Plot the automaton width profile

The width profile tells us whether the automaton is bounded (polynomial
= tractable at N=32) or explosive (exponential = infeasible).

GPU accelerates the carry extraction: evaluate 260 solutions × 7 rounds
× multiple additions in parallel.
"""
import sys, os, time
import numpy as np

K32 = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]


def scale_rot(k, N):
    return max(1, round(k * N / 32))


class MiniSHA:
    def __init__(self, N):
        self.N = N
        self.MASK = (1 << N) - 1
        self.MSB = 1 << (N-1)
        self.rS0 = [scale_rot(2,N), scale_rot(13,N), scale_rot(22,N)]
        self.rS1 = [scale_rot(6,N), scale_rot(11,N), scale_rot(25,N)]
        self.rs0 = [scale_rot(7,N), scale_rot(18,N)]; self.ss0 = scale_rot(3,N)
        self.rs1 = [scale_rot(17,N), scale_rot(19,N)]; self.ss1 = scale_rot(10,N)
        self.K = [k & self.MASK for k in K32]
        self.IV = [v & self.MASK for v in [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
                                             0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]]

    def ror(self, x, k):
        k = k % self.N; return ((x >> k) | (x << (self.N - k))) & self.MASK
    def Sigma0(self, a): return self.ror(a,self.rS0[0])^self.ror(a,self.rS0[1])^self.ror(a,self.rS0[2])
    def Sigma1(self, e): return self.ror(e,self.rS1[0])^self.ror(e,self.rS1[1])^self.ror(e,self.rS1[2])
    def sigma0(self, x): return self.ror(x,self.rs0[0])^self.ror(x,self.rs0[1])^((x>>self.ss0)&self.MASK)
    def sigma1(self, x): return self.ror(x,self.rs1[0])^self.ror(x,self.rs1[1])^((x>>self.ss1)&self.MASK)
    def Ch(self, e, f, g): return (e & f) ^ ((~e & self.MASK) & g)
    def Maj(self, a, b, c): return (a & b) ^ (a & c) ^ (b & c)

    def compress_57(self, M):
        W = list(M) + [0]*48
        for i in range(16, 64):
            W[i] = (self.sigma1(W[i-2]) + W[i-7] + self.sigma0(W[i-15]) + W[i-16]) & self.MASK
        a,b,c,d,e,f,g,h = self.IV
        for i in range(57):
            T1 = (h + self.Sigma1(e) + self.Ch(e,f,g) + self.K[i] + W[i]) & self.MASK
            T2 = (self.Sigma0(a) + self.Maj(a,b,c)) & self.MASK
            h,g,f,e,d,c,b,a = g,f,e,(d+T1)&self.MASK,c,b,a,(T1+T2)&self.MASK
        return [a,b,c,d,e,f,g,h], W[:57]


def extract_addition_carries(a, b, N):
    """Extract all N-1 carry bits from a + b mod 2^N."""
    carries = []
    c = 0
    for bit in range(N):
        total = ((a >> bit) & 1) + ((b >> bit) & 1) + c
        c = total >> 1
        if bit < N - 1:
            carries.append(c)
    return carries


def extract_collision_carries(sha, s1, s2, W1p, W2p, w1, w2):
    """Extract ALL carry bits from the 7-round tail for one collision solution.

    Returns a list of carry bits (one per addition per bit position).
    """
    N = sha.N
    MASK = sha.MASK

    # Build full W arrays
    W1 = list(w1)
    W2 = list(w2)
    W1.append((sha.sigma1(w1[2]) + W1p[54] + sha.sigma0(W1p[46]) + W1p[45]) & MASK)
    W2.append((sha.sigma1(w2[2]) + W2p[54] + sha.sigma0(W2p[46]) + W2p[45]) & MASK)
    W1.append((sha.sigma1(w1[3]) + W1p[55] + sha.sigma0(W1p[47]) + W1p[46]) & MASK)
    W2.append((sha.sigma1(w2[3]) + W2p[55] + sha.sigma0(W2p[47]) + W2p[46]) & MASK)
    W1.append((sha.sigma1(W1[4]) + W1p[56] + sha.sigma0(W1p[48]) + W1p[47]) & MASK)
    W2.append((sha.sigma1(W2[4]) + W2p[56] + sha.sigma0(W2p[48]) + W2p[47]) & MASK)

    all_carries = []
    a1,b1,c1,d1,e1,f1,g1,h1 = s1
    a2,b2,c2,d2,e2,f2,g2,h2 = s2

    for rnd in range(7):
        # T1 additions for M1: h+Sig1(e), +Ch, +K, +W
        sig1_1 = sha.Sigma1(e1)
        ch1 = sha.Ch(e1, f1, g1)
        t1 = (h1 + sig1_1) & MASK
        all_carries.extend(extract_addition_carries(h1, sig1_1, N))
        t2 = (t1 + ch1) & MASK
        all_carries.extend(extract_addition_carries(t1, ch1, N))
        t3 = (t2 + sha.K[57+rnd]) & MASK
        all_carries.extend(extract_addition_carries(t2, sha.K[57+rnd], N))
        T1_1 = (t3 + W1[rnd]) & MASK
        all_carries.extend(extract_addition_carries(t3, W1[rnd], N))

        # T2 for M1: Sig0(a)+Maj
        sig0_1 = sha.Sigma0(a1)
        maj1 = sha.Maj(a1, b1, c1)
        T2_1 = (sig0_1 + maj1) & MASK
        all_carries.extend(extract_addition_carries(sig0_1, maj1, N))

        # a = T1+T2, e = d+T1
        new_a1 = (T1_1 + T2_1) & MASK
        all_carries.extend(extract_addition_carries(T1_1, T2_1, N))
        new_e1 = (d1 + T1_1) & MASK
        all_carries.extend(extract_addition_carries(d1, T1_1, N))

        h1,g1,f1,e1,d1,c1,b1,a1 = g1,f1,e1,new_e1,c1,b1,a1,new_a1

        # Same for M2
        sig1_2 = sha.Sigma1(e2); ch2 = sha.Ch(e2, f2, g2)
        t1 = (h2 + sig1_2) & MASK
        all_carries.extend(extract_addition_carries(h2, sig1_2, N))
        t2 = (t1 + ch2) & MASK
        all_carries.extend(extract_addition_carries(t1, ch2, N))
        t3 = (t2 + sha.K[57+rnd]) & MASK
        all_carries.extend(extract_addition_carries(t2, sha.K[57+rnd], N))
        T1_2 = (t3 + W2[rnd]) & MASK
        all_carries.extend(extract_addition_carries(t3, W2[rnd], N))
        sig0_2 = sha.Sigma0(a2); maj2 = sha.Maj(a2, b2, c2)
        T2_2 = (sig0_2 + maj2) & MASK
        all_carries.extend(extract_addition_carries(sig0_2, maj2, N))
        new_a2 = (T1_2 + T2_2) & MASK
        all_carries.extend(extract_addition_carries(T1_2, T2_2, N))
        new_e2 = (d2 + T1_2) & MASK
        all_carries.extend(extract_addition_carries(d2, T1_2, N))

        h2,g2,f2,e2,d2,c2,b2,a2 = g2,f2,e2,new_e2,c2,b2,a2,new_a2

    return all_carries


def find_collisions_and_profile(N=4):
    """Find all collisions at width N and profile their carry automaton."""
    sha = MiniSHA(N)
    MASK = sha.MASK

    # Find candidate
    fill = MASK
    m0 = None
    for m in range(0, 1 << min(N, 16)):
        M1 = [m & MASK] + [fill]*15; M2 = list(M1)
        M2[0] ^= sha.MSB; M2[9] ^= sha.MSB
        s1, W1p = sha.compress_57(M1); s2, W2p = sha.compress_57(M2)
        if s1[0] == s2[0]:
            m0 = m & MASK; break

    if m0 is None:
        # Try homotopy
        sys.path.insert(0, '.')
        spec = __import__('50_precision_homotopy')
        mini = spec.MiniSHA256(N)
        m0_h, _, _, _, _ = mini.find_m0()
        m0 = m0_h
        M1 = [m0] + [MASK]*15; M2 = list(M1)
        M2[0] ^= sha.MSB; M2[9] ^= sha.MSB
        s1, W1p = sha.compress_57(M1); s2, W2p = sha.compress_57(M2)

    print(f"N={N}, M[0]=0x{m0:x}", flush=True)

    # Cascade constant
    dh = (s1[7]-s2[7])&MASK
    dSig1 = (sha.Sigma1(s1[4])-sha.Sigma1(s2[4]))&MASK
    dCh = (sha.Ch(s1[4],s1[5],s1[6])-sha.Ch(s2[4],s2[5],s2[6]))&MASK
    T2_1 = (sha.Sigma0(s1[0])+sha.Maj(s1[0],s1[1],s1[2]))&MASK
    T2_2 = (sha.Sigma0(s2[0])+sha.Maj(s2[0],s2[1],s2[2]))&MASK
    C_w57 = (dh+dSig1+dCh+(T2_1-T2_2))&MASK

    # Find all collisions via cascade DP
    print(f"Finding collisions via cascade DP (2^{4*N} search)...", flush=True)
    t0 = time.time()
    collisions = []

    def find_w2_off(st1, st2, rnd, w1k):
        r1 = (st1[7]+sha.Sigma1(st1[4])+sha.Ch(st1[4],st1[5],st1[6])+sha.K[rnd])&MASK
        r2 = (st2[7]+sha.Sigma1(st2[4])+sha.Ch(st2[4],st2[5],st2[6])+sha.K[rnd])&MASK
        t1 = (sha.Sigma0(st1[0])+sha.Maj(st1[0],st1[1],st1[2]))&MASK
        t2 = (sha.Sigma0(st2[0])+sha.Maj(st2[0],st2[1],st2[2]))&MASK
        return (w1k + r1 - r2 + t1 - t2) & MASK

    def sha_rnd(st, k, w):
        a,b,c,d,e,f,g,h = st
        T1 = (h+sha.Sigma1(e)+sha.Ch(e,f,g)+k+w)&MASK
        T2 = (sha.Sigma0(a)+sha.Maj(a,b,c))&MASK
        return [(T1+T2)&MASK, a, b, c, (d+T1)&MASK, e, f, g]

    for w57 in range(1 << N):
        st1_57 = list(s1); st2_57 = list(s2)
        w2_57 = find_w2_off(st1_57, st2_57, 57, w57)
        st1_57 = sha_rnd(st1_57, sha.K[57], w57)
        st2_57 = sha_rnd(st2_57, sha.K[57], w2_57)
        for w58 in range(1 << N):
            st1_58 = list(st1_57); st2_58 = list(st2_57)
            w2_58 = find_w2_off(st1_58, st2_58, 58, w58)
            st1_58 = sha_rnd(st1_58, sha.K[58], w58)
            st2_58 = sha_rnd(st2_58, sha.K[58], w2_58)
            for w59 in range(1 << N):
                st1_59 = list(st1_58); st2_59 = list(st2_58)
                w2_59 = find_w2_off(st1_59, st2_59, 59, w59)
                st1_59 = sha_rnd(st1_59, sha.K[59], w59)
                st2_59 = sha_rnd(st2_59, sha.K[59], w2_59)
                for w60 in range(1 << N):
                    st1_60 = list(st1_59); st2_60 = list(st2_59)
                    w2_60 = find_w2_off(st1_60, st2_60, 60, w60)
                    st1_60 = sha_rnd(st1_60, sha.K[60], w60)
                    st2_60 = sha_rnd(st2_60, sha.K[60], w2_60)
                    # Schedule
                    W1f = [w57,w58,w59,w60,0,0,0]
                    W2f = [w2_57,w2_58,w2_59,w2_60,0,0,0]
                    W1f[4]=(sha.sigma1(W1f[2])+W1p[54]+sha.sigma0(W1p[46])+W1p[45])&MASK
                    W2f[4]=(sha.sigma1(W2f[2])+W2p[54]+sha.sigma0(W2p[46])+W2p[45])&MASK
                    W1f[5]=(sha.sigma1(W1f[3])+W1p[55]+sha.sigma0(W1p[47])+W1p[46])&MASK
                    W2f[5]=(sha.sigma1(W2f[3])+W2p[55]+sha.sigma0(W2p[47])+W2p[46])&MASK
                    W1f[6]=(sha.sigma1(W1f[4])+W1p[56]+sha.sigma0(W1p[48])+W1p[47])&MASK
                    W2f[6]=(sha.sigma1(W2f[4])+W2p[56]+sha.sigma0(W2p[48])+W2p[47])&MASK
                    fs1 = list(st1_60); fs2 = list(st2_60)
                    for r in range(4,7):
                        fs1 = sha_rnd(fs1, sha.K[57+r], W1f[r])
                        fs2 = sha_rnd(fs2, sha.K[57+r], W2f[r])
                    if all(fs1[r]==fs2[r] for r in range(8)):
                        collisions.append(([w57,w58,w59,w60],[w2_57,w2_58,w2_59,w2_60]))

    elapsed = time.time() - t0
    print(f"Found {len(collisions)} collisions in {elapsed:.1f}s", flush=True)

    if not collisions:
        print("No collisions — can't profile carries", flush=True)
        return

    # Extract carry vectors for all collisions
    print(f"\nExtracting carry vectors...", flush=True)
    carry_matrix = []
    for w1, w2 in collisions:
        carries = extract_collision_carries(sha, s1, s2, W1p, W2p, w1, w2)
        carry_matrix.append(carries)

    carry_arr = np.array(carry_matrix, dtype=np.uint8)
    n_coll, n_carries = carry_arr.shape
    print(f"Carry matrix: {n_coll} × {n_carries}", flush=True)

    # Carry entropy
    unique_vectors = len(set(tuple(row) for row in carry_arr.tolist()))
    print(f"Unique carry vectors: {unique_vectors}", flush=True)
    print(f"Carry entropy: {np.log2(max(1,unique_vectors)):.2f} bits", flush=True)

    # Per-carry analysis
    always_0 = (carry_arr.sum(axis=0) == 0).sum()
    always_1 = (carry_arr.sum(axis=0) == n_coll).sum()
    variable = n_carries - always_0 - always_1
    print(f"\nAlways 0: {always_0} ({100*always_0/n_carries:.1f}%)")
    print(f"Always 1: {always_1} ({100*always_1/n_carries:.1f}%)")
    print(f"Variable: {variable} ({100*variable/n_carries:.1f}%)")

    # Automaton width at each bit position
    # Group carries by bit position within the addition
    adds_per_round_per_msg = 7  # h+S1, +Ch, +K, +W, S0+Maj, T1+T2, d+T1
    carries_per_add = N - 1
    total_per_round = adds_per_round_per_msg * carries_per_add * 2  # × 2 messages

    print(f"\n--- Automaton Width Profile (per bit position) ---")
    print(f"Carries per round per message: {adds_per_round_per_msg} adds × {carries_per_add} carries = {adds_per_round_per_msg * carries_per_add}")
    print(f"Total per round (both msgs): {total_per_round}")

    for bit in range(N - 1):
        # Extract carries at this bit position across all additions and rounds
        bit_carries = []
        for add_idx in range(adds_per_round_per_msg * 2 * 7):  # all adds across all rounds
            carry_idx = add_idx * carries_per_add + bit
            if carry_idx < n_carries:
                bit_carries.append(carry_idx)

        if not bit_carries:
            continue

        # Count distinct states at this bit position
        states_at_bit = carry_arr[:, bit_carries]
        unique_states = len(set(tuple(row) for row in states_at_bit.tolist()))
        print(f"  bit {bit}: {unique_states} distinct states (of {n_coll} solutions, {len(bit_carries)} carries)")

    print(f"\n{'='*60}")
    print(f"SUMMARY: N={N}, {n_coll} collisions, {unique_vectors} carry vectors")
    print(f"Carry entropy = {np.log2(max(1,unique_vectors)):.2f} bits")
    print(f"{'='*60}")


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    find_collisions_and_profile(N)
