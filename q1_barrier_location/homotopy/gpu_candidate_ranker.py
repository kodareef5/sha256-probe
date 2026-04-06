#!/usr/bin/env python3
"""
GPU candidate ranker for precision homotopy.

Scans ALL M[0] values at word width N for da[56]=0 candidates,
then evaluates each candidate's collision proximity by sampling
millions of random free-word assignments on GPU.

Candidates are ranked by min_hw (minimum Hamming weight of the
collision residual over random samples). Lower min_hw = closer
to collision = more likely SAT for Kissat.

This directly accelerates the Q1 homotopy pipeline by identifying
the best candidates BEFORE spending hours on SAT solving.

Output: ranked candidate list, formatted for fast_parallel_solve.py

Usage:
    python3 gpu_candidate_ranker.py N [samples_per_candidate] [top_k]
    # N: word width (default 12)
    # samples_per_candidate: GPU random samples (default 1M)
    # top_k: output top K candidates (default 10)
"""

import sys, os, time, csv
import torch

_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_root, '..', '..'))

K32 = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]
IV32 = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
        0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]


def scale_rot(k32, N):
    return max(1, round(k32 * N / 32))


class MiniSHA:
    def __init__(self, N):
        self.N = N
        self.MASK = (1 << N) - 1
        self.MSB = 1 << (N - 1)
        self.rS0 = [scale_rot(2,N), scale_rot(13,N), scale_rot(22,N)]
        self.rS1 = [scale_rot(6,N), scale_rot(11,N), scale_rot(25,N)]
        self.rs0 = [scale_rot(7,N), scale_rot(18,N)]
        self.ss0 = scale_rot(3,N)
        self.rs1 = [scale_rot(17,N), scale_rot(19,N)]
        self.ss1 = scale_rot(10,N)
        self.K = [k & self.MASK for k in K32]
        self.IV = [v & self.MASK for v in IV32]

    def ror(self, x, k):
        k = k % self.N
        return ((x >> k) | (x << (self.N - k))) & self.MASK

    def Sigma0(self, a):
        return self.ror(a, self.rS0[0]) ^ self.ror(a, self.rS0[1]) ^ self.ror(a, self.rS0[2])
    def Sigma1(self, e):
        return self.ror(e, self.rS1[0]) ^ self.ror(e, self.rS1[1]) ^ self.ror(e, self.rS1[2])
    def sigma0(self, x):
        return self.ror(x, self.rs0[0]) ^ self.ror(x, self.rs0[1]) ^ ((x >> self.ss0) & self.MASK)
    def sigma1(self, x):
        return self.ror(x, self.rs1[0]) ^ self.ror(x, self.rs1[1]) ^ ((x >> self.ss1) & self.MASK)

    def compress57(self, M):
        W = list(M) + [0]*41
        for i in range(16, 57):
            W[i] = (self.sigma1(W[i-2]) + W[i-7] + self.sigma0(W[i-15]) + W[i-16]) & self.MASK
        a,b,c,d,e,f,g,h = self.IV
        for i in range(57):
            T1 = (h + self.Sigma1(e) + ((e&f)^((~e)&g)&self.MASK) + self.K[i] + W[i]) & self.MASK
            T2 = (self.Sigma0(a) + ((a&b)^(a&c)^(b&c))) & self.MASK
            h,g,f,e,d,c,b,a = g,f,e,(d+T1)&self.MASK,c,b,a,(T1+T2)&self.MASK
        return [a,b,c,d,e,f,g,h], W


def popcount32(x):
    x = x - ((x >> 1) & 0x55555555)
    x = (x & 0x33333333) + ((x >> 2) & 0x33333333)
    x = (x + (x >> 4)) & 0x0F0F0F0F
    x = x + (x >> 8)
    x = x + (x >> 16)
    return x & 0x3F


def gpu_ror(x, k, N, mask):
    k = k % N
    return ((x >> k) | (x << (N - k))) & mask


def gpu_evaluate_candidate(state1, state2, W1_pre, W2_pre, sha, device,
                           n_samples=1_000_000, batch_size=1 << 20):
    """
    Evaluate one candidate by sampling n_samples random independent
    free-word assignments on GPU.

    Returns: (min_hw, mean_hw, p10_hw) — minimum, mean, and 10th percentile
    """
    N = sha.N
    MASK = sha.MASK
    mask_t = torch.tensor(MASK, dtype=torch.int32, device=device)

    # Precompute schedule constants
    def t(v): return torch.tensor(v, dtype=torch.int32, device=device)
    w1c = {k: t(W1_pre[k]) for k in [45,46,47,48,54,55,56]}
    w2c = {k: t(W2_pre[k]) for k in [45,46,47,48,54,55,56]}
    w1c['s46'] = t(sha.sigma0(W1_pre[46]))
    w2c['s46'] = t(sha.sigma0(W2_pre[46]))
    w1c['s47'] = t(sha.sigma0(W1_pre[47]))
    w2c['s47'] = t(sha.sigma0(W2_pre[47]))
    w1c['s48'] = t(sha.sigma0(W1_pre[48]))
    w2c['s48'] = t(sha.sigma0(W2_pre[48]))

    K57 = [t(sha.K[57+i]) for i in range(7)]
    s1 = [t(state1[i]) for i in range(8)]
    s2 = [t(state2[i]) for i in range(8)]

    rS0 = sha.rS0; rS1 = sha.rS1; rs1r = sha.rs1; ss1 = sha.ss1

    def do_sigma1(x):
        return gpu_ror(x, rs1r[0], N, mask_t) ^ gpu_ror(x, rs1r[1], N, mask_t) ^ ((x >> ss1) & mask_t)
    def do_Sigma0(a):
        return gpu_ror(a, rS0[0], N, mask_t) ^ gpu_ror(a, rS0[1], N, mask_t) ^ gpu_ror(a, rS0[2], N, mask_t)
    def do_Sigma1(e):
        return gpu_ror(e, rS1[0], N, mask_t) ^ gpu_ror(e, rS1[1], N, mask_t) ^ gpu_ror(e, rS1[2], N, mask_t)
    def do_round(st, Ki, Wi):
        a,b,c,d,e,f,g,h = st
        ch = ((e & f) ^ ((~e) & g)) & mask_t
        T1 = (h + do_Sigma1(e) + ch + Ki + Wi) & mask_t
        maj = ((a & b) ^ (a & c) ^ (b & c)) & mask_t
        T2 = (do_Sigma0(a) + maj) & mask_t
        return [(T1 + T2) & mask_t, a, b, c, (d + T1) & mask_t, e, f, g]

    global_min = 8 * N
    hw_samples = []
    evaluated = 0

    while evaluated < n_samples:
        bs = min(batch_size, n_samples - evaluated)

        # Independent random free words for each message
        w1_57 = torch.randint(0, 1 << N, (bs,), dtype=torch.int32, device=device)
        w1_58 = torch.randint(0, 1 << N, (bs,), dtype=torch.int32, device=device)
        w1_59 = torch.randint(0, 1 << N, (bs,), dtype=torch.int32, device=device)
        w1_60 = torch.randint(0, 1 << N, (bs,), dtype=torch.int32, device=device)
        w2_57 = torch.randint(0, 1 << N, (bs,), dtype=torch.int32, device=device)
        w2_58 = torch.randint(0, 1 << N, (bs,), dtype=torch.int32, device=device)
        w2_59 = torch.randint(0, 1 << N, (bs,), dtype=torch.int32, device=device)
        w2_60 = torch.randint(0, 1 << N, (bs,), dtype=torch.int32, device=device)

        # Schedule
        w1_61 = (do_sigma1(w1_59) + w1c[54] + w1c['s46'] + w1c[45]) & mask_t
        w2_61 = (do_sigma1(w2_59) + w2c[54] + w2c['s46'] + w2c[45]) & mask_t
        w1_62 = (do_sigma1(w1_60) + w1c[55] + w1c['s47'] + w1c[46]) & mask_t
        w2_62 = (do_sigma1(w2_60) + w2c[55] + w2c['s47'] + w2c[46]) & mask_t
        w1_63 = (do_sigma1(w1_61) + w1c[56] + w1c['s48'] + w1c[47]) & mask_t
        w2_63 = (do_sigma1(w2_61) + w2c[56] + w2c['s48'] + w2c[47]) & mask_t

        W1t = [w1_57, w1_58, w1_59, w1_60, w1_61, w1_62, w1_63]
        W2t = [w2_57, w2_58, w2_59, w2_60, w2_61, w2_62, w2_63]

        st1 = [s.expand(bs) for s in s1]
        for i in range(7):
            st1 = do_round(st1, K57[i], W1t[i])
        st2 = [s.expand(bs) for s in s2]
        for i in range(7):
            st2 = do_round(st2, K57[i], W2t[i])

        total_hw = torch.zeros(bs, dtype=torch.int32, device=device)
        for i in range(8):
            total_hw = total_hw + popcount32(st1[i] ^ st2[i])

        batch_min = total_hw.min().item()
        if batch_min < global_min:
            global_min = batch_min

        # Keep stats for percentile computation (subsample to save memory)
        if bs > 10000:
            hw_samples.append(total_hw[::bs//10000].cpu())
        else:
            hw_samples.append(total_hw.cpu())
        evaluated += bs

    all_hw = torch.cat(hw_samples)
    mean_hw = all_hw.float().mean().item()
    sorted_hw = all_hw.sort().values
    p10_hw = sorted_hw[len(sorted_hw)//10].item()  # 10th percentile

    return global_min, mean_hw, p10_hw


def scan_and_rank(N, samples_per=1_000_000, top_k=10):
    sha = MiniSHA(N)
    MASK = sha.MASK
    MSB = sha.MSB
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    fills = [MASK, 0, MASK >> 1, MSB, 0x55 & MASK, 0xAA & MASK,
             0x33 & MASK, 0xCC & MASK, 0x0F & MASK, 0xF0 & MASK]

    print(f"GPU Candidate Ranker: N={N} bits, {samples_per:,} samples/candidate")
    print(f"Device: {device}" + (f" ({torch.cuda.get_device_name(0)})" if device.type == 'cuda' else ""))
    print(f"Scanning M[0] space for da[56]=0 candidates...\n")

    t0 = time.time()
    candidates = []
    max_m0 = min(MASK, (1 << 24) - 1)

    for fill in fills:
        for m0 in range(max_m0 + 1):
            M1 = [m0] + [fill]*15
            M2 = list(M1); M2[0] = m0 ^ MSB; M2[9] = fill ^ MSB
            s1, W1 = sha.compress57(M1)
            s2, W2 = sha.compress57(M2)
            if s1[0] == s2[0]:
                hw56 = sum(bin(s1[i] ^ s2[i]).count('1') for i in range(8))
                candidates.append((m0, fill, s1, s2, W1, W2, hw56))

    scan_time = time.time() - t0
    print(f"Found {len(candidates)} candidates in {scan_time:.1f}s")

    if not candidates:
        print("No candidates found!")
        return []

    # GPU evaluation of each candidate
    print(f"\nRanking {len(candidates)} candidates ({samples_per:,} random samples each)...\n")
    results = []
    t1 = time.time()

    for i, (m0, fill, s1, s2, W1, W2, hw56) in enumerate(candidates):
        min_hw, mean_hw, p10_hw = gpu_evaluate_candidate(
            s1, s2, W1, W2, sha, device,
            n_samples=samples_per, batch_size=min(1 << 20, samples_per))
        results.append({
            'm0': m0, 'fill': fill, 'hw56': hw56,
            'min_hw': min_hw, 'mean_hw': mean_hw, 'p10_hw': p10_hw
        })
        if (i + 1) % 10 == 0 or i == len(candidates) - 1:
            elapsed = time.time() - t1
            print(f"  [{i+1}/{len(candidates)}] {elapsed:.1f}s "
                  f"({(i+1)/elapsed:.1f} cand/s)", flush=True)

    # Sort by min_hw (lower is better)
    results.sort(key=lambda r: (r['min_hw'], r['p10_hw'], r['mean_hw']))

    eval_time = time.time() - t1
    total_time = time.time() - t0

    print(f"\n{'='*80}")
    print(f"TOP-{top_k} CANDIDATES (N={N}, {len(candidates)} total, {eval_time:.1f}s GPU eval)")
    print(f"{'='*80}")
    print(f"{'Rank':>4} {'M[0]':>10} {'Fill':>10} {'hw56':>5} {'min_hw':>7} {'p10_hw':>7} {'mean_hw':>8}")
    print(f"{'-'*4} {'-'*10} {'-'*10} {'-'*5} {'-'*7} {'-'*7} {'-'*8}")

    for i, r in enumerate(results[:top_k]):
        print(f"{i+1:4d} 0x{r['m0']:08x} 0x{r['fill']:08x} {r['hw56']:5d} "
              f"{r['min_hw']:7d} {r['p10_hw']:7d} {r['mean_hw']:8.1f}")

    # Show distribution of min_hw across all candidates
    min_hws = [r['min_hw'] for r in results]
    print(f"\nmin_hw distribution across {len(results)} candidates:")
    for hw in sorted(set(min_hws)):
        count = min_hws.count(hw)
        print(f"  min_hw={hw}: {count} candidates ({100*count/len(results):.1f}%)")

    print(f"\nTotal time: {total_time:.1f}s (scan {scan_time:.1f}s + GPU eval {eval_time:.1f}s)")

    # Output CSV for fast_parallel_solve.py
    csv_file = f"ranked_candidates_N{N}.csv"
    with open(os.path.join(_root, csv_file), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['m0', 'fill', 'hw56', 'min_hw', 'p10_hw', 'mean_hw'])
        w.writeheader()
        for r in results[:top_k]:
            w.writerow(r)
    print(f"Top-{top_k} candidates written to {csv_file}")

    return results


if __name__ == "__main__":
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    samples = int(sys.argv[2]) if len(sys.argv) > 2 else 1_000_000
    top_k = int(sys.argv[3]) if len(sys.argv) > 3 else 10

    scan_and_rank(N, samples, top_k)
