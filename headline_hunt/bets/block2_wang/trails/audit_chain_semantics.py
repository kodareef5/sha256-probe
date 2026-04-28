#!/usr/bin/env python3
"""
audit_chain_semantics.py - report block-1 working residual vs block-2 chain input.

For each 2blockcertpin/v1 trail bundle, reconstruct block 1 and print:
- whether block1.residual_state_diff matches the simulated round-63
  working-state diff
- the HW of that working-state diff
- the HW of the post-feed-forward chaining-output diff that actually
  becomes block 2's input IV diff

Usage:
    python3 audit_chain_semantics.py sample_trail_bundles/*.json
    python3 audit_chain_semantics.py --jsonl sample_trail_bundles/
"""
import argparse
import json
import os
import sys


REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)

from headline_hunt.bets.block2_wang.encoders.simulate_2block_absorption import (
    REGS,
    hex_tuple,
    hw_tuple,
    reconstruct_block1,
    xor_tuple,
)


def iter_bundle_paths(paths):
    for path in paths:
        if os.path.isdir(path):
            for root, _, files in os.walk(path):
                for name in sorted(files):
                    if name.endswith(".json"):
                        yield os.path.join(root, name)
        else:
            yield path


def audit_bundle(path):
    with open(path) as f:
        bundle = json.load(f)

    b1 = bundle["block1"]
    state1_63, state2_63, chain1_out, chain2_out = reconstruct_block1(b1)
    working_diff = xor_tuple(state1_63, state2_63)
    chain_diff = xor_tuple(chain1_out, chain2_out)
    claimed = tuple(int(b1.get("residual_state_diff", {}).get(f"d{r}63", "0x0"), 16)
                    for r in REGS)

    working_hw = hw_tuple(working_diff)
    chain_hw = hw_tuple(chain_diff)
    return {
        "path": path,
        "cand_id": bundle.get("cand_id", "?"),
        "witness_id": bundle.get("witness_id", "?"),
        "claimed_matches_working_state": claimed == working_diff,
        "working_state_hw": working_hw,
        "chain_input_hw": chain_hw,
        "chain_minus_working_hw": chain_hw - working_hw,
        "working_state_diff": hex_tuple(working_diff),
        "chain_input_diff": hex_tuple(chain_diff),
    }


def print_table(rows):
    print("status  workingHW  chainHW  delta  witness")
    for row in rows:
        status = "OK" if row["claimed_matches_working_state"] else "BAD"
        print(f"{status:<6}  {row['working_state_hw']:>9}  "
              f"{row['chain_input_hw']:>7}  "
              f"{row['chain_minus_working_hw']:>5}  "
              f"{row['witness_id']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("paths", nargs="+",
                    help="Trail bundle JSON files or directories to scan")
    ap.add_argument("--jsonl", action="store_true",
                    help="Emit one JSON object per bundle")
    ap.add_argument("--fail-on-mismatch", action="store_true",
                    help="Exit 1 if any claimed residual does not match simulation")
    args = ap.parse_args()

    rows = []
    for path in iter_bundle_paths(args.paths):
        try:
            rows.append(audit_bundle(path))
        except (KeyError, json.JSONDecodeError, OSError, ValueError) as exc:
            print(f"ERROR {path}: {exc}", file=sys.stderr)
            if args.fail_on_mismatch:
                sys.exit(1)

    if args.jsonl:
        for row in rows:
            print(json.dumps(row, sort_keys=True))
    else:
        print_table(rows)

    if args.fail_on_mismatch and any(not r["claimed_matches_working_state"]
                                     for r in rows):
        sys.exit(1)


if __name__ == "__main__":
    main()
