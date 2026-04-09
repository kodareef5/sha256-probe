#!/usr/bin/env python3
"""
delta_const_scan.py — Compute the per-candidate delta_const = const_M1 - const_M2
where const = W[53] + sigma0(W[45]) + W[44].

This is the "fixed offset" between the sr=61 schedule rule for M1 and M2.
A small delta_const means the two messages' W[60] values are constrained
to differ only by sigma1(W1[58]) - sigma1(W2[58]) (modulo small offset).

Hypothesis: smaller |delta_const| or special structure in delta_const
might make sr=61 easier for some candidates than others.

Also computes hw_delta_const, which we can compare against solver
runtime correlations later.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def candidate_metrics(M0, fill):
    M1 = [M0] + [fill] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1, W1_pre = precompute_state(M1)
    s2, W2_pre = precompute_state(M2)

    # Verify da[56] = 0 (candidate validity)
    if s1[0] != s2[0]:
        return None

    const_M1 = add(W1_pre[53], sigma0(W1_pre[45]), W1_pre[44])
    const_M2 = add(W2_pre[53], sigma0(W2_pre[45]), W2_pre[44])
    delta_const = (const_M1 - const_M2) & MASK
    delta_xor = const_M1 ^ const_M2

    # Also compute the W[44], W[45], W[53] differentials directly
    dW44 = (W1_pre[44] - W2_pre[44]) & MASK
    dW45 = (W1_pre[45] - W2_pre[45]) & MASK
    dW53 = (W1_pre[53] - W2_pre[53]) & MASK

    return {
        'M0': M0,
        'fill': fill,
        'da56': 0,  # passes
        'const_M1': const_M1,
        'const_M2': const_M2,
        'delta_const_add': delta_const,
        'delta_const_xor': delta_xor,
        'hw_delta_xor': hw(delta_xor),
        'hw_delta_add': hw(delta_const),
        'dW44': dW44,
        'dW45': dW45,
        'dW53': dW53,
        'hw_dW44': hw(W1_pre[44] ^ W2_pre[44]),
        'hw_dW45': hw(W1_pre[45] ^ W2_pre[45]),
        'hw_dW53': hw(W1_pre[53] ^ W2_pre[53]),
    }


def main():
    print("=== delta_const scan: 4 known candidates ===\n")
    candidates = [
        (0x17149975, 0xFFFFFFFF, "primary (sr=60 SAT)"),
        (0xa22dc6c7, 0xFFFFFFFF, "alt 1"),
        (0x9cfea9ce, 0x00000000, "alt 2"),
        (0x3f239926, 0xAAAAAAAA, "alt 3"),
    ]

    print(f"{'M0':<12} {'fill':<12} {'tag':<22} {'delta_const_add':<12} "
          f"{'hw_xor':<7} {'hw_add':<7} {'hw_dW44':<8} {'hw_dW45':<8} {'hw_dW53':<8}")
    print("-" * 110)
    for M0, fill, tag in candidates:
        m = candidate_metrics(M0, fill)
        if m is None:
            print(f"0x{M0:08x}  0x{fill:08x}  {tag:<22}  da56!=0 (skip)")
            continue
        print(f"0x{M0:08x}  0x{fill:08x}  {tag:<22}  "
              f"0x{m['delta_const_add']:08x}  "
              f"{m['hw_delta_xor']:<7} {m['hw_delta_add']:<7} "
              f"{m['hw_dW44']:<8} {m['hw_dW45']:<8} {m['hw_dW53']:<8}")

    print()
    print("Interpretation:")
    print("  delta_const is the fixed offset in M2's sr=61 W[60] rule vs M1's")
    print("  Smaller |delta_const| means W1[60] and W2[60] are closer to each other")
    print("    (only differ by sigma1(W1[58]) - sigma1(W2[58]))")
    print("  Smaller hw_dW44/45/53 means earlier-round propagation kept differentials small")


if __name__ == "__main__":
    main()
