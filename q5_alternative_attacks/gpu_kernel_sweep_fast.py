#!/usr/bin/env python3
"""
GPU Cascade DP Kernel Sweep v2 — Optimized for N=10+

Key optimization: batch w58 dimension on GPU too, so inner batch is
W58_CHUNK × SIZE × SIZE elements (up to 16M). This reduces Python→GPU
round trips from SIZE^2 to SIZE × SIZE/CHUNK = ~65K at N=10.

Expected N=10 timing: ~5-10 min per kernel bit.
"""
import sys, os, time, math
import torch

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def scale_rot(k32, N):
    r = round(k32 * N / 32)
    return max(1, r)


def ror_n(x, k, N, MASK):
    k = k % N
    return ((x >> k) | (x << (N - k))) & MASK


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


class MiniSHAParams:
    """SHA parameters for given N, pre-computed on init."""
    def __init__(self, N):
        self.N = N
        self.MASK = (1 << N) - 1
        self.rS0 = [scale_rot(2, N), scale_rot(13, N), scale_rot(22, N)]
        self.rS1 = [scale_rot(6, N), scale_rot(11, N), scale_rot(25, N)]
        self.rs0 = [scale_rot(7, N), scale_rot(18, N)]
        self.ss0 = scale_rot(3, N)
        self.rs1 = [scale_rot(17, N), scale_rot(19, N)]
        self.ss1 = scale_rot(10, N)
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

    def precompute(self, M):
        W = list(M[:16])
        for i in range(16, 57):
            W.append((self.sigma1(W[i-2]) + W[i-7] + self.sigma0(W[i-15]) + W[i-16]) & self.MASK)
        a, b, c, d = self.IVN[:4]
        e, f, g, h = self.IVN[4:]
        for i in range(57):
            T1 = (h + self.Sigma1(e) + self.Ch(e, f, g) + self.KN[i] + W[i]) & self.MASK
            T2 = (self.Sigma0(a) + self.Maj(a, b, c)) & self.MASK
            h, g, f, e = g, f, e, (d + T1) & self.MASK
            d, c, b, a = c, b, a, (T1 + T2) & self.MASK
        return [a, b, c, d, e, f, g, h], W

    def sha_round(self, st, k, w):
        a, b, c, d, e, f, g, h = st
        T1 = (h + self.Sigma1(e) + self.Ch(e, f, g) + k + w) & self.MASK
        T2 = (self.Sigma0(a) + self.Maj(a, b, c)) & self.MASK
        return [(T1 + T2) & self.MASK, a, b, c, (d + T1) & self.MASK, e, f, g]

    def cascade_offset(self, s1, s2, rnd):
        r1 = (s1[7] + self.Sigma1(s1[4]) + self.Ch(s1[4], s1[5], s1[6]) + self.KN[rnd]) & self.MASK
        r2 = (s2[7] + self.Sigma1(s2[4]) + self.Ch(s2[4], s2[5], s2[6]) + self.KN[rnd]) & self.MASK
        T21 = (self.Sigma0(s1[0]) + self.Maj(s1[0], s1[1], s1[2])) & self.MASK
        T22 = (self.Sigma0(s2[0]) + self.Maj(s2[0], s2[1], s2[2])) & self.MASK
        return (r1 - r2 + T21 - T22) & self.MASK


# ---- GPU batch operations ---- #

def g_ror(x, k, N, MASK):
    k = k % N
    return ((x >> k) | (x << (N - k))) & MASK

def g_S0(a, p):
    return g_ror(a, p.rS0[0], p.N, p.MASK) ^ g_ror(a, p.rS0[1], p.N, p.MASK) ^ g_ror(a, p.rS0[2], p.N, p.MASK)

def g_S1(e, p):
    return g_ror(e, p.rS1[0], p.N, p.MASK) ^ g_ror(e, p.rS1[1], p.N, p.MASK) ^ g_ror(e, p.rS1[2], p.N, p.MASK)

def g_s1(x, p):
    return g_ror(x, p.rs1[0], p.N, p.MASK) ^ g_ror(x, p.rs1[1], p.N, p.MASK) ^ ((x >> p.ss1) & p.MASK)

def g_Ch(e, f, g, MASK):
    return ((e & f) ^ ((~e) & g)) & MASK

def g_Maj(a, b, c, MASK):
    return ((a & b) ^ (a & c) ^ (b & c)) & MASK

def g_sha_round(s, k, w, p):
    """s = [a,b,c,d,e,f,g,h] tensors, k/w = tensors or scalars."""
    T1 = (s[7] + g_S1(s[4], p) + g_Ch(s[4], s[5], s[6], p.MASK) + k + w) & p.MASK
    T2 = (g_S0(s[0], p) + g_Maj(s[0], s[1], s[2], p.MASK)) & p.MASK
    return [(T1 + T2) & p.MASK, s[0], s[1], s[2],
            (s[3] + T1) & p.MASK, s[4], s[5], s[6]]

def g_cascade(s1, s2, rnd_k, p):
    """Vectorized cascade offset computation."""
    r1 = (s1[7] + g_S1(s1[4], p) + g_Ch(s1[4], s1[5], s1[6], p.MASK) + rnd_k) & p.MASK
    r2 = (s2[7] + g_S1(s2[4], p) + g_Ch(s2[4], s2[5], s2[6], p.MASK) + rnd_k) & p.MASK
    T21 = (g_S0(s1[0], p) + g_Maj(s1[0], s1[1], s1[2], p.MASK)) & p.MASK
    T22 = (g_S0(s2[0], p) + g_Maj(s2[0], s2[1], s2[2], p.MASK)) & p.MASK
    return (r1 - r2 + T21 - T22) & p.MASK


def find_candidate(p, kernel_bit):
    delta = 1 << kernel_bit
    fills = [p.MASK, 0, p.MASK >> 1, 1 << (p.N - 1), 0x55 & p.MASK, 0xAA & p.MASK]
    for fill in fills:
        for m0 in range(p.MASK + 1):
            M1 = [m0] + [fill] * 15
            M2 = list(M1)
            M2[0] = m0 ^ delta
            M2[9] = fill ^ delta
            s1, W1 = p.precompute(M1)
            s2, W2 = p.precompute(M2)
            if s1[0] == s2[0]:
                return m0, fill, s1, s2, W1, W2
    return None


def gpu_cascade_dp_fast(p, s1_56, s2_56, W1p, W2p):
    """Optimized GPU cascade DP: batch (w58, w59, w60) on GPU."""
    N, MASK, SIZE = p.N, p.MASK, 1 << p.N

    # Memory: ~200 bytes per element (50 live int32 tensors × 4 bytes)
    # Target ~1.5GB working set to stay safe on 8GB GPU
    max_batch = 1500 * 1024**2 // 200  # ~7.5M elements
    W58_CHUNK = max(1, min(SIZE, max_batch // (SIZE * SIZE)))
    BATCH_PER_CHUNK = W58_CHUNK * SIZE * SIZE

    print(f"  W58_CHUNK={W58_CHUNK}, batch/chunk={BATCH_PER_CHUNK//1000}K, "
          f"chunks/w57={math.ceil(SIZE/W58_CHUNK)}")

    total_coll = 0
    t0 = time.time()

    # Pre-create index tensors
    w59_all = torch.arange(SIZE, dtype=torch.int32, device=device)
    w60_all = torch.arange(SIZE, dtype=torch.int32, device=device)

    # Schedule constants (pre-computed, used in rounds 61-63)
    s0_W46 = p.sigma0(W1p[46])
    s0_W47 = p.sigma0(W1p[47])
    s0_W48 = p.sigma0(W1p[48])
    s0_W46_2 = p.sigma0(W2p[46])
    s0_W47_2 = p.sigma0(W2p[47])
    s0_W48_2 = p.sigma0(W2p[48])

    for w57 in range(SIZE):
        # Round 57 on CPU (scalar)
        cas57 = p.cascade_offset(s1_56, s2_56, 57)
        w2_57 = (w57 + cas57) & MASK
        st1_57 = p.sha_round(s1_56, p.KN[57], w57)
        st2_57 = p.sha_round(s2_56, p.KN[57], w2_57)

        # Round 58: batch all w58 on GPU
        # State57 broadcast to (SIZE,)
        gs1_57 = [torch.full((SIZE,), v, dtype=torch.int32, device=device) for v in st1_57]
        gs2_57 = [torch.full((SIZE,), v, dtype=torch.int32, device=device) for v in st2_57]
        w58_all = torch.arange(SIZE, dtype=torch.int32, device=device)

        cas58 = p.cascade_offset(st1_57, st2_57, 58)  # scalar
        w2_58_all = (w58_all + cas58) & MASK

        gs1_58 = g_sha_round(gs1_57, p.KN[58], w58_all, p)
        gs2_58 = g_sha_round(gs2_57, p.KN[58], w2_58_all, p)
        # gs1_58[i] has shape (SIZE,) — state58 for each w58 value

        # Process w58 in chunks
        for w58_start in range(0, SIZE, W58_CHUNK):
            w58_end = min(w58_start + W58_CHUNK, SIZE)
            C = w58_end - w58_start  # actual chunk size

            # Slice state58 for this chunk: (C, 8)
            cs1_58 = [v[w58_start:w58_end] for v in gs1_58]  # each (C,)
            cs2_58 = [v[w58_start:w58_end] for v in gs2_58]

            # Cascade offset for round 59: (C,) — depends on state58
            cas59 = g_cascade(cs1_58, cs2_58, p.KN[59], p)  # (C,)

            # Expand state58 × w59: (C, SIZE) → (C*SIZE,)
            CS = C * SIZE
            es1_58 = [v.unsqueeze(1).expand(C, SIZE).reshape(CS) for v in cs1_58]
            es2_58 = [v.unsqueeze(1).expand(C, SIZE).reshape(CS) for v in cs2_58]
            w59_exp = w59_all.unsqueeze(0).expand(C, SIZE).reshape(CS)
            cas59_exp = cas59.unsqueeze(1).expand(C, SIZE).reshape(CS)
            w2_59_exp = (w59_exp + cas59_exp) & MASK

            # SHA round 59: (CS,)
            gs1_59 = g_sha_round(es1_58, p.KN[59], w59_exp, p)
            gs2_59 = g_sha_round(es2_58, p.KN[59], w2_59_exp, p)

            # Cascade offset for round 60: (CS,) — depends on state59
            cas60 = g_cascade(gs1_59, gs2_59, p.KN[60], p)  # (CS,)

            # Expand state59 × w60: (CS, SIZE) → (CS*SIZE,)
            BATCH = CS * SIZE
            es1_59 = [v.unsqueeze(1).expand(CS, SIZE).reshape(BATCH) for v in gs1_59]
            es2_59 = [v.unsqueeze(1).expand(CS, SIZE).reshape(BATCH) for v in gs2_59]
            w60_exp = w60_all.unsqueeze(0).expand(CS, SIZE).reshape(BATCH)
            cas60_exp = cas60.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)
            w2_60_exp = (w60_exp + cas60_exp) & MASK

            # Also expand w59 and w2_59 for schedule computation
            w59_for_sched = w59_exp.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)
            w2_59_for_sched = w2_59_exp.unsqueeze(1).expand(CS, SIZE).reshape(BATCH)

            # SHA round 60
            gs1_60 = g_sha_round(es1_59, p.KN[60], w60_exp, p)
            gs2_60 = g_sha_round(es2_59, p.KN[60], w2_60_exp, p)

            # Schedule: W[61] = sigma1(W[59]) + W1p[54] + sigma0(W1p[46]) + W1p[45]
            W1_61 = (g_s1(w59_for_sched, p) + W1p[54] + s0_W46 + W1p[45]) & MASK
            W2_61 = (g_s1(w2_59_for_sched, p) + W2p[54] + s0_W46_2 + W2p[45]) & MASK

            # W[62] = sigma1(W[60]) + W1p[55] + sigma0(W1p[47]) + W1p[46]
            W1_62 = (g_s1(w60_exp, p) + W1p[55] + s0_W47 + W1p[46]) & MASK
            W2_62 = (g_s1(w2_60_exp, p) + W2p[55] + s0_W47_2 + W2p[46]) & MASK

            # W[63] = sigma1(W[61]) + W1p[56] + sigma0(W1p[48]) + W1p[47]
            W1_63 = (g_s1(W1_61, p) + W1p[56] + s0_W48 + W1p[47]) & MASK
            W2_63 = (g_s1(W2_61, p) + W2p[56] + s0_W48_2 + W2p[47]) & MASK

            # Rounds 61-63
            gs1_61 = g_sha_round(gs1_60, p.KN[61], W1_61, p)
            gs2_61 = g_sha_round(gs2_60, p.KN[61], W2_61, p)
            gs1_62 = g_sha_round(gs1_61, p.KN[62], W1_62, p)
            gs2_62 = g_sha_round(gs2_61, p.KN[62], W2_62, p)
            gs1_63 = g_sha_round(gs1_62, p.KN[63], W1_63, p)
            gs2_63 = g_sha_round(gs2_62, p.KN[63], W2_63, p)

            # Check collision
            match = torch.ones(BATCH, dtype=torch.bool, device=device)
            for r in range(8):
                match &= (gs1_63[r] == gs2_63[r])
            total_coll += match.sum().item()

        # Progress
        if w57 % max(1, SIZE // 16) == 0 or w57 == SIZE - 1:
            elapsed = time.time() - t0
            pct = 100.0 * (w57 + 1) / SIZE
            eta = elapsed / max(pct, 0.01) * 100 - elapsed if pct > 0 else 0
            rate = (w57 + 1) * SIZE * SIZE * SIZE / elapsed if elapsed > 0 else 0
            print(f"  [{pct:5.1f}%] w57={w57:#x} coll={total_coll} "
                  f"{elapsed:.0f}s ETA {eta:.0f}s rate={rate:.2e}/s", flush=True)

    elapsed = time.time() - t0
    return total_coll, elapsed


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    bits_arg = sys.argv[2] if len(sys.argv) > 2 else None

    if bits_arg:
        if '-' in bits_arg:
            lo, hi = bits_arg.split('-')
            kernel_bits = list(range(int(lo), int(hi) + 1))
        else:
            kernel_bits = [int(bits_arg)]
    else:
        kernel_bits = list(range(N))

    p = MiniSHAParams(N)

    print(f"GPU Kernel Sweep (fast) at N={N}")
    print(f"Device: {device}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        mem = torch.cuda.get_device_properties(0).total_memory
        print(f"VRAM: {mem/1e9:.1f} GB")
    print(f"Kernel bits: {kernel_bits}")
    print(f"Search space per bit: 2^{4*N} = {1 << (4*N):.2e}")
    print()

    results = []

    for bit in kernel_bits:
        print(f"{'='*60}")
        print(f"Kernel bit {bit} (delta = 2^{bit} = {1 << bit:#x})")

        cand = find_candidate(p, bit)
        if cand is None:
            print(f"  No candidate found")
            results.append((bit, None, None, None, 0))
            continue

        m0, fill, s1, s2, W1, W2 = cand
        print(f"  Candidate: M[0]={m0:#x}, fill={fill:#x}")

        torch.cuda.empty_cache()
        coll, elapsed = gpu_cascade_dp_fast(p, s1, s2, W1, W2)

        log2c = math.log2(coll) if coll > 0 else 0
        print(f"  RESULT: {coll} collisions (log2={log2c:.2f}) in {elapsed:.1f}s")
        results.append((bit, m0, fill, coll, elapsed))
        print()

    # Summary
    print(f"\n{'='*60}")
    print(f"KERNEL SWEEP RESULTS — N={N}")
    print(f"{'='*60}")
    print(f"| Bit | M[0] | Fill | Collisions | log2 | Time |")
    print(f"|-----|------|------|-----------|------|------|")
    best_coll, best_bit = 0, -1
    for bit, m0, fill, coll, elapsed in results:
        if coll is None:
            print(f"| {bit} | — | — | no candidate | — | — |")
        else:
            log2c = math.log2(coll) if coll > 0 else 0
            print(f"| {bit} | {m0:#x} | {fill:#x} | {coll} | {log2c:.2f} | {elapsed:.0f}s |")
            if coll is not None and coll > best_coll:
                best_coll, best_bit = coll, bit

    if best_bit >= 0:
        msb_bit = N - 1
        msb_r = next((r for r in results if r[0] == msb_bit), None)
        msb_c = msb_r[3] if msb_r and msb_r[3] else 0
        imp = best_coll / msb_c if msb_c > 0 else float('inf')
        print(f"\nBest: bit {best_bit} ({best_coll} coll)")
        if msb_c > 0:
            print(f"MSB (bit {msb_bit}): {msb_c} coll, improvement: {imp:.1f}x")

    # Save
    ts = time.strftime('%Y%m%d_%H%M')
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f'{ts}_gpu_kernel_sweep_n{N}.md')
    with open(outpath, 'w') as f:
        f.write(f"# GPU Kernel Sweep — N={N}\n\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M UTC')}\n")
        f.write(f"Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'cpu'}\n\n")
        f.write(f"| Bit | M[0] | Fill | Collisions | log2 | Time |\n")
        f.write(f"|-----|------|------|-----------|------|------|\n")
        for bit, m0, fill, coll, elapsed in results:
            if coll is None:
                f.write(f"| {bit} | — | — | no candidate | — | — |\n")
            else:
                log2c = math.log2(coll) if coll > 0 else 0
                f.write(f"| {bit} | {m0:#x} | {fill:#x} | {coll} | {log2c:.2f} | {elapsed:.0f}s |\n")
        if best_bit >= 0:
            f.write(f"\nBest: bit {best_bit} ({best_coll} collisions)\n")
    print(f"\nSaved: {outpath}")


if __name__ == '__main__':
    main()
