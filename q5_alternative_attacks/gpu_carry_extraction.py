#!/usr/bin/env python3
"""
GPU carry extraction: enumerate N=4 collisions and extract carry patterns.

For each of the 49 collisions found by GPU exhaustive enumeration,
compute the carry chain for every modular addition in the 7-round tail.
Report the carry entropy (should match macbook's 5.6 bits).

This gives us the carry VECTORS, which can be analyzed for structure
(common carries, carry correlations, carry-to-input dependencies).
"""
import sys, os, time, collections
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


def extract_carries(a, b, N):
    """Extract carry bits from a + b (mod 2^N).
    Returns list of N-1 carry bits (carry into positions 1..N-1).
    """
    carries = []
    c = 0
    for bit in range(N):
        ab = ((a >> bit) & 1) + ((b >> bit) & 1) + c
        c = ab >> 1
        if bit < N - 1:
            carries.append(c)
    return carries


def main():
    N = 4
    MASK = (1 << N) - 1
    MSB = 1 << (N - 1)

    # Use homotopy to get candidate
    sys.path.insert(0, '.')
    spec = __import__('50_precision_homotopy')
    sha = spec.MiniSHA256(N)
    m0, s1, s2, W1p, W2p = sha.find_m0()
    K = sha.K

    # Cascade constant
    dh = (s1[7]-s2[7]) & MASK
    dSig1 = (sha.Sigma1(s1[4])-sha.Sigma1(s2[4])) & MASK
    dCh = (sha.ch(s1[4],s1[5],s1[6])-sha.ch(s2[4],s2[5],s2[6])) & MASK
    T2_1 = (sha.Sigma0(s1[0])+sha.maj(s1[0],s1[1],s1[2])) & MASK
    T2_2 = (sha.Sigma0(s2[0])+sha.maj(s2[0],s2[1],s2[2])) & MASK
    C_w57 = (dh+dSig1+dCh+(T2_1-T2_2)) & MASK

    print(f"N={N}, M[0]=0x{m0:x}, C_w57=0x{C_w57:x}", flush=True)

    # Exhaustively find all collisions and extract carries
    carry_vectors = []
    collision_count = 0

    def eval_with_carries(w1, w2):
        """Evaluate collision AND extract carry vectors."""
        W1 = list(w1); W2 = list(w2)
        # Schedule
        W1.append((sha.sigma1(w1[2])+W1p[54]+sha.sigma0(W1p[46])+W1p[45])&MASK)
        W2.append((sha.sigma1(w2[2])+W2p[54]+sha.sigma0(W2p[46])+W2p[45])&MASK)
        W1.append((sha.sigma1(w1[3])+W1p[55]+sha.sigma0(W1p[47])+W1p[46])&MASK)
        W2.append((sha.sigma1(w2[3])+W2p[55]+sha.sigma0(W2p[47])+W2p[46])&MASK)
        W1.append((sha.sigma1(W1[4])+W1p[56]+sha.sigma0(W1p[48])+W1p[47])&MASK)
        W2.append((sha.sigma1(W2[4])+W2p[56]+sha.sigma0(W2p[48])+W2p[47])&MASK)

        carries_all = []
        a1,b1,c1,d1,e1,f1,g1,h1 = s1
        a2,b2,c2,d2,e2,f2,g2,h2 = s2

        for i in range(7):
            # T1 = h + Sigma1(e) + Ch(e,f,g) + K + W
            Sig1_1 = sha.Sigma1(e1); Sig1_2 = sha.Sigma1(e2)
            Ch1 = sha.ch(e1,f1,g1); Ch2 = sha.ch(e2,f2,g2)

            # h + Sig1
            t = (h1 + Sig1_1) & MASK
            carries_all.extend(extract_carries(h1, Sig1_1, N))
            # + Ch
            t2 = (t + Ch1) & MASK
            carries_all.extend(extract_carries(t, Ch1, N))
            # + K
            t3 = (t2 + K[57+i]) & MASK
            carries_all.extend(extract_carries(t2, K[57+i], N))
            # + W
            T1_1 = (t3 + W1[i]) & MASK
            carries_all.extend(extract_carries(t3, W1[i], N))

            # T2 = Sigma0(a) + Maj(a,b,c)
            Sig0_1 = sha.Sigma0(a1)
            Maj1 = sha.maj(a1,b1,c1)
            T2_1 = (Sig0_1 + Maj1) & MASK
            carries_all.extend(extract_carries(Sig0_1, Maj1, N))

            # a = T1 + T2
            new_a1 = (T1_1 + T2_1) & MASK
            carries_all.extend(extract_carries(T1_1, T2_1, N))

            # e = d + T1
            new_e1 = (d1 + T1_1) & MASK
            carries_all.extend(extract_carries(d1, T1_1, N))

            h1,g1,f1,e1,d1,c1,b1,a1 = g1,f1,e1,new_e1,c1,b1,a1,new_a1

            # Same for M2
            t = (h2 + Sig1_2) & MASK
            t2 = (t + Ch2) & MASK
            t3 = (t2 + K[57+i]) & MASK
            T1_2 = (t3 + W2[i]) & MASK
            Sig0_2 = sha.Sigma0(a2); Maj2 = sha.maj(a2,b2,c2)
            T2_2 = (Sig0_2 + Maj2) & MASK
            new_a2 = (T1_2 + T2_2) & MASK; new_e2 = (d2 + T1_2) & MASK
            h2,g2,f2,e2,d2,c2,b2,a2 = g2,f2,e2,new_e2,c2,b2,a2,new_a2

        collision = all(
            [a1==a2, b1==b2, c1==c2, d1==d2, e1==e2, f1==f2, g1==g2, h1==h2])
        return collision, tuple(carries_all)

    print(f"Exhaustive enumeration...", flush=True)
    t0 = time.time()

    for idx in range(1 << (7 * N)):
        w1_57 = idx & MASK
        w1_58 = (idx >> N) & MASK
        w2_58 = (idx >> (2*N)) & MASK
        w1_59 = (idx >> (3*N)) & MASK
        w2_59 = (idx >> (4*N)) & MASK
        w1_60 = (idx >> (5*N)) & MASK
        w2_60 = (idx >> (6*N)) & MASK
        w2_57 = (w1_57 + C_w57) & MASK

        w1 = [w1_57, w1_58, w1_59, w1_60]
        w2 = [w2_57, w2_58, w2_59, w2_60]

        collision, carries = eval_with_carries(w1, w2)
        if collision:
            collision_count += 1
            carry_vectors.append(carries)
            if collision_count <= 5:
                print(f"  #{collision_count}: W1=[{','.join(hex(x) for x in w1)}] "
                      f"carries={len(carries)} bits", flush=True)

    elapsed = time.time() - t0
    print(f"\nFound {collision_count} collisions in {elapsed:.0f}s", flush=True)
    print(f"Each has {len(carry_vectors[0])} carry bits", flush=True)

    # Compute carry entropy
    carry_array = np.array(carry_vectors, dtype=np.uint8)
    n_coll, n_carries = carry_array.shape
    print(f"\nCarry matrix: {n_coll} × {n_carries}", flush=True)

    # Per-carry analysis
    always_0 = (carry_array.sum(axis=0) == 0).sum()
    always_1 = (carry_array.sum(axis=0) == n_coll).sum()
    variable = n_carries - always_0 - always_1
    print(f"Always 0: {always_0}")
    print(f"Always 1: {always_1}")
    print(f"Variable: {variable}")

    # Unique carry vectors
    unique = len(set(tuple(row) for row in carry_array.tolist()))
    print(f"\nUnique carry vectors: {unique}")
    print(f"Carry entropy: {np.log2(unique):.2f} bits")
    print(f"Expected from theorem: 5.6 bits")

    # Per-round analysis
    carries_per_round = 7 * (N - 1)  # 7 additions × (N-1) carries each
    # Actually 7 additions per round × 2 messages × (N-1) carries
    # But my extraction does M1 then M2 per round
    additions_per_round = 7  # h+Sig1, +Ch, +K, +W, Sig0+Maj, T1+T2, d+T1
    carries_per_addition = N - 1
    total_per_round_m1 = additions_per_round * carries_per_addition
    print(f"\nPer-round M1 carries: {total_per_round_m1}")
    print(f"Total carries extracted: {n_carries}")


if __name__ == "__main__":
    main()
