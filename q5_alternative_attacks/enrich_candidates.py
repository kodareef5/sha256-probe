#!/usr/bin/env python3
"""
enrich_candidates.py — Augment Q3 candidate CSV files with sr=61 algebraic metrics.

For each known da[56]=0 candidate, computes:
- delta_const_xor / hw_delta_const: the sr=61 W[60] rule offset between M1 and M2
- hw_dW44, hw_dW45, hw_dW53: pre-schedule differential propagation
- hw_dW54, hw_dW55, hw_dW56: how the differential evolves into the late-round window
- hw_dC57: dW[61] constant from W[54]+sigma0(W[46])+W[45] (for sr=60 W[61] rule)

Output: combined CSV with all metrics, sorted by hw_delta_const ascending.
"""

import sys, os, glob, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def compute_metrics(M0, fill):
    M1 = [M0] + [fill] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1, W1 = precompute_state(M1)
    s2, W2 = precompute_state(M2)

    if s1[0] != s2[0]:
        return None

    # sr=61 W[60] rule: W[60] = sigma1(W[58]) + W[53] + sigma0(W[45]) + W[44]
    delta_const = (add(W1[53], sigma0(W1[45]), W1[44]) -
                   add(W2[53], sigma0(W2[45]), W2[44])) & MASK
    delta_const_xor = (add(W1[53], sigma0(W1[45]), W1[44]) ^
                       add(W2[53], sigma0(W2[45]), W2[44]))

    # sr=60 W[61] rule constant: dW[61] = sigma1_diff(W[59]) + (dW[54]+dsigma0(W[46])+dW[45])
    dC_61 = (add(W1[54], sigma0(W1[46]), W1[45]) -
             add(W2[54], sigma0(W2[46]), W2[45])) & MASK

    # Per-word differential HW around the critical window
    diffs = {}
    for i in range(40, 57):
        diffs[i] = hw(W1[i] ^ W2[i])

    # Total state diff at round 56
    hw56 = sum(hw(s1[r] ^ s2[r]) for r in range(8))

    # State per-register HW
    state_hw = [hw(s1[r] ^ s2[r]) for r in range(8)]

    return {
        'M0': M0, 'fill': fill,
        'hw56': hw56,
        'state_hw': state_hw,
        'delta_const_xor': delta_const_xor,
        'hw_delta_const': hw(delta_const_xor),
        'dC_61_xor': hw(dC_61),
        'hw_dW44': diffs[44], 'hw_dW45': diffs[45], 'hw_dW46': diffs[46],
        'hw_dW53': diffs[53], 'hw_dW54': diffs[54], 'hw_dW55': diffs[55],
        'hw_dW56': diffs[56],
    }


def load_existing_candidates():
    """Load all M0,fill pairs from Q3 CSV outputs."""
    base = '/root/sha256_probe/q3_candidate_families/results/20260405_mitm_scan'
    cands = []
    for f in sorted(glob.glob(f'{base}/*.csv')):
        with open(f) as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                cands.append((int(row['m0'], 16), int(row['fill'], 16)))
    return cands


def main():
    cands = load_existing_candidates()
    print(f"Loaded {len(cands)} candidates from Q3 scan results\n")

    rows = []
    for M0, fill in cands:
        m = compute_metrics(M0, fill)
        if m is not None:
            rows.append(m)

    # Sort by hw_delta_const ascending (lowest = potentially best for sr=61)
    rows.sort(key=lambda r: r['hw_delta_const'])

    # Print compact table
    print(f"{'M0':<12} {'fill':<12} {'hw56':<5} {'hw_dC':<6} "
          f"{'hw_dC_61':<9} {'dW44':<5} {'dW45':<5} {'dW46':<5} "
          f"{'dW53':<5} {'dW54':<5} {'dW55':<5} {'dW56':<5}")
    print("-" * 100)
    for r in rows:
        print(f"0x{r['M0']:08x}  0x{r['fill']:08x}  {r['hw56']:<5} "
              f"{r['hw_delta_const']:<6} {r['dC_61_xor']:<9} "
              f"{r['hw_dW44']:<5} {r['hw_dW45']:<5} {r['hw_dW46']:<5} "
              f"{r['hw_dW53']:<5} {r['hw_dW54']:<5} {r['hw_dW55']:<5} {r['hw_dW56']:<5}")

    print()
    print("Statistics across all candidates:")
    if rows:
        for key in ['hw_delta_const', 'hw_dW44', 'hw_dW45', 'hw_dW46',
                    'hw_dW53', 'hw_dW54', 'hw_dW55', 'hw_dW56']:
            vals = [r[key] for r in rows]
            print(f"  {key:<15}: min={min(vals)}, max={max(vals)}, "
                  f"mean={sum(vals)/len(vals):.1f}")


if __name__ == "__main__":
    main()
