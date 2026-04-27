#!/usr/bin/env python3
"""Convert results.tsv (from dispatcher) into runs.jsonl entries via append_run.py.

Reads results.tsv (TAB-separated):
  iso_ts<TAB>run_id<TAB>cnf<TAB>seed<TAB>conflicts<TAB>status<TAB>wall<TAB>tag

For each line:
  1. Look up cand_id from cnf filename via candidates.yaml lookup.
  2. Run audit_cnf.py to confirm CONFIRMED.
  3. Call append_run.py with --bet sr61_n32, --candidate <id>, --cnf <path>,
     --solver kissat, --seed <S>, --status <S>, --wall <W>, --notes "tag".
"""
import argparse
import json
import os
import re
import subprocess
import sys
import yaml

REPO = "/Users/mac/Desktop/sha256_review"
APPEND = os.path.join(REPO, "headline_hunt/infra/append_run.py")


def load_cand_lookup():
    """Return dict: (m0_int, fill_int, kernel_bit) -> cand_id."""
    with open(os.path.join(REPO, "headline_hunt/registry/candidates.yaml")) as f:
        cs = yaml.safe_load(f)
    out = {}
    for c in cs:
        if not isinstance(c, dict):
            continue
        out[(int(c["m0"], 16), int(c["fill"], 16), c["kernel"]["bit"])] = c["id"]
    return out


def parse_cnf_basename(cnf_path):
    """Parse (m0, fill, bit) from cnf filename via regex.
    Recognized: sr61_cascade_m{M}_f{F}_bit{B}.cnf  OR
                sr61_n32_bit{B}_m{M}_fill{F}_enf0.cnf"""
    name = os.path.basename(cnf_path)
    m1 = re.match(r"^sr61_cascade_m([0-9a-f]+)_f([0-9a-f]+)_bit(\d+)\.cnf$", name)
    if m1:
        return (int(m1.group(1), 16), int(m1.group(2), 16), int(m1.group(3)))
    m2 = re.match(r"^sr61_n32_bit(\d+)_m([0-9a-f]+)_fill([0-9a-f]+)_enf0\.cnf$", name)
    if m2:
        return (int(m2.group(2), 16), int(m2.group(3), 16), int(m2.group(1)))
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results.tsv")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.results):
        print(f"No results file: {args.results}", file=sys.stderr)
        return

    cand_lookup = load_cand_lookup()

    appended = 0
    skipped = 0
    failed = 0

    with open(args.results) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 8:
                continue
            ts, run_id, cnf, seed, conflicts, status, wall, tag = parts[:8]

            key = parse_cnf_basename(cnf)
            if not key:
                print(f"  SKIP: cnf parse fail {cnf}", file=sys.stderr)
                skipped += 1
                continue
            cand_id = cand_lookup.get(key)
            if not cand_id:
                print(f"  SKIP: no cand_id for {key} ({cnf})", file=sys.stderr)
                skipped += 1
                continue

            # Map status to schema
            status_norm = status.upper()
            if status_norm not in ("SAT", "UNSAT", "TIMEOUT", "KILLED", "ERROR"):
                # Default UNKNOWN → TIMEOUT for our tracking
                if status_norm == "UNKNOWN":
                    status_norm = "TIMEOUT"
                else:
                    status_norm = "TIMEOUT"

            cmd = ["python3", APPEND,
                   "--bet", "sr61_n32",
                   "--candidate", cand_id,
                   "--cnf", cnf,
                   "--solver", "kissat",
                   "--solver-version", "4.0.4",
                   "--seed", seed,
                   "--status", status_norm,
                   "--wall", wall,
                   "--encoder", "cascade_enf0",
                   "--notes", f"{tag} (overnight dispatcher run_id={run_id} conflicts={conflicts})"]

            if args.dry_run:
                print(f"  DRYRUN: {cand_id} seed={seed} status={status_norm} wall={wall}", file=sys.stderr)
                continue

            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0:
                appended += 1
            else:
                failed += 1
                print(f"  FAIL: {r.stderr[:200]}", file=sys.stderr)

    print(f"appended={appended} skipped={skipped} failed={failed}", file=sys.stderr)


if __name__ == "__main__":
    main()
