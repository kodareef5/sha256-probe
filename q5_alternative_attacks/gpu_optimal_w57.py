#!/usr/bin/env python3
"""
GPU-exhaustive optimal W57 search for sr=60 sequential modification.

Given a candidate (M[0], fill) with da[56]=0, exhaustively searches
ALL 2^32 values of W1[57] to find the one that minimizes de57_hw
(Hamming weight of the e-register difference after round 57).

This extends the sequential_modification.py analysis:
- sequential_modification.py fixes dW57 for da57=0, gets ONE de57
- This tool fixes dW57 for da57=0, then tries ALL W1[57] values
  to find the one where the ABSOLUTE e-register positions are
  most favorable for subsequent rounds

Then extends to depth-2: given optimal W57, search all W1[58]
values to minimize error at round 58.

Uses GPU for the embarrassingly parallel W57 sweep.

Usage:
    python3 gpu_optimal_w57.py [candidate_idx]
    # candidate_idx: 0=published (0x17149975), 1=best (0x44b49bc3)
"""

import sys, os, time
import torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from lib.sha256 import K, IV, MASK, hw, add, Sigma0, Sigma1, Ch, Maj, precompute_state


def to_i32(v):
    """Convert unsigned 32-bit int to signed for PyTorch int32."""
    v = v & 0xFFFFFFFF
    return v if v < 0x80000000 else v - 0x100000000


def popcount32_gpu(x):
    x = x - ((x >> 1) & 0x55555555)
    x = (x & 0x33333333) + ((x >> 2) & 0x33333333)
    x = (x + (x >> 4)) & 0x0F0F0F0F
    x = x + (x >> 8)
    x = x + (x >> 16)
    return x & 0x3F


def gpu_ror32(x, k):
    return ((x >> k) | (x << (32 - k))) & 0xFFFFFFFF


def gpu_Sigma0(a):
    return gpu_ror32(a, 2) ^ gpu_ror32(a, 13) ^ gpu_ror32(a, 22)


def gpu_Sigma1(e):
    return gpu_ror32(e, 6) ^ gpu_ror32(e, 11) ^ gpu_ror32(e, 25)


def gpu_Ch(e, f, g):
    return ((e & f) ^ ((~e) & g)) & 0xFFFFFFFF


def gpu_Maj(a, b, c):
    return ((a & b) ^ (a & c) ^ (b & c)) & 0xFFFFFFFF


def gpu_round(state, Ki, Wi):
    """One SHA-256 compression round on GPU tensors."""
    a, b, c, d, e, f, g, h = state
    ch = gpu_Ch(e, f, g)
    T1 = (h + gpu_Sigma1(e) + ch + Ki + Wi) & 0xFFFFFFFF
    maj = gpu_Maj(a, b, c)
    T2 = (gpu_Sigma0(a) + maj) & 0xFFFFFFFF
    return [(T1 + T2) & 0xFFFFFFFF, a, b, c, (d + T1) & 0xFFFFFFFF, e, f, g]


def sweep_w57(s1, s2, dw57, device, batch_size=1 << 22):
    """
    Sweep ALL 2^32 W1[57] values, compute de57_hw for each.
    dw57: the dW needed for da57=0 (W2[57] = W1[57] - dw57).

    Returns: (best_hw, best_w1_57, histogram)
    """
    K57 = torch.tensor(to_i32(K[57]), dtype=torch.int32, device=device)
    dw57_t = torch.tensor(to_i32(dw57), dtype=torch.int32, device=device)

    s1_t = [torch.tensor(to_i32(v), dtype=torch.int32, device=device) for v in s1]
    s2_t = [torch.tensor(to_i32(v), dtype=torch.int32, device=device) for v in s2]

    best_hw = 32
    best_w1 = 0
    hw_hist = torch.zeros(33, dtype=torch.int64, device='cpu')
    total = 1 << 32
    t0 = time.time()

    for start in range(0, total, batch_size):
        bs = min(batch_size, total - start)
        w1_57 = torch.arange(start, start + bs, dtype=torch.int32, device=device)
        w2_57 = (w1_57 - dw57_t) & 0xFFFFFFFF

        # Compute round 57 for both messages
        st1 = gpu_round(s1_t, K57, w1_57)
        st2 = gpu_round(s2_t, K57, w2_57)

        # da57 should be 0 by construction
        # de57 = e1[57] XOR e2[57]
        de57 = st1[4] ^ st2[4]
        de57_hw = popcount32_gpu(de57)

        # Total state diff HW (all 8 registers)
        total_hw = torch.zeros(bs, dtype=torch.int32, device=device)
        for i in range(8):
            total_hw = total_hw + popcount32_gpu(st1[i] ^ st2[i])

        # Track best de57
        batch_min_idx = de57_hw.argmin()
        batch_min_hw = de57_hw[batch_min_idx].item()
        if batch_min_hw < best_hw:
            best_hw = batch_min_hw
            best_w1 = (start + batch_min_idx.item()) & 0xFFFFFFFF
            best_total = total_hw[batch_min_idx].item()
            elapsed = time.time() - t0
            print(f"  new best de57_hw={best_hw} total_hw={best_total} "
                  f"W1[57]=0x{best_w1:08x} ({elapsed:.1f}s, "
                  f"{(start+bs)/total*100:.1f}%)", flush=True)

        # Histogram
        for h in range(33):
            hw_hist[h] += (de57_hw == h).sum().cpu()

        if (start // batch_size) % 256 == 255:
            elapsed = time.time() - t0
            pct = (start + bs) / total * 100
            rate = (start + bs) / elapsed
            print(f"  progress: {pct:.1f}%, {rate/1e6:.1f}M/s, "
                  f"best de57_hw={best_hw}", flush=True)

    elapsed = time.time() - t0
    return best_hw, best_w1, hw_hist, elapsed


def sweep_w58_given_w57(s1, s2, dw57, best_w1_57, device, batch_size=1 << 22):
    """
    Given optimal W1[57], sweep ALL 2^32 W1[58] values.
    Tests both da58=0 and de58=0 constraints, plus unconstrained.
    """
    K57_t = torch.tensor(to_i32(K[57]), dtype=torch.int32, device=device)
    K58_t = torch.tensor(to_i32(K[58]), dtype=torch.int32, device=device)

    s1_t = [torch.tensor(to_i32(v), dtype=torch.int32, device=device) for v in s1]
    s2_t = [torch.tensor(to_i32(v), dtype=torch.int32, device=device) for v in s2]

    # First compute state after round 57 with optimal W57
    w1_57 = torch.tensor(to_i32(best_w1_57), dtype=torch.int32, device=device)
    w2_57 = (w1_57 - torch.tensor(to_i32(dw57), dtype=torch.int32, device=device)) & 0xFFFFFFFF
    st1_57 = gpu_round(s1_t, K57_t, w1_57)
    st2_57 = gpu_round(s2_t, K57_t, w2_57)

    # Compute dW58 for da58=0
    d_h = (st1_57[7] - st2_57[7]) & MASK
    d_Sig1 = (Sigma1(st1_57[4].item()) - Sigma1(st2_57[4].item())) & MASK
    d_Ch = (Ch(st1_57[4].item(), st1_57[5].item(), st1_57[6].item()) -
            Ch(st2_57[4].item(), st2_57[5].item(), st2_57[6].item())) & MASK
    C_T1 = add(d_h.item(), d_Sig1, d_Ch)
    d_Sig0 = (Sigma0(st1_57[0].item()) - Sigma0(st2_57[0].item())) & MASK
    d_Maj = (Maj(st1_57[0].item(), st1_57[1].item(), st1_57[2].item()) -
             Maj(st2_57[0].item(), st2_57[1].item(), st2_57[2].item())) & MASK
    C_T2 = add(d_Sig0, d_Maj)
    dw58_a = (-add(C_T1, C_T2)) & MASK

    # Compute dW58 for de58=0
    d_d = (st1_57[3] - st2_57[3]) & MASK
    dw58_e = (-add(d_d.item(), C_T1)) & MASK

    print(f"\n  dW58 for da58=0: 0x{dw58_a:08x}")
    print(f"  dW58 for de58=0: 0x{dw58_e:08x}")

    # Now sweep W1[58] with da58=0 constraint
    dw58_t = torch.tensor(to_i32(dw58_a), dtype=torch.int32, device=device)

    best_hw = 256
    best_w1_58 = 0
    total = 1 << 32
    t0 = time.time()

    for start in range(0, total, batch_size):
        bs = min(batch_size, total - start)
        w1_58 = torch.arange(start, start + bs, dtype=torch.int32, device=device)
        w2_58 = (w1_58 - dw58_t) & 0xFFFFFFFF

        st1_58 = gpu_round([s.expand(bs) if s.dim() == 0 else s.expand(bs)
                            for s in st1_57], K58_t, w1_58)
        st2_58 = gpu_round([s.expand(bs) if s.dim() == 0 else s.expand(bs)
                            for s in st2_57], K58_t, w2_58)

        total_hw = torch.zeros(bs, dtype=torch.int32, device=device)
        for i in range(8):
            total_hw = total_hw + popcount32_gpu(st1_58[i] ^ st2_58[i])

        batch_min_idx = total_hw.argmin()
        batch_min_hw = total_hw[batch_min_idx].item()
        if batch_min_hw < best_hw:
            best_hw = batch_min_hw
            best_w1_58 = (start + batch_min_idx.item()) & 0xFFFFFFFF
            elapsed = time.time() - t0
            de58 = (st1_58[4][batch_min_idx] ^ st2_58[4][batch_min_idx]).item()
            print(f"  new best total_hw={best_hw} de58_hw={hw(de58)} "
                  f"W1[58]=0x{best_w1_58:08x} ({elapsed:.1f}s)", flush=True)

        if (start // batch_size) % 256 == 255:
            elapsed = time.time() - t0
            pct = (start + bs) / total * 100
            print(f"  W58 sweep: {pct:.1f}%, best_total_hw={best_hw}", flush=True)

    elapsed = time.time() - t0
    return best_hw, best_w1_58, dw58_a, elapsed


def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    candidates = [
        (0x17149975, 0xFFFFFFFF, "published"),
        (0x44b49bc3, 0xFFFFFFFF, "best_de57"),
    ]

    idx = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    m0, fill, label = candidates[idx]

    print(f"GPU Optimal W57 Search: {label} (M[0]=0x{m0:08x})")
    print(f"Device: {device}")
    print()

    M1 = [m0] + [fill]*15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1, W1 = precompute_state(M1)
    s2, W2 = precompute_state(M2)
    assert s1[0] == s2[0], f"da56 != 0"

    # Compute dW57 for da57=0
    d_h = (s1[7] - s2[7]) & MASK
    d_Sig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    d_Ch = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    C_T1 = add(d_h, d_Sig1, d_Ch)
    d_Sig0 = (Sigma0(s1[0]) - Sigma0(s2[0])) & MASK
    d_Maj = (Maj(s1[0], s1[1], s1[2]) - Maj(s2[0], s2[1], s2[2])) & MASK
    C_T2 = add(d_Sig0, d_Maj)
    dw57 = (-add(C_T1, C_T2)) & MASK
    print(f"dW57 for da57=0: 0x{dw57:08x}")

    # Phase 1: Sweep all W1[57]
    print(f"\n{'='*60}")
    print(f"PHASE 1: Exhaustive W1[57] sweep (2^32 values)")
    print(f"{'='*60}")
    best_hw57, best_w1_57, hist, t = sweep_w57(s1, s2, dw57, device)

    print(f"\nPhase 1 result: best de57_hw = {best_hw57}")
    print(f"  W1[57] = 0x{best_w1_57:08x}")
    print(f"  W2[57] = 0x{(best_w1_57 - dw57) & MASK:08x}")
    print(f"  Time: {t:.1f}s")
    print(f"\n  de57_hw histogram (how many W1[57] give each hw):")
    for h in range(min(best_hw57 + 5, 33)):
        count = hist[h].item()
        if count > 0:
            print(f"    hw={h:2d}: {count:>10,} values ({count/2**32*100:.4f}%)")

    # Phase 2: Given optimal W57, sweep W58
    print(f"\n{'='*60}")
    print(f"PHASE 2: Exhaustive W1[58] sweep with da58=0 (2^32 values)")
    print(f"{'='*60}")
    best_hw58, best_w1_58, dw58, t2 = sweep_w58_given_w57(
        s1, s2, dw57, best_w1_57, device)

    print(f"\nPhase 2 result: best total_hw after round 58 = {best_hw58}")
    print(f"  W1[58] = 0x{best_w1_58:08x}")
    print(f"  Time: {t2:.1f}s")

    print(f"\n{'='*60}")
    print(f"SUMMARY: Sequential modification with GPU-optimal free words")
    print(f"  Candidate: {label} (M[0]=0x{m0:08x})")
    print(f"  W1[57] = 0x{best_w1_57:08x} → de57_hw = {best_hw57}")
    print(f"  W1[58] = 0x{best_w1_58:08x} → total_hw_58 = {best_hw58}")
    print(f"  Remaining free: W[59], W[60] (2 words = 64 bits)")
    print(f"  Total GPU time: {t + t2:.1f}s")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
