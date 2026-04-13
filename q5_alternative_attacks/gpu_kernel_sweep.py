#!/usr/bin/env python3
"""
GPU Cascade DP Kernel Sweep — RTX 4070 kernel-bit sweep at N=10+

Batches (w59, w60) on GPU (up to 1M parallel) while CPU loops (w57, w58).
Tests all kernel bit positions to find optimal collision kernel per N.

Directly answers macbook's request for N=10 sweep data points.
"""
import sys, os, time, math
import torch
import numpy as np

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')


def scale_rot(k32, N):
    r = round(k32 * N / 32)
    return max(1, r)


def ror_n(x, k, N, MASK):
    k = k % N
    return ((x >> k) | (x << (N - k))) & MASK


def setup_sha(N):
    """Set up SHA primitives for given N."""
    MASK = (1 << N) - 1

    rS0 = [scale_rot(2, N), scale_rot(13, N), scale_rot(22, N)]
    rS1 = [scale_rot(6, N), scale_rot(11, N), scale_rot(25, N)]
    rs0 = [scale_rot(7, N), scale_rot(18, N)]
    ss0 = scale_rot(3, N)
    rs1 = [scale_rot(17, N), scale_rot(19, N)]
    ss1 = scale_rot(10, N)

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
    KN = [k & MASK for k in K32]
    IVN = [iv & MASK for iv in IV32]

    def Sigma0(a):
        return ror_n(a, rS0[0], N, MASK) ^ ror_n(a, rS0[1], N, MASK) ^ ror_n(a, rS0[2], N, MASK)
    def Sigma1(e):
        return ror_n(e, rS1[0], N, MASK) ^ ror_n(e, rS1[1], N, MASK) ^ ror_n(e, rS1[2], N, MASK)
    def sigma0(x):
        return ror_n(x, rs0[0], N, MASK) ^ ror_n(x, rs0[1], N, MASK) ^ ((x >> ss0) & MASK)
    def sigma1(x):
        return ror_n(x, rs1[0], N, MASK) ^ ror_n(x, rs1[1], N, MASK) ^ ((x >> ss1) & MASK)
    def Ch(e, f, g):
        return ((e & f) ^ ((~e) & g)) & MASK
    def Maj(a, b, c):
        return ((a & b) ^ (a & c) ^ (b & c)) & MASK

    return {
        'MASK': MASK, 'N': N, 'KN': KN, 'IVN': IVN,
        'Sigma0': Sigma0, 'Sigma1': Sigma1,
        'sigma0': sigma0, 'sigma1': sigma1,
        'Ch': Ch, 'Maj': Maj,
        'rS0': rS0, 'rS1': rS1, 'rs0': rs0, 'rs1': rs1,
        'ss0': ss0, 'ss1': ss1,
    }


def precompute(sha, M):
    N, MASK = sha['N'], sha['MASK']
    W = list(M[:16])
    for i in range(16, 57):
        W.append((sha['sigma1'](W[i-2]) + W[i-7] + sha['sigma0'](W[i-15]) + W[i-16]) & MASK)
    a, b, c, d = sha['IVN'][:4]
    e, f, g, h = sha['IVN'][4:]
    for i in range(57):
        T1 = (h + sha['Sigma1'](e) + sha['Ch'](e, f, g) + sha['KN'][i] + W[i]) & MASK
        T2 = (sha['Sigma0'](a) + sha['Maj'](a, b, c)) & MASK
        h, g, f, e = g, f, e, (d + T1) & MASK
        d, c, b, a = c, b, a, (T1 + T2) & MASK
    return [a, b, c, d, e, f, g, h], W


def sha_round_scalar(sha, st, k, w):
    MASK = sha['MASK']
    a, b, c, d, e, f, g, h = st
    T1 = (h + sha['Sigma1'](e) + sha['Ch'](e, f, g) + k + w) & MASK
    T2 = (sha['Sigma0'](a) + sha['Maj'](a, b, c)) & MASK
    return [(T1 + T2) & MASK, a, b, c, (d + T1) & MASK, e, f, g]


def cascade_offset(sha, s1, s2, rnd, w1k=0):
    MASK = sha['MASK']
    r1 = (s1[7] + sha['Sigma1'](s1[4]) + sha['Ch'](s1[4], s1[5], s1[6]) + sha['KN'][rnd]) & MASK
    r2 = (s2[7] + sha['Sigma1'](s2[4]) + sha['Ch'](s2[4], s2[5], s2[6]) + sha['KN'][rnd]) & MASK
    T21 = (sha['Sigma0'](s1[0]) + sha['Maj'](s1[0], s1[1], s1[2])) & MASK
    T22 = (sha['Sigma0'](s2[0]) + sha['Maj'](s2[0], s2[1], s2[2])) & MASK
    return (w1k + r1 - r2 + T21 - T22) & MASK


# ---- GPU-accelerated batch SHA operations ---- #

def gpu_ror(x, k, N, MASK):
    k = k % N
    return ((x >> k) | (x << (N - k))) & MASK


def gpu_Sigma0(a, rS0, N, MASK):
    return gpu_ror(a, rS0[0], N, MASK) ^ gpu_ror(a, rS0[1], N, MASK) ^ gpu_ror(a, rS0[2], N, MASK)


def gpu_Sigma1(e, rS1, N, MASK):
    return gpu_ror(e, rS1[0], N, MASK) ^ gpu_ror(e, rS1[1], N, MASK) ^ gpu_ror(e, rS1[2], N, MASK)


def gpu_sigma1(x, rs1, ss1, N, MASK):
    return gpu_ror(x, rs1[0], N, MASK) ^ gpu_ror(x, rs1[1], N, MASK) ^ ((x >> ss1) & MASK)


def gpu_Ch(e, f, g, MASK):
    return ((e & f) ^ ((~e) & g)) & MASK


def gpu_Maj(a, b, c, MASK):
    return ((a & b) ^ (a & c) ^ (b & c)) & MASK


def gpu_sha_round(s, k, w, sha_params):
    """Batch SHA round on GPU. s = list of 8 tensors, k/w are tensors."""
    N, MASK = sha_params['N'], sha_params['MASK']
    rS0, rS1 = sha_params['rS0'], sha_params['rS1']
    T1 = (s[7] + gpu_Sigma1(s[4], rS1, N, MASK) +
          gpu_Ch(s[4], s[5], s[6], MASK) + k + w) & MASK
    T2 = (gpu_Sigma0(s[0], rS0, N, MASK) +
          gpu_Maj(s[0], s[1], s[2], MASK)) & MASK
    return [(T1 + T2) & MASK, s[0], s[1], s[2],
            (s[3] + T1) & MASK, s[4], s[5], s[6]]


def find_candidate(sha, kernel_bit):
    """Find M[0] with da56=0 for given kernel bit."""
    N, MASK = sha['N'], sha['MASK']
    delta = 1 << kernel_bit
    fills = [MASK, 0, MASK >> 1, 1 << (N - 1), 0x55 & MASK, 0xAA & MASK]

    for fill in fills:
        for m0 in range(MASK + 1):
            M1 = [m0] + [fill] * 15
            M2 = list(M1)
            M2[0] = m0 ^ delta
            M2[9] = fill ^ delta
            s1, W1 = precompute(sha, M1)
            s2, W2 = precompute(sha, M2)
            if s1[0] == s2[0]:
                return m0, fill, s1, s2, W1, W2
    return None


def gpu_cascade_dp(sha, s1_56, s2_56, W1p, W2p, sha_params):
    """
    GPU cascade DP: batch (w59, w60) on GPU, loop (w57, w58) on CPU.
    Returns collision count.
    """
    N = sha['N']
    MASK = sha['MASK']
    SIZE = 1 << N
    total_coll = 0
    t0 = time.time()
    tested = 0

    # Pre-create w59/w60 tensors on GPU
    w59_all = torch.arange(SIZE, dtype=torch.int64, device=device)  # (SIZE,)
    w60_all = torch.arange(SIZE, dtype=torch.int64, device=device)  # (SIZE,)

    for w57 in range(SIZE):
        st1_57 = list(s1_56)
        st2_57 = list(s2_56)
        w2_57 = cascade_offset(sha, st1_57, st2_57, 57, w57)
        st1_57 = sha_round_scalar(sha, st1_57, sha['KN'][57], w57)
        st2_57 = sha_round_scalar(sha, st2_57, sha['KN'][57], w2_57)

        for w58 in range(SIZE):
            st1_58 = list(st1_57)
            st2_58 = list(st2_57)
            w2_58 = cascade_offset(sha, st1_58, st2_58, 58, w58)
            st1_58 = sha_round_scalar(sha, st1_58, sha['KN'][58], w58)
            st2_58 = sha_round_scalar(sha, st2_58, sha['KN'][58], w2_58)

            # ---- GPU batch: all (w59, w60) combos ----
            # Step 1: Process round 59 for all w59 values
            # Broadcast state58 to (SIZE,)
            gs1_58 = [torch.full((SIZE,), v, dtype=torch.int64, device=device)
                      for v in st1_58]
            gs2_58 = [torch.full((SIZE,), v, dtype=torch.int64, device=device)
                      for v in st2_58]

            # Cascade offset for round 59 (constant for all w59)
            cas59 = cascade_offset(sha, st1_58, st2_58, 59, 0)
            w2_59_all = (w59_all + cas59) & MASK

            # SHA round 59
            gs1_59 = gpu_sha_round(gs1_58,
                                   torch.tensor(sha['KN'][59], dtype=torch.int64, device=device),
                                   w59_all, sha_params)
            gs2_59 = gpu_sha_round(gs2_58,
                                   torch.tensor(sha['KN'][59], dtype=torch.int64, device=device),
                                   w2_59_all, sha_params)

            # Step 2: For each w59, compute cascade offset for round 60
            # cas60 = find_w2(s59, 60, 0) — depends on state59, different per w59
            cas60_r1 = (gs1_59[7] + gpu_Sigma1(gs1_59[4], sha_params['rS1'], N, MASK) +
                        gpu_Ch(gs1_59[4], gs1_59[5], gs1_59[6], MASK) +
                        sha['KN'][60]) & MASK
            cas60_r2 = (gs2_59[7] + gpu_Sigma1(gs2_59[4], sha_params['rS1'], N, MASK) +
                        gpu_Ch(gs2_59[4], gs2_59[5], gs2_59[6], MASK) +
                        sha['KN'][60]) & MASK
            cas60_T21 = (gpu_Sigma0(gs1_59[0], sha_params['rS0'], N, MASK) +
                         gpu_Maj(gs1_59[0], gs1_59[1], gs1_59[2], MASK)) & MASK
            cas60_T22 = (gpu_Sigma0(gs2_59[0], sha_params['rS0'], N, MASK) +
                         gpu_Maj(gs2_59[0], gs2_59[1], gs2_59[2], MASK)) & MASK
            cas60_vec = (cas60_r1 - cas60_r2 + cas60_T21 - cas60_T22) & MASK  # (SIZE,)

            # Step 3: Expand (w59, w60) to (SIZE, SIZE) then flatten to (SIZE*SIZE,)
            # State59 expanded: (SIZE,8) -> (SIZE,1,8) -> (SIZE,SIZE,8) -> (SIZE*SIZE,8)
            BATCH = SIZE * SIZE
            gs1_59_exp = [v.unsqueeze(1).expand(SIZE, SIZE).reshape(BATCH) for v in gs1_59]
            gs2_59_exp = [v.unsqueeze(1).expand(SIZE, SIZE).reshape(BATCH) for v in gs2_59]

            # w60 expanded: (SIZE,) -> (1,SIZE) -> (SIZE,SIZE) -> (SIZE*SIZE,)
            w1_60_exp = w60_all.unsqueeze(0).expand(SIZE, SIZE).reshape(BATCH)
            # Cascade offset: per-w59 offset applied to each w60
            cas60_exp = cas60_vec.unsqueeze(1).expand(SIZE, SIZE).reshape(BATCH)
            w2_60_exp = (w1_60_exp + cas60_exp) & MASK

            # SHA round 60
            k60 = torch.tensor(sha['KN'][60], dtype=torch.int64, device=device)
            gs1_60 = gpu_sha_round(gs1_59_exp, k60, w1_60_exp, sha_params)
            gs2_60 = gpu_sha_round(gs2_59_exp, k60, w2_60_exp, sha_params)

            # Schedule: W[61] = sigma1(W[59]) + W1p[54] + sigma0(W1p[46]) + W1p[45]
            w59_exp = w59_all.unsqueeze(1).expand(SIZE, SIZE).reshape(BATCH)
            w2_59_exp = w2_59_all.unsqueeze(1).expand(SIZE, SIZE).reshape(BATCH)

            W1_61 = (gpu_sigma1(w59_exp, sha_params['rs1'], sha_params['ss1'], N, MASK) +
                     W1p[54] + sha['sigma0'](W1p[46]) + W1p[45]) & MASK
            W2_61 = (gpu_sigma1(w2_59_exp, sha_params['rs1'], sha_params['ss1'], N, MASK) +
                     W2p[54] + sha['sigma0'](W2p[46]) + W2p[45]) & MASK

            # W[62] = sigma1(W[60]) + W1p[55] + sigma0(W1p[47]) + W1p[46]
            W1_62 = (gpu_sigma1(w1_60_exp, sha_params['rs1'], sha_params['ss1'], N, MASK) +
                     W1p[55] + sha['sigma0'](W1p[47]) + W1p[46]) & MASK
            W2_62 = (gpu_sigma1(w2_60_exp, sha_params['rs1'], sha_params['ss1'], N, MASK) +
                     W2p[55] + sha['sigma0'](W2p[47]) + W2p[46]) & MASK

            # W[63] = sigma1(W[61]) + W1p[56] + sigma0(W1p[48]) + W1p[47]
            W1_63 = (gpu_sigma1(W1_61, sha_params['rs1'], sha_params['ss1'], N, MASK) +
                     W1p[56] + sha['sigma0'](W1p[48]) + W1p[47]) & MASK
            W2_63 = (gpu_sigma1(W2_61, sha_params['rs1'], sha_params['ss1'], N, MASK) +
                     W2p[56] + sha['sigma0'](W2p[48]) + W2p[47]) & MASK

            # Rounds 61-63
            k61 = torch.tensor(sha['KN'][61], dtype=torch.int64, device=device)
            k62 = torch.tensor(sha['KN'][62], dtype=torch.int64, device=device)
            k63 = torch.tensor(sha['KN'][63], dtype=torch.int64, device=device)

            gs1_61 = gpu_sha_round(gs1_60, k61, W1_61, sha_params)
            gs2_61 = gpu_sha_round(gs2_60, k61, W2_61, sha_params)
            gs1_62 = gpu_sha_round(gs1_61, k62, W1_62, sha_params)
            gs2_62 = gpu_sha_round(gs2_61, k62, W2_62, sha_params)
            gs1_63 = gpu_sha_round(gs1_62, k63, W1_63, sha_params)
            gs2_63 = gpu_sha_round(gs2_62, k63, W2_63, sha_params)

            # Check collision: all 8 state words must match
            match = torch.ones(BATCH, dtype=torch.bool, device=device)
            for r in range(8):
                match &= (gs1_63[r] == gs2_63[r])

            n_hits = match.sum().item()
            total_coll += n_hits
            tested += BATCH

        # Progress
        if w57 % max(1, SIZE // 32) == 0 or w57 == SIZE - 1:
            elapsed = time.time() - t0
            pct = 100.0 * (w57 + 1) / SIZE
            eta = elapsed / max(pct, 0.01) * 100 - elapsed if pct > 0 else 0
            print(f"  [{pct:5.1f}%] w57={w57:#x} coll={total_coll} "
                  f"{elapsed:.0f}s ETA {eta:.0f}s", flush=True)

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

    sha = setup_sha(N)
    sha_params = {
        'N': N, 'MASK': sha['MASK'],
        'rS0': sha['rS0'], 'rS1': sha['rS1'],
        'rs0': sha['rs0'], 'rs1': sha['rs1'],
        'ss0': sha['ss0'], 'ss1': sha['ss1'],
    }

    print(f"GPU Kernel Sweep at N={N}")
    print(f"Device: {device}")
    print(f"Kernel bits to test: {kernel_bits}")
    print(f"Search space per bit: 2^{4*N} = {1 << (4*N):.2e}")
    print()

    results = []

    for bit in kernel_bits:
        print(f"{'='*60}")
        print(f"Kernel bit {bit} (delta = 2^{bit} = {1 << bit:#x})")

        cand = find_candidate(sha, bit)
        if cand is None:
            print(f"  No candidate found (da56 != 0 for all M[0], 6 fills)")
            results.append((bit, None, None, None, 0))
            continue

        m0, fill, s1, s2, W1, W2 = cand
        print(f"  Candidate: M[0]={m0:#x}, fill={fill:#x}")

        coll, elapsed = gpu_cascade_dp(sha, s1, s2, W1, W2, sha_params)

        log2c = math.log2(coll) if coll > 0 else 0
        print(f"  RESULT: {coll} collisions (log2={log2c:.2f}) in {elapsed:.1f}s")
        results.append((bit, m0, fill, coll, elapsed))
        print()

    # Summary table
    print(f"\n{'='*60}")
    print(f"KERNEL SWEEP RESULTS — N={N}")
    print(f"{'='*60}")
    print(f"| Bit | M[0] | Fill | Collisions | log2 | Time |")
    print(f"|-----|------|------|-----------|------|------|")
    best_coll = 0
    best_bit = -1
    for bit, m0, fill, coll, elapsed in results:
        if coll is None:
            print(f"| {bit} | — | — | no candidate | — | — |")
        else:
            log2c = math.log2(coll) if coll > 0 else 0
            print(f"| {bit} | {m0:#x} | {fill:#x} | {coll} | {log2c:.2f} | {elapsed:.0f}s |")
            if coll > best_coll:
                best_coll = coll
                best_bit = bit

    if best_bit >= 0:
        msb_bit = N - 1
        msb_result = next((r for r in results if r[0] == msb_bit), None)
        msb_coll = msb_result[3] if msb_result and msb_result[3] else 0
        improvement = best_coll / msb_coll if msb_coll > 0 else float('inf')
        print(f"\nBest kernel: bit {best_bit} with {best_coll} collisions")
        print(f"MSB kernel (bit {msb_bit}): {msb_coll} collisions")
        print(f"Improvement: {improvement:.1f}x")

    # Save results
    ts = time.strftime('%Y%m%d_%H%M')
    outdir = os.path.join(os.path.dirname(__file__), 'results')
    os.makedirs(outdir, exist_ok=True)
    outpath = os.path.join(outdir, f'{ts}_gpu_kernel_sweep_n{N}.md')
    with open(outpath, 'w') as f:
        f.write(f"# GPU Kernel Sweep Results — N={N}\n\n")
        f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M UTC')}\n")
        f.write(f"Device: {device}\n\n")
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
    print(f"\nResults saved to {outpath}")


if __name__ == '__main__':
    main()
