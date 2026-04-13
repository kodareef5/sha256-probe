#!/usr/bin/env python3
"""
GPU Cascade DP Kernel Sweep v3 — torch.compile for 8-10x speedup

Key: compile the inner batch function (rounds 59-63 + cascade + schedule + check)
into a single fused CUDA kernel, eliminating per-op Python overhead.

Expected N=10: ~50 min per kernel bit (vs 7h uncompiled).
"""
import sys, os, time, math
import torch

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

K32 = [0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,
       0x923f82a4,0xab1c5ed5,0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,
       0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,0xe49b69c1,0xefbe4786,
       0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
       0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,
       0x06ca6351,0x14292967,0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,
       0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,0xa2bfe8a1,0xa81a664b,
       0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
       0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,
       0x5b9cca4f,0x682e6ff3,0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,
       0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2]
IV32 = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
        0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19]


def scale_rot(k32, N):
    r = round(k32 * N / 32)
    return max(1, r)

def ror_n(x, k, N, MASK):
    k = k % N
    return ((x >> k) | (x << (N - k))) & MASK


class Params:
    def __init__(self, N):
        self.N = N
        self.MASK = (1 << N) - 1
        self.rS0 = [scale_rot(2,N), scale_rot(13,N), scale_rot(22,N)]
        self.rS1 = [scale_rot(6,N), scale_rot(11,N), scale_rot(25,N)]
        self.rs1 = [scale_rot(17,N), scale_rot(19,N)]
        self.ss1 = scale_rot(10,N)
        self.rs0 = [scale_rot(7,N), scale_rot(18,N)]
        self.ss0 = scale_rot(3,N)
        self.KN = [k & self.MASK for k in K32]
        self.IVN = [iv & self.MASK for iv in IV32]

    def _ror(self, x, k):
        return ror_n(x, k, self.N, self.MASK)
    def Sigma0(self, a): return self._ror(a, self.rS0[0]) ^ self._ror(a, self.rS0[1]) ^ self._ror(a, self.rS0[2])
    def Sigma1(self, e): return self._ror(e, self.rS1[0]) ^ self._ror(e, self.rS1[1]) ^ self._ror(e, self.rS1[2])
    def sigma0(self, x): return self._ror(x, self.rs0[0]) ^ self._ror(x, self.rs0[1]) ^ ((x >> self.ss0) & self.MASK)
    def sigma1(self, x): return self._ror(x, self.rs1[0]) ^ self._ror(x, self.rs1[1]) ^ ((x >> self.ss1) & self.MASK)
    def Ch(self, e, f, g): return ((e & f) ^ ((~e) & g)) & self.MASK
    def Maj(self, a, b, c): return ((a & b) ^ (a & c) ^ (b & c)) & self.MASK
    def sha_round(self, st, k, w):
        a,b,c,d,e,f,g,h = st
        T1 = (h + self.Sigma1(e) + self.Ch(e,f,g) + k + w) & self.MASK
        T2 = (self.Sigma0(a) + self.Maj(a,b,c)) & self.MASK
        return [(T1+T2)&self.MASK,a,b,c,(d+T1)&self.MASK,e,f,g]
    def cascade_offset(self, s1, s2, rnd):
        r1 = (s1[7]+self.Sigma1(s1[4])+self.Ch(s1[4],s1[5],s1[6])+self.KN[rnd])&self.MASK
        r2 = (s2[7]+self.Sigma1(s2[4])+self.Ch(s2[4],s2[5],s2[6])+self.KN[rnd])&self.MASK
        T21 = (self.Sigma0(s1[0])+self.Maj(s1[0],s1[1],s1[2]))&self.MASK
        T22 = (self.Sigma0(s2[0])+self.Maj(s2[0],s2[1],s2[2]))&self.MASK
        return (r1-r2+T21-T22)&self.MASK
    def precompute(self, M):
        W = list(M[:16])
        for i in range(16,57):
            W.append((self.sigma1(W[i-2])+W[i-7]+self.sigma0(W[i-15])+W[i-16])&self.MASK)
        a,b,c,d = self.IVN[:4]; e,f,g,h = self.IVN[4:]
        for i in range(57):
            T1=(h+self.Sigma1(e)+self.Ch(e,f,g)+self.KN[i]+W[i])&self.MASK
            T2=(self.Sigma0(a)+self.Maj(a,b,c))&self.MASK
            h,g,f,e=g,f,e,(d+T1)&self.MASK; d,c,b,a=c,b,a,(T1+T2)&self.MASK
        return [a,b,c,d,e,f,g,h], W


def make_compiled_batch_fn(p):
    """Create a compiled batch evaluation function for given SHA params."""
    N, MASK = p.N, p.MASK
    rS0_0, rS0_1, rS0_2 = p.rS0
    rS1_0, rS1_1, rS1_2 = p.rS1
    rs1_0, rs1_1, ss1 = p.rs1[0], p.rs1[1], p.ss1

    def g_ror(x, k):
        k = k % N
        return ((x >> k) | (x << (N - k))) & MASK

    def g_S0(a):
        return g_ror(a, rS0_0) ^ g_ror(a, rS0_1) ^ g_ror(a, rS0_2)

    def g_S1(e):
        return g_ror(e, rS1_0) ^ g_ror(e, rS1_1) ^ g_ror(e, rS1_2)

    def g_s1(x):
        return g_ror(x, rs1_0) ^ g_ror(x, rs1_1) ^ ((x >> ss1) & MASK)

    def g_Ch(e, f, g):
        return ((e & f) ^ ((~e) & g)) & MASK

    def g_Maj(a, b, c):
        return ((a & b) ^ (a & c) ^ (b & c)) & MASK

    def g_sha_round(a, b, c, d, e, f, g, h, k, w):
        T1 = (h + g_S1(e) + g_Ch(e, f, g) + k + w) & MASK
        T2 = (g_S0(a) + g_Maj(a, b, c)) & MASK
        return (T1+T2)&MASK, a, b, c, (d+T1)&MASK, e, f, g

    def g_cascade(a1,b1,c1,d1,e1,f1,g1,h1, a2,b2,c2,d2,e2,f2,g2,h2, rnd_k):
        r1 = (h1 + g_S1(e1) + g_Ch(e1,f1,g1) + rnd_k) & MASK
        r2 = (h2 + g_S1(e2) + g_Ch(e2,f2,g2) + rnd_k) & MASK
        T21 = (g_S0(a1) + g_Maj(a1,b1,c1)) & MASK
        T22 = (g_S0(a2) + g_Maj(a2,b2,c2)) & MASK
        return (r1 - r2 + T21 - T22) & MASK

    K59, K60, K61, K62, K63 = p.KN[59], p.KN[60], p.KN[61], p.KN[62], p.KN[63]

    def batch_eval(
        # state58 for all w58 in chunk: 8 tensors, each (C,)
        a1_58, b1_58, c1_58, d1_58, e1_58, f1_58, g1_58, h1_58,
        a2_58, b2_58, c2_58, d2_58, e2_58, f2_58, g2_58, h2_58,
        # pre-computed schedule constants (scalars as tensors)
        s0_W46_1, s0_W47_1, s0_W48_1, W1p_45, W1p_46, W1p_47, W1p_54, W1p_55, W1p_56,
        s0_W46_2, s0_W47_2, s0_W48_2, W2p_45, W2p_46, W2p_47, W2p_54, W2p_55, W2p_56,
        # index tensors
        w59_all, w60_all,  # (SIZE,)
        C,  # chunk size (int)
        SIZE,  # = 1 << N
    ):
        # Cascade for round 59
        cas59 = g_cascade(a1_58,b1_58,c1_58,d1_58,e1_58,f1_58,g1_58,h1_58,
                         a2_58,b2_58,c2_58,d2_58,e2_58,f2_58,g2_58,h2_58, K59)

        # Expand state58 × w59: (C, SIZE) → (C*SIZE,)
        CS = C * SIZE
        a1e = a1_58.unsqueeze(1).expand(C, SIZE).reshape(CS)
        b1e = b1_58.unsqueeze(1).expand(C, SIZE).reshape(CS)
        c1e = c1_58.unsqueeze(1).expand(C, SIZE).reshape(CS)
        d1e = d1_58.unsqueeze(1).expand(C, SIZE).reshape(CS)
        e1e = e1_58.unsqueeze(1).expand(C, SIZE).reshape(CS)
        f1e = f1_58.unsqueeze(1).expand(C, SIZE).reshape(CS)
        g1e = g1_58.unsqueeze(1).expand(C, SIZE).reshape(CS)
        h1e = h1_58.unsqueeze(1).expand(C, SIZE).reshape(CS)
        a2e = a2_58.unsqueeze(1).expand(C, SIZE).reshape(CS)
        b2e = b2_58.unsqueeze(1).expand(C, SIZE).reshape(CS)
        c2e = c2_58.unsqueeze(1).expand(C, SIZE).reshape(CS)
        d2e = d2_58.unsqueeze(1).expand(C, SIZE).reshape(CS)
        e2e = e2_58.unsqueeze(1).expand(C, SIZE).reshape(CS)
        f2e = f2_58.unsqueeze(1).expand(C, SIZE).reshape(CS)
        g2e = g2_58.unsqueeze(1).expand(C, SIZE).reshape(CS)
        h2e = h2_58.unsqueeze(1).expand(C, SIZE).reshape(CS)

        w59_exp = w59_all.unsqueeze(0).expand(C, SIZE).reshape(CS)
        cas59_exp = cas59.unsqueeze(1).expand(C, SIZE).reshape(CS)
        w2_59_exp = (w59_exp + cas59_exp) & MASK

        # Round 59
        a1_59,b1_59,c1_59,d1_59,e1_59,f1_59,g1_59,h1_59 = g_sha_round(
            a1e,b1e,c1e,d1e,e1e,f1e,g1e,h1e, K59, w59_exp)
        a2_59,b2_59,c2_59,d2_59,e2_59,f2_59,g2_59,h2_59 = g_sha_round(
            a2e,b2e,c2e,d2e,e2e,f2e,g2e,h2e, K59, w2_59_exp)

        # Cascade for round 60
        cas60 = g_cascade(a1_59,b1_59,c1_59,d1_59,e1_59,f1_59,g1_59,h1_59,
                         a2_59,b2_59,c2_59,d2_59,e2_59,f2_59,g2_59,h2_59, K60)

        # Expand × w60
        BATCH = CS * SIZE
        a1_59e = a1_59.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)
        b1_59e = b1_59.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)
        c1_59e = c1_59.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)
        d1_59e = d1_59.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)
        e1_59e = e1_59.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)
        f1_59e = f1_59.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)
        g1_59e = g1_59.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)
        h1_59e = h1_59.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)
        a2_59e = a2_59.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)
        b2_59e = b2_59.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)
        c2_59e = c2_59.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)
        d2_59e = d2_59.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)
        e2_59e = e2_59.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)
        f2_59e = f2_59.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)
        g2_59e = g2_59.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)
        h2_59e = h2_59.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)

        w60_exp = w60_all.unsqueeze(0).expand(CS, SIZE).reshape(BATCH)
        cas60_exp = cas60.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)
        w2_60_exp = (w60_exp + cas60_exp) & MASK

        w59_for_sched = w59_exp.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)
        w2_59_for_sched = w2_59_exp.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)

        # Round 60
        a1_60,b1_60,c1_60,d1_60,e1_60,f1_60,g1_60,h1_60 = g_sha_round(
            a1_59e,b1_59e,c1_59e,d1_59e,e1_59e,f1_59e,g1_59e,h1_59e, K60, w60_exp)
        a2_60,b2_60,c2_60,d2_60,e2_60,f2_60,g2_60,h2_60 = g_sha_round(
            a2_59e,b2_59e,c2_59e,d2_59e,e2_59e,f2_59e,g2_59e,h2_59e, K60, w2_60_exp)

        # Schedule
        W1_61 = (g_s1(w59_for_sched) + W1p_54 + s0_W46_1 + W1p_45) & MASK
        W2_61 = (g_s1(w2_59_for_sched) + W2p_54 + s0_W46_2 + W2p_45) & MASK
        W1_62 = (g_s1(w60_exp) + W1p_55 + s0_W47_1 + W1p_46) & MASK
        W2_62 = (g_s1(w2_60_exp) + W2p_55 + s0_W47_2 + W2p_46) & MASK
        W1_63 = (g_s1(W1_61) + W1p_56 + s0_W48_1 + W1p_47) & MASK
        W2_63 = (g_s1(W2_61) + W2p_56 + s0_W48_2 + W2p_47) & MASK

        # Rounds 61-63
        a1,b1,c1,d1,e1,f1,g1,h1 = g_sha_round(a1_60,b1_60,c1_60,d1_60,e1_60,f1_60,g1_60,h1_60,K61,W1_61)
        a2,b2,c2,d2,e2,f2,g2,h2 = g_sha_round(a2_60,b2_60,c2_60,d2_60,e2_60,f2_60,g2_60,h2_60,K61,W2_61)
        a1,b1,c1,d1,e1,f1,g1,h1 = g_sha_round(a1,b1,c1,d1,e1,f1,g1,h1,K62,W1_62)
        a2,b2,c2,d2,e2,f2,g2,h2 = g_sha_round(a2,b2,c2,d2,e2,f2,g2,h2,K62,W2_62)
        a1,b1,c1,d1,e1,f1,g1,h1 = g_sha_round(a1,b1,c1,d1,e1,f1,g1,h1,K63,W1_63)
        a2,b2,c2,d2,e2,f2,g2,h2 = g_sha_round(a2,b2,c2,d2,e2,f2,g2,h2,K63,W2_63)

        # Collision check
        match = (a1==a2) & (b1==b2) & (c1==c2) & (d1==d2) & (e1==e2) & (f1==f2) & (g1==g2) & (h1==h2)
        return match.sum()

    # Try to compile
    try:
        compiled = torch.compile(batch_eval, fullgraph=False)
        print("  torch.compile: enabled")
        return compiled
    except Exception as e:
        print(f"  torch.compile failed: {e}, using uncompiled")
        return batch_eval


def find_candidate(p, kernel_bit):
    delta = 1 << kernel_bit
    fills = [p.MASK, 0, p.MASK >> 1, 1 << (p.N - 1), 0x55 & p.MASK, 0xAA & p.MASK]
    for fill in fills:
        for m0 in range(p.MASK + 1):
            M1 = [m0] + [fill] * 15
            M2 = list(M1); M2[0] ^= delta; M2[9] ^= delta
            s1, W1 = p.precompute(M1)
            s2, W2 = p.precompute(M2)
            if s1[0] == s2[0]:
                return m0, fill, s1, s2, W1, W2
    return None


def find_all_candidates(p, kernel_bit):
    delta = 1 << kernel_bit
    fills = [p.MASK, 0, p.MASK >> 1, 1 << (p.N - 1), 0x55 & p.MASK, 0xAA & p.MASK]
    candidates = []
    for fill in fills:
        for m0 in range(p.MASK + 1):
            M1 = [m0] + [fill] * 15
            M2 = list(M1); M2[0] ^= delta; M2[9] ^= delta
            s1, W1 = p.precompute(M1)
            s2, W2 = p.precompute(M2)
            if s1[0] == s2[0]:
                candidates.append((m0, fill, s1, s2, W1, W2))
    return candidates


def gpu_cascade_dp(p, s1_56, s2_56, W1p, W2p, batch_fn):
    N, MASK, SIZE = p.N, p.MASK, 1 << p.N

    max_batch = 1500 * 1024**2 // 200
    W58_CHUNK = max(1, min(SIZE, max_batch // (SIZE * SIZE)))

    total_coll = 0
    t0 = time.time()

    w59_all = torch.arange(SIZE, dtype=torch.int32, device=device)
    w60_all = torch.arange(SIZE, dtype=torch.int32, device=device)

    # Schedule constants
    sched_consts_1 = [
        torch.tensor(p.sigma0(W1p[46]), dtype=torch.int32, device=device),
        torch.tensor(p.sigma0(W1p[47]), dtype=torch.int32, device=device),
        torch.tensor(p.sigma0(W1p[48]), dtype=torch.int32, device=device),
        torch.tensor(W1p[45], dtype=torch.int32, device=device),
        torch.tensor(W1p[46], dtype=torch.int32, device=device),
        torch.tensor(W1p[47], dtype=torch.int32, device=device),
        torch.tensor(W1p[54], dtype=torch.int32, device=device),
        torch.tensor(W1p[55], dtype=torch.int32, device=device),
        torch.tensor(W1p[56], dtype=torch.int32, device=device),
    ]
    sched_consts_2 = [
        torch.tensor(p.sigma0(W2p[46]), dtype=torch.int32, device=device),
        torch.tensor(p.sigma0(W2p[47]), dtype=torch.int32, device=device),
        torch.tensor(p.sigma0(W2p[48]), dtype=torch.int32, device=device),
        torch.tensor(W2p[45], dtype=torch.int32, device=device),
        torch.tensor(W2p[46], dtype=torch.int32, device=device),
        torch.tensor(W2p[47], dtype=torch.int32, device=device),
        torch.tensor(W2p[54], dtype=torch.int32, device=device),
        torch.tensor(W2p[55], dtype=torch.int32, device=device),
        torch.tensor(W2p[56], dtype=torch.int32, device=device),
    ]

    for w57 in range(SIZE):
        cas57 = p.cascade_offset(s1_56, s2_56, 57)
        w2_57 = (w57 + cas57) & MASK
        st1_57 = p.sha_round(s1_56, p.KN[57], w57)
        st2_57 = p.sha_round(s2_56, p.KN[57], w2_57)

        # Batch all w58 on GPU
        gs1_57 = [torch.full((SIZE,), v, dtype=torch.int32, device=device) for v in st1_57]
        gs2_57 = [torch.full((SIZE,), v, dtype=torch.int32, device=device) for v in st2_57]
        w58_all = torch.arange(SIZE, dtype=torch.int32, device=device)
        cas58 = p.cascade_offset(st1_57, st2_57, 58)
        w2_58_all = (w58_all + cas58) & MASK

        # SHA round 58 on GPU (uncompiled — just for state58 setup)
        def g_ror(x, k):
            k = k % N
            return ((x >> k) | (x << (N - k))) & MASK
        def g_sha_rnd(s, k, w):
            T1 = (s[7] + (g_ror(s[4],p.rS1[0])^g_ror(s[4],p.rS1[1])^g_ror(s[4],p.rS1[2])) +
                  ((s[4]&s[5])^((~s[4])&s[6])&MASK) + k + w) & MASK
            T2 = ((g_ror(s[0],p.rS0[0])^g_ror(s[0],p.rS0[1])^g_ror(s[0],p.rS0[2])) +
                  ((s[0]&s[1])^(s[0]&s[2])^(s[1]&s[2]))&MASK) & MASK
            return [(T1+T2)&MASK, s[0], s[1], s[2], (s[3]+T1)&MASK, s[4], s[5], s[6]]

        gs1_58 = g_sha_rnd(gs1_57, p.KN[58], w58_all)
        gs2_58 = g_sha_rnd(gs2_57, p.KN[58], w2_58_all)

        for w58_start in range(0, SIZE, W58_CHUNK):
            w58_end = min(w58_start + W58_CHUNK, SIZE)
            C = w58_end - w58_start

            chunk_args = (
                *[v[w58_start:w58_end] for v in gs1_58],
                *[v[w58_start:w58_end] for v in gs2_58],
                *sched_consts_1, *sched_consts_2,
                w59_all, w60_all,
                C, SIZE,
            )
            n_hits = batch_fn(*chunk_args)
            if isinstance(n_hits, torch.Tensor):
                n_hits = n_hits.item()
            total_coll += n_hits

        if w57 % max(1, SIZE // 16) == 0 or w57 == SIZE - 1:
            elapsed = time.time() - t0
            pct = 100.0 * (w57 + 1) / SIZE
            eta = elapsed / max(pct, 0.01) * 100 - elapsed
            rate = (w57 + 1) * SIZE * SIZE * SIZE / elapsed if elapsed > 0 else 0
            print(f"  [{pct:5.1f}%] w57={w57:#x} coll={total_coll} "
                  f"{elapsed:.0f}s ETA {eta:.0f}s rate={rate:.2e}/s", flush=True)

    return total_coll, time.time() - t0


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    bits_arg = sys.argv[2] if len(sys.argv) > 2 else None
    all_candidates = '--all' in sys.argv

    if bits_arg and bits_arg != '--all':
        if '-' in bits_arg:
            lo, hi = bits_arg.split('-')
            kernel_bits = list(range(int(lo), int(hi) + 1))
        else:
            kernel_bits = [int(bits_arg)]
    else:
        kernel_bits = list(range(N))

    p = Params(N)
    print(f"GPU Kernel Sweep (compiled) at N={N}")
    print(f"Device: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'})")
    print(f"Kernel bits: {kernel_bits}")
    print(f"All candidates: {all_candidates}")

    batch_fn = make_compiled_batch_fn(p)

    # Warmup torch.compile
    print("Warming up torch.compile...", flush=True)
    cand = find_candidate(p, kernel_bits[0])
    if cand:
        m0, fill, s1, s2, W1, W2 = cand
        # Run a tiny portion to trigger JIT
        w59_t = torch.arange(1 << p.N, dtype=torch.int32, device=device)
        w60_t = torch.arange(1 << p.N, dtype=torch.int32, device=device)
        sched1 = [torch.tensor(x, dtype=torch.int32, device=device) for x in
                  [p.sigma0(W1[46]),p.sigma0(W1[47]),p.sigma0(W1[48]),
                   W1[45],W1[46],W1[47],W1[54],W1[55],W1[56]]]
        sched2 = [torch.tensor(x, dtype=torch.int32, device=device) for x in
                  [p.sigma0(W2[46]),p.sigma0(W2[47]),p.sigma0(W2[48]),
                   W2[45],W2[46],W2[47],W2[54],W2[55],W2[56]]]
        dummy = [torch.zeros(2, dtype=torch.int32, device=device) for _ in range(16)]
        try:
            batch_fn(*dummy, *sched1, *sched2, w59_t[:2], w60_t[:2], 2, 2)
        except:
            pass
    print("Warmup done.", flush=True)

    results = []
    for bit in kernel_bits:
        print(f"\n{'='*60}")
        print(f"Kernel bit {bit} (delta = 2^{bit} = {1<<bit:#x})")

        if all_candidates:
            candidates = find_all_candidates(p, bit)
        else:
            cand = find_candidate(p, bit)
            candidates = [cand] if cand else []

        if not candidates:
            print("  No candidate found")
            results.append((bit, None, None, None, 0))
            continue

        best_coll, best_m0, best_fill, best_time = 0, 0, 0, 0
        for ci, (m0, fill, s1, s2, W1, W2) in enumerate(candidates):
            print(f"  Candidate {ci+1}/{len(candidates)}: M[0]={m0:#x}, fill={fill:#x}")
            torch.cuda.empty_cache()
            coll, elapsed = gpu_cascade_dp(p, s1, s2, W1, W2, batch_fn)
            log2c = math.log2(coll) if coll > 0 else 0
            print(f"  → {coll} collisions (log2={log2c:.2f}) in {elapsed:.1f}s")
            if coll > best_coll:
                best_coll, best_m0, best_fill, best_time = coll, m0, fill, elapsed

        results.append((bit, best_m0, best_fill, best_coll, best_time))

    # Summary
    print(f"\n{'='*60}")
    print(f"KERNEL SWEEP — N={N}")
    print(f"{'='*60}")
    print(f"| Bit | M[0] | Fill | Collisions | log2 | Time |")
    print(f"|-----|------|------|-----------|------|------|")
    best_c, best_b = 0, -1
    for bit, m0, fill, coll, elapsed in results:
        if coll is None:
            print(f"| {bit} | — | — | no candidate | — | — |")
        else:
            log2c = math.log2(coll) if coll > 0 else 0
            print(f"| {bit} | {m0:#x} | {fill:#x} | {coll} | {log2c:.2f} | {elapsed:.0f}s |")
            if coll > best_c: best_c, best_b = coll, bit

    if best_b >= 0:
        print(f"\nBest: bit {best_b} ({best_c} collisions)")

    # Save
    ts = time.strftime('%Y%m%d_%H%M')
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f'{ts}_gpu_kernel_sweep_n{N}.md')
    with open(outpath, 'w') as f:
        f.write(f"# GPU Kernel Sweep (compiled) — N={N}\n\n")
        f.write(f"| Bit | M[0] | Fill | Collisions | log2 | Time |\n")
        f.write(f"|-----|------|------|-----------|------|------|\n")
        for bit, m0, fill, coll, elapsed in results:
            if coll is None:
                f.write(f"| {bit} | — | — | no candidate | — | — |\n")
            else:
                log2c = math.log2(coll) if coll > 0 else 0
                f.write(f"| {bit} | {m0:#x} | {fill:#x} | {coll} | {log2c:.2f} | {elapsed:.0f}s |\n")
        if best_b >= 0:
            f.write(f"\nBest: bit {best_b} ({best_c} collisions)\n")
    print(f"\nSaved: {outpath}")


if __name__ == '__main__':
    main()
