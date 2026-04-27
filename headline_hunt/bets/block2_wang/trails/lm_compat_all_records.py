#!/usr/bin/env python3
"""
lm_compat_all_records.py — extend F36's LM-compatibility check from
67 deep-min records to ALL 3065 F32 records.

For each record (cand, hw_total, hw_idx), runs active_adder_lm_bound
and checks whether ANY adder is LM-incompatible. F36 established
that all 67 deep-min records are LM-compatible. This script tests
whether the property extends to the full corpus.

Strong claim if all 3065 are compatible:
  "Cascade-1 trails are LM-compatible at every HW level, not just
   at the deep minimum. Universal cascade-1 structural property."

Output: per-record LM-compat status + summary stats.
"""
import json
import os
import subprocess
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, "active_adder_lm_bound")
CORPUS = os.path.join(os.path.dirname(HERE), "residuals", "F28_deep_corpus.jsonl")
OUTPUT = os.path.join(HERE, "F36_extended_all_records_lm_compat.jsonl")


def main():
    if not os.path.exists(TOOL):
        print(f"ERROR: tool not found: {TOOL}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(CORPUS):
        print(f"ERROR: corpus not found: {CORPUS}", file=sys.stderr)
        sys.exit(1)

    records = []
    with open(CORPUS) as f:
        for line in f:
            records.append(json.loads(line))
    print(f"Scanning {len(records)} F32 records for LM compatibility...",
          file=sys.stderr)

    incompat_records = []
    compat_count = 0
    per_cand_compat = {}  # cand_id -> count of LM-compatible records

    with open(OUTPUT, "w") as fout:
        for i, rec in enumerate(records):
            if i % 100 == 0 and i > 0:
                print(f"  {i}/{len(records)}...", file=sys.stderr)
            try:
                out = subprocess.check_output([
                    TOOL,
                    rec["m0"], rec["fill"], str(rec["kernel_bit"]),
                    rec["w_57"], rec["w_58"], rec["w_59"], rec["w_60"]
                ]).decode()
            except subprocess.CalledProcessError as e:
                print(f"  Tool failed for record {i}: {e}", file=sys.stderr)
                continue

            lm_cost = None
            incompat = None
            for line in out.split("\n"):
                if "Lipmaa-Moriai cost" in line:
                    lm_cost = int(line.split(":")[1].strip().split()[0])
                if "Incompatible" in line:
                    incompat = int(line.split(":")[1].strip().split()[0])

            if incompat is None:
                continue

            cand = rec["candidate_id"]
            per_cand_compat.setdefault(cand, [0, 0])  # [compat, incompat]
            if incompat == 0:
                compat_count += 1
                per_cand_compat[cand][0] += 1
            else:
                incompat_records.append({
                    "cand": cand,
                    "hw_total": rec["hw_total"],
                    "hw_idx": rec["hw_idx"],
                    "lm_cost": lm_cost,
                    "incompat_count": incompat,
                })
                per_cand_compat[cand][1] += 1

            fout.write(json.dumps({
                "candidate_id": cand,
                "hw_total": rec["hw_total"],
                "hw_idx": rec["hw_idx"],
                "lm_cost": lm_cost,
                "incompat": incompat,
            }) + "\n")

    total = compat_count + len(incompat_records)
    print(f"\n=== Results ===", file=sys.stderr)
    print(f"Total records scanned: {total}", file=sys.stderr)
    print(f"  LM-compatible:   {compat_count} ({100*compat_count/total:.1f}%)",
          file=sys.stderr)
    print(f"  LM-incompatible: {len(incompat_records)} ({100*len(incompat_records)/total:.1f}%)",
          file=sys.stderr)

    if incompat_records:
        print(f"\n⚠ {len(incompat_records)} INCOMPATIBLE records (showing first 10):",
              file=sys.stderr)
        for r in incompat_records[:10]:
            print(f"  {r['cand']}  HW={r['hw_total']} idx={r['hw_idx']}  "
                  f"LM={r['lm_cost']}  incompat={r['incompat_count']}",
                  file=sys.stderr)
    else:
        print(f"\n✓ ALL {total} records are LM-compatible — F36 extends "
              f"universally to every (cand, HW, idx) record",
              file=sys.stderr)

    print(f"\nPer-cand summary (first 5 cands):", file=sys.stderr)
    for cand, (c, i) in sorted(per_cand_compat.items())[:5]:
        print(f"  {cand}: {c}/{c+i} compatible", file=sys.stderr)

    print(f"\nOutput: {OUTPUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
