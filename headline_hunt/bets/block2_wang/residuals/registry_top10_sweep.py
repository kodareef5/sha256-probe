#!/usr/bin/env python3
"""
registry_top10_sweep.py — F100 sweep tool.

For each candidate in headline_hunt/registry/candidates.yaml, build
a 200k-sample residual corpus to /tmp, extract top-10 lowest-HW
W-witnesses, run certpin_verify --solver all, and record per-cand
results in a single summary JSON.

Skips cands already covered by F94/F95/F96/F98/F99 (passed via
--skip-list).

Usage:
    python3 registry_top10_sweep.py \
        --skip-list "m17149975,ma22dc6c7,m9cfea9ce,m189b13c7,m4e560940,..." \
        --out registry_top10_sweep_summary.json
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
import yaml


HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
BUILD_CORPUS = os.path.join(HERE, "build_corpus.py")
CERTPIN = os.path.join(REPO, "headline_hunt", "bets",
                        "cascade_aux_encoding", "encoders", "certpin_verify.py")


def sweep_one(cand, out_corpus_path):
    """Build corpus + run cert-pin for one cand. Returns dict of per-witness results."""
    m0 = cand["m0"]
    fill = cand["fill"]
    kbit = cand["kernel"]["bit"]

    # Build 200k corpus
    t0 = time.time()
    r = subprocess.run([
        "python3", BUILD_CORPUS,
        "--m0", m0, "--fill", fill, "--kernel-bit", str(kbit),
        "--samples", "200000", "--hw-threshold", "80", "--seed", "42",
        "--w1-60", "0xb6befe82",
        "--out", out_corpus_path,
    ], capture_output=True, text=True)
    build_wall = time.time() - t0
    if r.returncode != 0:
        return {"cand_id": cand["id"], "status": "BUILD_FAILED",
                "error": r.stderr[:300]}

    # Extract top-10
    records = [json.loads(l) for l in open(out_corpus_path)]
    if not records:
        return {"cand_id": cand["id"], "status": "EMPTY_CORPUS",
                "build_wall": build_wall}
    records.sort(key=lambda r: r["hw_total"])
    top10 = records[:10]

    # Build batch JSONL
    batch_path = out_corpus_path.replace(".jsonl", "_top10.jsonl")
    with open(batch_path, "w") as f:
        for i, rec in enumerate(top10):
            f.write(json.dumps({
                "cand_id": f"{cand['id']}_topHW{rec['hw_total']}_idx{i}",
                "m0": m0, "fill": fill, "kernel_bit": kbit,
                "w57": rec["w1_57"], "w58": rec["w1_58"],
                "w59": rec["w1_59"], "w60": rec["w1_60"],
                "hw": rec["hw_total"],
            }) + "\n")

    # Run cert-pin --solver all
    t0 = time.time()
    cp = subprocess.run([
        "python3", CERTPIN, "--batch", batch_path, "--solver", "all",
    ], capture_output=True, text=True)
    cp_wall = time.time() - t0

    # Parse output for verdicts
    verdicts = []
    sat_count = 0
    unsat_count = 0
    for line in cp.stdout.split("\n"):
        if "UNSAT" in line and "near-residual" in line:
            unsat_count += 1
            verdicts.append("UNSAT")
        elif "SAT" in line and "verified collision" in line:
            sat_count += 1
            verdicts.append("SAT")
        elif "MIXED" in line:
            verdicts.append("MIXED")

    return {
        "cand_id": cand["id"],
        "m0": m0, "fill": fill, "kernel_bit": kbit,
        "n_records_corpus": len(records),
        "min_hw": records[0]["hw_total"],
        "top10_hws": [r["hw_total"] for r in top10],
        "sat_count": sat_count,
        "unsat_count": unsat_count,
        "verdicts": verdicts,
        "build_wall_s": round(build_wall, 2),
        "certpin_wall_s": round(cp_wall, 2),
        "status": "OK",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-list", default="",
                    help="Comma-separated m0 substrings to skip (already audited)")
    ap.add_argument("--out", required=True, help="Summary JSON output path")
    ap.add_argument("--limit", type=int, default=None,
                    help="Max number of cands to process (debug)")
    args = ap.parse_args()

    skip = [s.strip() for s in args.skip_list.split(",") if s.strip()]
    cands_file = os.path.join(REPO, "headline_hunt/registry/candidates.yaml")
    cands = yaml.safe_load(open(cands_file))

    remaining = [c for c in cands if not any(s in c["id"] for s in skip)]
    if args.limit:
        remaining = remaining[:args.limit]
    print(f"Processing {len(remaining)} cands (skipping {len(cands) - len(remaining)} done)",
          file=sys.stderr)

    results = []
    t_global = time.time()
    with tempfile.TemporaryDirectory() as tmpdir:
        for i, cand in enumerate(remaining):
            t0 = time.time()
            corpus_path = os.path.join(tmpdir, f"corpus_{cand['id']}.jsonl")
            r = sweep_one(cand, corpus_path)
            results.append(r)
            wall = time.time() - t0
            sat = r.get("sat_count", "?")
            unsat = r.get("unsat_count", "?")
            print(f"  [{i+1:>2}/{len(remaining)}] {cand['id']:<55}  "
                  f"SAT={sat} UNSAT={unsat}  ({wall:.1f}s)",
                  file=sys.stderr)

    total_wall = time.time() - t_global
    total_sat = sum(r.get("sat_count", 0) for r in results)
    total_unsat = sum(r.get("unsat_count", 0) for r in results)
    summary = {
        "n_cands_processed": len(results),
        "total_sat": total_sat,
        "total_unsat": total_unsat,
        "total_wall_seconds": round(total_wall, 1),
        "results": results,
    }
    with open(args.out, "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n=== SWEEP SUMMARY ===", file=sys.stderr)
    print(f"  Cands processed: {len(results)}", file=sys.stderr)
    print(f"  Total SAT:    {total_sat}", file=sys.stderr)
    print(f"  Total UNSAT:  {total_unsat}", file=sys.stderr)
    print(f"  Total wall:   {round(total_wall, 1)}s", file=sys.stderr)
    print(f"  Output:       {args.out}", file=sys.stderr)
    if total_sat > 0:
        print(f"\n*** HEADLINE-CLASS DISCOVERY: {total_sat} SAT result(s) ***",
              file=sys.stderr)


if __name__ == "__main__":
    main()
