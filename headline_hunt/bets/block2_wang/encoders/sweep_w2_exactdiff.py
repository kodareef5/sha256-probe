#!/usr/bin/env python3
"""
sweep_w2_exactdiff.py - rank simple single-round block-2 exact_diff probes.

This is a lightweight design-space probe for trail iteration. It loads a
2blockcertpin/v1 bundle, derives candidate diff words from the block-1
working-state residual and/or the actual block-2 chain-input diff, then
tests one W2 `exact_diff` constraint at a time.

Small sample counts are for triage only. Re-run interesting candidates
with >=100 samples before treating an apparent improvement as structural.

The current simulator supports W2 exact/exact_diff rounds 0..24. Later
rounds require a real late-schedule synthesizer and are intentionally not
included by default.

Usage:
    python3 sweep_w2_exactdiff.py bit3_HW55_naive_blocktwo.json
    python3 sweep_w2_exactdiff.py bundle.json --rounds 0-24 --diff-source both
"""
import argparse
import copy
import json
import os
import sys


REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)

from headline_hunt.bets.block2_wang.encoders.simulate_2block_absorption import (
    REGS,
    hw_tuple,
    reconstruct_block1,
    simulate_bundle,
    xor_tuple,
)


def parse_rounds(spec):
    rounds = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = [int(x) for x in part.split("-", 1)]
            rounds.extend(range(lo, hi + 1))
        else:
            rounds.append(int(part))
    return sorted(set(rounds))


def candidate_diffs(bundle, source):
    b1 = bundle["block1"]
    state1_63, state2_63, chain1_out, chain2_out = reconstruct_block1(b1)
    working = xor_tuple(state1_63, state2_63)
    chain = xor_tuple(chain1_out, chain2_out)

    candidates = []
    if source in {"working", "both"}:
        candidates.extend(("working_" + reg, val) for reg, val in zip(REGS, working))
    if source in {"chain", "both"}:
        candidates.extend(("chain_" + reg, val) for reg, val in zip(REGS, chain))

    seen = set()
    out = []
    for label, val in candidates:
        if val == 0 or val in seen:
            continue
        seen.add(val)
        out.append((label, val))
    return out, hw_tuple(working), hw_tuple(chain)


def run_variant(bundle, round_idx, diff, n_samples):
    variant = copy.deepcopy(bundle)
    variant["block2"]["W2_constraints"] = [
        {"round": round_idx, "type": "exact_diff", "diff": f"0x{diff:08x}"}
    ]
    return simulate_bundle(variant, n_samples=n_samples)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bundle", help="2blockcertpin/v1 trail bundle JSON")
    ap.add_argument("--rounds", default="0-24",
                    help="Rounds to probe, e.g. '0-24' or '0,5,9,16'")
    ap.add_argument("--diff-source", choices=["chain", "working", "both"],
                    default="chain",
                    help="Candidate diff words to test")
    ap.add_argument("--n-samples", type=int, default=20)
    ap.add_argument("--top-k", type=int, default=20)
    ap.add_argument("--out-json", default=None)
    args = ap.parse_args()

    with open(args.bundle) as f:
        bundle = json.load(f)

    rounds = parse_rounds(args.rounds)
    diffs, working_hw, chain_hw = candidate_diffs(bundle, args.diff_source)
    if not diffs:
        print("No non-zero candidate diffs.", file=sys.stderr)
        sys.exit(1)

    baseline = simulate_bundle(bundle, n_samples=args.n_samples)
    rows = []
    for round_idx in rounds:
        for label, diff in diffs:
            result = run_variant(bundle, round_idx, diff, args.n_samples)
            rows.append({
                "round": round_idx,
                "diff_label": label,
                "diff": f"0x{diff:08x}",
                "verdict": result["verdict"],
                "min_target_distance": result.get("min_target_distance"),
                "median_target_distance": result.get("median_target_distance"),
                "max_target_distance": result.get("max_target_distance"),
                "min_final_hw": result.get("min_final_hw"),
                "median_final_hw": result.get("median_final_hw"),
                "max_final_hw": result.get("max_final_hw"),
                "n_target_matches": result.get("n_target_matches"),
                "n_near_residuals": result.get("n_near_residuals"),
                "error": result.get("synthesis_error")
                         or "; ".join(result.get("unsupported_constraints", [])),
            })

    rows.sort(key=lambda r: (
        r["median_target_distance"] is None,
        r["median_target_distance"] if r["median_target_distance"] is not None else 10**9,
        r["min_target_distance"] if r["min_target_distance"] is not None else 10**9,
    ))

    print("=== W2 exact_diff sweep ===")
    print(f"Bundle:          {args.bundle}")
    print(f"Rounds:          {args.rounds}")
    print(f"Diff source:     {args.diff_source} ({len(diffs)} non-zero unique words)")
    print(f"Samples/variant: {args.n_samples}")
    print(f"Block1 working residual HW: {working_hw}")
    print(f"Block2 chain-input diff HW: {chain_hw}")
    print(f"Baseline verdict: {baseline['verdict']}")
    print(f"Baseline target distance median: {baseline.get('median_target_distance')}")
    print()
    print("rank  round  diff_label  diff        verdict          minD  medD  minHW  medHW")
    for i, row in enumerate(rows[:args.top_k], 1):
        print(f"{i:>4}  {row['round']:>5}  {row['diff_label']:<10}  "
              f"{row['diff']}  {row['verdict']:<15}  "
              f"{str(row['min_target_distance']):>4}  "
              f"{str(row['median_target_distance']):>4}  "
              f"{str(row['min_final_hw']):>5}  {str(row['median_final_hw']):>5}")

    if args.out_json:
        with open(args.out_json, "w") as f:
            json.dump({
                "bundle": args.bundle,
                "rounds": rounds,
                "diff_source": args.diff_source,
                "n_samples": args.n_samples,
                "working_hw": working_hw,
                "chain_hw": chain_hw,
                "baseline": baseline,
                "rows": rows,
            }, f, indent=2)
        print(f"\nFull JSON: {args.out_json}", file=sys.stderr)


if __name__ == "__main__":
    main()
