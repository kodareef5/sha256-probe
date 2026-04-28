#!/usr/bin/env python3
"""
analyze_cascade_bits.py — bit-position analysis on cascade-filter survivors.

Reads the JSON output of forward_bounded_searcher --cascade-filter and
computes per-bit statistics on the dm patterns that satisfy the
cascade signature:

  1. Bit-frequency: how often does each bit of dm[p1], dm[p2] appear set
     among survivors? Uniform = no correlation; biased = algebraic
     constraint.
  2. Bit-pair correlations: which dm bits co-occur or are mutually
     exclusive among survivors?
  3. Low-HW correlation: which dm bits are over-represented among
     low-residual-HW survivors?

These statistics characterize WHICH dm bits are "necessary" for the
cascade-1 a-zero signature at round 60.

Usage:
    python3 analyze_cascade_bits.py n8_cascade_survivors.json
"""
import argparse
import json
import sys
from collections import Counter


def bit_set_at(value, bit):
    return (value >> bit) & 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("survivor_json", help="JSON output from --cascade-filter --out-json")
    ap.add_argument("--low-hw-threshold", type=int, default=None,
                    help="Threshold for 'low HW' correlation. "
                         "Defaults to the median of the survivor HW distribution.")
    args = ap.parse_args()

    data = json.load(open(args.survivor_json))
    N = data["N"]
    positions = data["positions"]
    survivors = data["survivors"]

    if not survivors:
        print("No survivors to analyze.")
        sys.exit(0)

    p1, p2 = positions
    print(f"=== Bit-position analysis (N={N}, positions={positions}) ===")
    print(f"Constraints:    {data['constraints']}")
    print(f"Survivors:      {len(survivors)}")
    print(f"HW range:       [{min(s['residual_hw'] for s in survivors)}, "
          f"{max(s['residual_hw'] for s in survivors)}]")

    # 1. Per-bit frequency
    bit_count_p1 = [0] * N
    bit_count_p2 = [0] * N
    for s in survivors:
        d1, d2 = s["dm"]
        for b in range(N):
            bit_count_p1[b] += bit_set_at(d1, b)
            bit_count_p2[b] += bit_set_at(d2, b)
    total = len(survivors)

    print(f"\n--- Bit frequency (N={N}, dm bits 0={'LSB'} .. {N-1}=MSB) ---")
    print(f"  Uniform expectation: {total/2:.0f} (50%)")
    print(f"  Bit | dm[{p1}] count (%) | dm[{p2}] count (%)")
    print(f"  ----+-{'-'*18}+-{'-'*18}")
    for b in range(N):
        c1, c2 = bit_count_p1[b], bit_count_p2[b]
        bias1 = (c1 / total) - 0.5
        bias2 = (c2 / total) - 0.5
        flag1 = " HOT" if abs(bias1) > 0.20 else (" cold" if abs(bias1) > 0.10 else "")
        flag2 = " HOT" if abs(bias2) > 0.20 else (" cold" if abs(bias2) > 0.10 else "")
        print(f"  {b:>3} | {c1:>5} ({100*c1/total:>5.1f}%){flag1:<6} | "
              f"{c2:>5} ({100*c2/total:>5.1f}%){flag2}")

    # 2. Bit pairs (dm[p1] x dm[p2]) — find tight correlations
    # For each (i, j) compute P(dm[p1] bit i set AND dm[p2] bit j set)
    print(f"\n--- Top dm[{p1}] × dm[{p2}] bit-pair correlations ---")
    print(f"  (looking for pairs where co-occurrence deviates from independence)")
    pair_correlations = []
    for i in range(N):
        for j in range(N):
            both_set = sum(1 for s in survivors
                           if bit_set_at(s["dm"][0], i) and bit_set_at(s["dm"][1], j))
            p_i = bit_count_p1[i] / total
            p_j = bit_count_p2[j] / total
            expected = p_i * p_j * total
            if expected > 0:
                ratio = both_set / expected
                deviation = abs(ratio - 1.0)
                if deviation > 0.15 and (both_set > 5 or expected > 5):
                    pair_correlations.append({
                        "i": i, "j": j,
                        "observed": both_set,
                        "expected": round(expected, 1),
                        "ratio": round(ratio, 2),
                    })
    pair_correlations.sort(key=lambda x: abs(x["ratio"] - 1.0), reverse=True)
    if pair_correlations:
        for pc in pair_correlations[:8]:
            sign = "↑" if pc["ratio"] > 1 else "↓"
            print(f"  dm[{p1}].{pc['i']:>2} & dm[{p2}].{pc['j']:>2}: "
                  f"obs={pc['observed']:>4}, exp={pc['expected']:>5.1f}, "
                  f"ratio={pc['ratio']:.2f} {sign}")
    else:
        print("  (no strong correlations above threshold)")

    # 3. Low-HW correlation
    threshold = args.low_hw_threshold
    if threshold is None:
        sorted_hws = sorted(s["residual_hw"] for s in survivors)
        threshold = sorted_hws[len(sorted_hws) // 4]  # 25th percentile
    low_hw_survivors = [s for s in survivors if s["residual_hw"] <= threshold]
    print(f"\n--- Low-HW correlation (HW ≤ {threshold}, "
          f"{len(low_hw_survivors)} survivors out of {total}) ---")
    if low_hw_survivors:
        bit_count_lowhw_p1 = [0] * N
        bit_count_lowhw_p2 = [0] * N
        for s in low_hw_survivors:
            d1, d2 = s["dm"]
            for b in range(N):
                bit_count_lowhw_p1[b] += bit_set_at(d1, b)
                bit_count_lowhw_p2[b] += bit_set_at(d2, b)
        n_low = len(low_hw_survivors)
        print(f"  Bit | dm[{p1}] base→low (%)        | dm[{p2}] base→low (%)")
        print(f"  ----+-{'-'*30}+-{'-'*30}")
        for b in range(N):
            base_freq1 = bit_count_p1[b] / total
            low_freq1 = bit_count_lowhw_p1[b] / n_low
            ratio1 = (low_freq1 / base_freq1) if base_freq1 > 0 else float("inf")
            base_freq2 = bit_count_p2[b] / total
            low_freq2 = bit_count_lowhw_p2[b] / n_low
            ratio2 = (low_freq2 / base_freq2) if base_freq2 > 0 else float("inf")
            flag1 = " ENRICHED" if ratio1 > 1.3 else (" depleted" if ratio1 < 0.7 else "")
            flag2 = " ENRICHED" if ratio2 > 1.3 else (" depleted" if ratio2 < 0.7 else "")
            print(f"  {b:>3} | {100*base_freq1:>5.1f}% → {100*low_freq1:>5.1f}% "
                  f"(×{ratio1:.2f}){flag1:<11} | "
                  f"{100*base_freq2:>5.1f}% → {100*low_freq2:>5.1f}% "
                  f"(×{ratio2:.2f}){flag2}")


if __name__ == "__main__":
    main()
