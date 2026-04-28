#!/usr/bin/env python3
"""
beam_w2_exactdiff.py - search small multi-round W2 exact_diff sequences.

This builds on sweep_w2_exactdiff.py. It keeps the same deliberately small
constraint vocabulary - one or more `exact_diff` pins using candidate words
derived from the block-1 residual - and asks whether combining simple pins
beats the best one-shot probe.

The simulator currently supports W2 exact/exact_diff rounds 0..24. Keep
beam widths modest: this is a design probe, not a solver.
Small sample counts are noisy; validate any promising sequence with a
larger `simulate_2block_absorption.py --n-samples` run.

Usage:
    python3 beam_w2_exactdiff.py bit3_HW55_naive_blocktwo.json
    python3 beam_w2_exactdiff.py bundle.json --depth 3 --beam-width 12
"""
import argparse
import copy
import json
import os
import sys


REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)

from headline_hunt.bets.block2_wang.encoders.simulate_2block_absorption import (
    simulate_bundle,
)
from headline_hunt.bets.block2_wang.encoders.sweep_w2_exactdiff import (
    candidate_diffs,
    parse_rounds,
)


def make_candidates(bundle, rounds, diff_source):
    diffs, working_hw, chain_hw = candidate_diffs(bundle, diff_source)
    candidates = []
    for round_idx in rounds:
        for label, diff in diffs:
            candidates.append({
                "round": round_idx,
                "type": "exact_diff",
                "diff": f"0x{diff:08x}",
                "_label": label,
                "_key": (round_idx, diff),
            })
    return candidates, working_hw, chain_hw


def public_constraints(items):
    return [
        {"round": c["round"], "type": c["type"], "diff": c["diff"]}
        for c in sorted(items, key=lambda x: (x["round"], x["diff"]))
    ]


def labels(items):
    return [
        f"r{c['round']}:{c['_label']}={c['diff']}"
        for c in sorted(items, key=lambda x: (x["round"], x["diff"]))
    ]


def run_constraints(bundle, items, n_samples):
    variant = copy.deepcopy(bundle)
    variant["block2"]["W2_constraints"] = public_constraints(items)
    result = simulate_bundle(variant, n_samples=n_samples)
    result["constraints"] = public_constraints(items)
    result["labels"] = labels(items)
    return result


def score(result):
    if result["verdict"] in {"UNSUPPORTED_CONSTRAINTS", "CONSTRAINT_SYNTHESIS_FAILED"}:
        return (1, 10**9, 10**9, 10**9)
    return (
        0,
        result.get("median_target_distance", 10**9),
        result.get("min_target_distance", 10**9),
        result.get("median_final_hw", 10**9),
    )


def print_state(rank, result):
    labels_s = ", ".join(result["labels"]) if result.get("labels") else "(none)"
    print(f"{rank:>3}  {result['verdict']:<27} "
          f"minD={str(result.get('min_target_distance')):>4} "
          f"medD={str(result.get('median_target_distance')):>4} "
          f"minHW={str(result.get('min_final_hw')):>4} "
          f"medHW={str(result.get('median_final_hw')):>4}  "
          f"{labels_s}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bundle", help="2blockcertpin/v1 trail bundle JSON")
    ap.add_argument("--rounds", default="0-24")
    ap.add_argument("--diff-source", choices=["chain", "working", "both"],
                    default="chain")
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--beam-width", type=int, default=12)
    ap.add_argument("--n-samples", type=int, default=10)
    ap.add_argument("--top-k", type=int, default=10)
    ap.add_argument("--out-json", default=None)
    args = ap.parse_args()

    with open(args.bundle) as f:
        bundle = json.load(f)

    rounds = parse_rounds(args.rounds)
    candidates, working_hw, chain_hw = make_candidates(bundle, rounds, args.diff_source)
    baseline = simulate_bundle(bundle, n_samples=args.n_samples)
    baseline["constraints"] = []
    baseline["labels"] = []

    print("=== W2 exact_diff beam search ===")
    print(f"Bundle:          {args.bundle}")
    print(f"Rounds:          {args.rounds}")
    print(f"Diff source:     {args.diff_source}")
    print(f"Candidate pins:  {len(candidates)}")
    print(f"Depth:           {args.depth}")
    print(f"Beam width:      {args.beam_width}")
    print(f"Samples/state:   {args.n_samples}")
    print(f"Block1 working residual HW: {working_hw}")
    print(f"Block2 chain-input diff HW: {chain_hw}")
    print()
    print("Baseline:")
    print_state(0, baseline)

    beam = [((), baseline)]
    all_results = [baseline]
    seen = {()}

    for depth in range(1, args.depth + 1):
        expanded = []
        failures = 0
        for keys, _ in beam:
            used_rounds = {k[0] for k in keys}
            current_items = [
                c for c in candidates if c["_key"] in keys
            ]
            for cand in candidates:
                if cand["round"] in used_rounds:
                    continue
                new_keys = tuple(sorted(keys + (cand["_key"],)))
                if new_keys in seen:
                    continue
                seen.add(new_keys)
                items = current_items + [cand]
                result = run_constraints(bundle, items, args.n_samples)
                if result["verdict"] in {
                    "UNSUPPORTED_CONSTRAINTS", "CONSTRAINT_SYNTHESIS_FAILED"
                }:
                    failures += 1
                expanded.append((new_keys, result))
                all_results.append(result)

        expanded.sort(key=lambda kr: score(kr[1]))
        beam = expanded[:args.beam_width]
        print()
        print(f"Depth {depth}: expanded={len(expanded)} failures={failures}")
        for i, (_, result) in enumerate(beam[:args.top_k], 1):
            print_state(i, result)

    all_results.sort(key=score)

    if args.out_json:
        with open(args.out_json, "w") as f:
            json.dump({
                "bundle": args.bundle,
                "rounds": rounds,
                "diff_source": args.diff_source,
                "depth": args.depth,
                "beam_width": args.beam_width,
                "n_samples": args.n_samples,
                "working_hw": working_hw,
                "chain_hw": chain_hw,
                "best": all_results[:args.top_k],
            }, f, indent=2)
        print(f"\nFull JSON: {args.out_json}", file=sys.stderr)


if __name__ == "__main__":
    main()
