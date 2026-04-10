#!/usr/bin/env python3
"""
Forward pass of the cascade MITM: enumerate (W[57], W[58], W[59], W[60])
with cascade constraints applied (W[57] zeros da57, W[60] zeros de60) and
measure the residual collision distance at round 63.

This is the direct version of the MITM — rather than pre-computing half
and half, we sample the constrained 2^96 space and look for low-distance
combinations. If random sampling finds near-collisions quickly, the
cascade decomposition is powerful. If not, we know the constraint space
is still too large for pure random search.

Usage: python3 cascade_forward_scan.py [n_samples]
"""

import sys, os, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def precompute_offsets(m0, fill):
    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1, W1_pre = precompute_state(M1)
    s2, W2_pre = precompute_state(M2)

    # Cascade 1 offset (for da57=0)
    dh = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    T2_1 = (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & MASK
    T2_2 = (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & MASK
    dT2 = (T2_1 - T2_2) & MASK
    C_w57 = (dh + dSig1 + dCh + dT2) & MASK

    return s1, s2, W1_pre, W2_pre, C_w57


def one_round(s, w, i):
    T1 = add(s[7], Sigma1(s[4]), Ch(s[4], s[5], s[6]), K[i], w)
    T2 = add(Sigma0(s[0]), Maj(s[0], s[1], s[2]))
    return (add(T1, T2), s[0], s[1], s[2], add(s[3], T1), s[4], s[5], s[6])


def sample_with_cascades(s1_init, s2_init, W1_pre, W2_pre, C_w57, rng):
    """Sample one (W[57..60]) tuple with cascade constraints, return final HW."""
    w1_57 = rng.getrandbits(32)
    w2_57 = (w1_57 + C_w57) & MASK
    w1_58 = rng.getrandbits(32); w2_58 = rng.getrandbits(32)
    w1_59 = rng.getrandbits(32); w2_59 = rng.getrandbits(32)

    # Apply rounds 57-59
    s1 = one_round(s1_init, w1_57, 57)
    s2 = one_round(s2_init, w2_57, 57)
    s1 = one_round(s1, w1_58, 58)
    s2 = one_round(s2, w2_58, 58)
    s1 = one_round(s1, w1_59, 59)
    s2 = one_round(s2, w2_59, 59)

    # Cascade 2 offset at round 59
    dh59 = (s1[7] - s2[7]) & MASK
    dSig1_59 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh_59 = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    C_w60 = (dh59 + dSig1_59 + dCh_59) & MASK

    w1_60 = rng.getrandbits(32)
    w2_60 = (w1_60 + C_w60) & MASK

    # Complete 7-round tail
    W1_tail = build_schedule_tail(W1_pre, [w1_57, w1_58, w1_59, w1_60])
    W2_tail = build_schedule_tail(W2_pre, [w2_57, w2_58, w2_59, w2_60])
    t1 = run_tail_rounds(s1_init, W1_tail)
    t2 = run_tail_rounds(s2_init, W2_tail)
    f1, f2 = t1[-1], t2[-1]
    total = sum(hw(f1[r] ^ f2[r]) for r in range(8))
    per_reg = [hw(f1[r] ^ f2[r]) for r in range(8)]
    return total, per_reg, [w1_57, w1_58, w1_59, w1_60]


def main():
    n_samples = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
    m0 = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x17149975
    fill = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0xFFFFFFFF

    print(f"Cascade-constrained forward scan")
    print(f"Candidate: M[0]=0x{m0:08x}, fill=0x{fill:08x}")
    print(f"Samples: {n_samples:,}")
    print()

    s1, s2, W1_pre, W2_pre, C_w57 = precompute_offsets(m0, fill)
    print(f"Cascade 1 offset C_w57 = 0x{C_w57:08x}")
    print()

    rng = random.Random(42)
    t0 = time.time()
    min_hw = 256
    best_sample = None
    hw_counts = {}

    for i in range(n_samples):
        total, per_reg, ws = sample_with_cascades(s1, s2, W1_pre, W2_pre, C_w57, rng)
        hw_counts[total] = hw_counts.get(total, 0) + 1
        if total < min_hw:
            min_hw = total
            best_sample = (ws, per_reg)
            print(f"  [{i:>7}] NEW BEST: total_hw={total} "
                  f"per_reg={per_reg}", flush=True)
            if total == 0:
                print(f"  COLLISION! W[57..60] = {[f'0x{w:08x}' for w in ws]}")
                break
        if (i + 1) % 10000 == 0:
            rate = (i + 1) / (time.time() - t0)
            print(f"  [{i+1:>7}/{n_samples}] {rate:.0f} samples/s, min so far={min_hw}",
                  flush=True)

    t1 = time.time() - t0
    print(f"\nDone in {t1:.1f}s ({n_samples/t1:.0f} samples/s)")
    print(f"Minimum HW found: {min_hw}")
    if best_sample:
        print(f"Best W[57..60]: {[f'0x{w:08x}' for w in best_sample[0]]}")
        print(f"Best per-reg:   {best_sample[1]}")

    # Distribution
    print(f"\nHW distribution:")
    sorted_hws = sorted(hw_counts.keys())
    for h in sorted_hws:
        if h % 5 == 0 or hw_counts[h] > n_samples * 0.02:
            bar = '#' * min(hw_counts[h] * 40 // n_samples, 60)
            print(f"  {h:3d}: {hw_counts[h]:6d} {bar}")


if __name__ == "__main__":
    main()
