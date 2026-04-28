#!/usr/bin/env python3
"""
validate_predictor.py — empirical validation of the F90 algebraic
predictor on cascade-1 survivor sets.

The F90 predictor for low-HW cascade-1 (at N=8): a dm pattern is
LIKELY to achieve low residual HW if all of the following hold:
  - dm[p1].bit-MSB == 1   (cascade kernel position)
  - dm[p2].bit-LSB == 1   (LSB enrichment signal)
  - dm[p2].bit-3   == 0   (anti-correlation signal at small N)

This script applies that 3-bit predicate to a survivor JSON, splits
into PREDICTED and NOT-PREDICTED groups, and reports the low-HW
enrichment ratio.

If the predictor works, PREDICTED group has higher fraction of
low-HW survivors than NOT-PREDICTED. The F90 claim is a ~2× boost.

Usage:
    python3 validate_predictor.py n8_cascade_survivors.json
    python3 validate_predictor.py n10_cascade_survivors.json --low-hw 28
"""
import argparse
import json
import statistics
import sys


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("survivor_json")
    ap.add_argument("--low-hw", type=int, default=None,
                    help="Low-HW threshold (default: 25th percentile)")
    args = ap.parse_args()

    data = json.load(open(args.survivor_json))
    N = data["N"]
    p1, p2 = data["positions"]
    survivors = data["survivors"]

    if not survivors:
        print("No survivors.")
        sys.exit(0)

    # F90 predictor: MSB of dm[p1] set, LSB of dm[p2] set, bit-3 of dm[p2] clear
    msb = N - 1
    def predicted(s):
        d1, d2 = s["dm"]
        return ((d1 >> msb) & 1) == 1 and ((d2 >> 0) & 1) == 1 and ((d2 >> 3) & 1) == 0

    pred_set = [s for s in survivors if predicted(s)]
    not_pred = [s for s in survivors if not predicted(s)]

    threshold = args.low_hw
    if threshold is None:
        sorted_hws = sorted(s["residual_hw"] for s in survivors)
        threshold = sorted_hws[len(sorted_hws) // 4]

    def stat(group, name):
        if not group:
            print(f"  {name}: empty")
            return None
        hws = [s["residual_hw"] for s in group]
        low_hw = sum(1 for h in hws if h <= threshold)
        print(f"  {name}: n={len(group)}, min={min(hws)}, "
              f"median={statistics.median(hws):.1f}, mean={statistics.mean(hws):.2f}, "
              f"max={max(hws)}")
        print(f"    low-HW (≤{threshold}): {low_hw}/{len(group)} = {100*low_hw/len(group):.1f}%")
        return low_hw / len(group)

    print(f"=== F90 Predictor validation (N={N}, positions=[{p1}, {p2}]) ===")
    print(f"  Predictor: dm[{p1}].bit{msb}=1 AND dm[{p2}].bit0=1 AND dm[{p2}].bit3=0")
    print(f"  Survivors: {len(survivors)}")
    print(f"  Low-HW threshold: ≤{threshold}")
    print()
    pred_low = stat(survivors, "ALL survivors")
    pred_pred = stat(pred_set, "PREDICTED set")
    pred_notpred = stat(not_pred, "NOT predicted")

    print()
    if pred_pred and pred_notpred and pred_notpred > 0:
        ratio = pred_pred / pred_notpred
        print(f"Low-HW enrichment: {pred_pred:.3f} / {pred_notpred:.3f} = {ratio:.2f}× boost")
        if ratio > 1.5:
            print(f"  → Predictor VALIDATED (ratio > 1.5×)")
        elif ratio > 1.0:
            print(f"  → Predictor weakly validated (1.0 < ratio < 1.5)")
        else:
            print(f"  → Predictor FAILED (ratio < 1.0)")


if __name__ == "__main__":
    main()
