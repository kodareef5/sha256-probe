#!/usr/bin/env python3
"""
partition_thermometer.py — Measure thermodynamic temperature per partition

For each 8-bit partition of W1[58] MSBs (with da57=0 constraint),
sample random values for the remaining free bits and measure the
minimum collision HW achievable.

Partitions where random sampling gets close to HW=0 are "hot" —
they contain the region where a collision is most likely.
Partitions where minimum HW stays high are "cold" — skip them.

This guides WHERE to spend compute: focus long solver runs on the
hottest partitions instead of uniform allocation.

Usage: python3 partition_thermometer.py [n_samples_per_partition]
"""

import sys, os, random, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def measure_partition_temperature(s1, s2, W1_pre, W2_pre, dw57,
                                   n_bits, pval, n_samples=100000):
    """Sample random free words and measure min collision HW for this partition."""
    random.seed(pval * 1337 + 42)  # deterministic per partition

    best_hw = 256
    hw_sum = 0

    for _ in range(n_samples):
        # W1[57] determined by da57=0 + random W2[57]
        w2_57 = random.getrandbits(32)
        w1_57 = (w2_57 + dw57) & MASK

        # W1[58] has MSBs fixed by partition
        w1_58_base = pval << (32 - n_bits)
        w1_58 = w1_58_base | (random.getrandbits(32 - n_bits))
        w2_58 = random.getrandbits(32)

        w1_59 = random.getrandbits(32)
        w2_59 = random.getrandbits(32)
        w1_60 = random.getrandbits(32)
        w2_60 = random.getrandbits(32)

        # Build schedule tail
        w1 = [w1_57, w1_58, w1_59, w1_60]
        w2 = [w2_57, w2_58, w2_59, w2_60]

        W1t = list(w1)
        W2t = list(w2)
        W1t.append(add(sigma1(w1[2]), W1_pre[54], sigma0(W1_pre[46]), W1_pre[45]))
        W2t.append(add(sigma1(w2[2]), W2_pre[54], sigma0(W2_pre[46]), W2_pre[45]))
        W1t.append(add(sigma1(w1[3]), W1_pre[55], sigma0(W1_pre[47]), W1_pre[46]))
        W2t.append(add(sigma1(w2[3]), W2_pre[55], sigma0(W2_pre[47]), W2_pre[46]))
        W1t.append(add(sigma1(W1t[4]), W1_pre[56], sigma0(W1_pre[48]), W1_pre[47]))
        W2t.append(add(sigma1(W2t[4]), W2_pre[56], sigma0(W2_pre[48]), W2_pre[47]))

        # Run 7 tail rounds
        trace1 = run_tail_rounds(s1, W1t)
        trace2 = run_tail_rounds(s2, W2t)
        f1, f2 = trace1[-1], trace2[-1]

        total_hw = sum(hw(f1[i] ^ f2[i]) for i in range(8))
        if total_hw < best_hw:
            best_hw = total_hw
        hw_sum += total_hw

    return best_hw, hw_sum / n_samples


if __name__ == "__main__":
    n_samples = int(sys.argv[1]) if len(sys.argv) > 1 else 50000

    m0 = 0x44b49bc3; fill = 0x80000000
    M1 = [m0]+[fill]*15; M2 = list(M1); M2[0]^=0x80000000; M2[9]^=0x80000000
    s1, W1 = precompute_state(M1); s2, W2 = precompute_state(M2)

    d_h56=(s1[7]-s2[7])&MASK; d_Sig1=(Sigma1(s1[4])-Sigma1(s2[4]))&MASK
    d_Ch=(Ch(s1[4],s1[5],s1[6])-Ch(s2[4],s2[5],s2[6]))&MASK; C_T1=(d_h56+d_Sig1+d_Ch)&MASK
    d_Sig0=(Sigma0(s1[0])-Sigma0(s2[0]))&MASK; d_Maj=(Maj(s1[0],s1[1],s1[2])-Maj(s2[0],s2[1],s2[2]))&MASK
    C_T2=(d_Sig0+d_Maj)&MASK; dw57=(-(C_T1+C_T2))&MASK

    n_bits = 8
    n_parts = 2**n_bits

    print(f"Partition Thermometer: {n_parts} partitions × {n_samples} samples")
    print(f"Candidate: 0x{m0:08x}, da57=0, {n_bits} bits of W1[58] fixed")
    print(f"{'='*60}", flush=True)

    results = []
    t0 = time.time()

    for pval in range(n_parts):
        best, mean = measure_partition_temperature(
            s1, s2, W1, W2, dw57, n_bits, pval, n_samples)
        results.append((pval, best, mean))

        if (pval+1) % 32 == 0:
            elapsed = time.time() - t0
            print(f"  [{pval+1}/{n_parts}] {elapsed:.0f}s", flush=True)

    # Sort by best HW (hottest first)
    results.sort(key=lambda x: x[1])

    print(f"\n{'='*60}")
    print(f"Top 20 hottest partitions (closest to collision):")
    print(f"{'Part':>6s} {'Best HW':>8s} {'Mean HW':>8s}")
    for pval, best, mean in results[:20]:
        marker = " <<<" if best < 90 else ""
        print(f"{pval:>6d} {best:>8d} {mean:>8.1f}{marker}")

    print(f"\nColdest 5 partitions:")
    for pval, best, mean in results[-5:]:
        print(f"{pval:>6d} {best:>8d} {mean:>8.1f}")

    # Check if ANY partition has meaningfully different temperature
    bests = [r[1] for r in results]
    print(f"\nBest HW range: {min(bests)} to {max(bests)}")
    print(f"Mean of bests: {sum(bests)/len(bests):.1f}")

    if max(bests) - min(bests) < 5:
        print("All partitions have similar temperature — no structure detected.")
        print("This is consistent with the thermodynamic floor being partition-independent.")
    else:
        print(f"Temperature varies by {max(bests)-min(bests)} — some partitions are hotter!")
        print("Focus solver time on the hottest partitions.")
