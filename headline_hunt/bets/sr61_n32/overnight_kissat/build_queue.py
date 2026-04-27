#!/usr/bin/env python3
"""Build a kissat work queue from registry + cnfs_n32 + prior runs.

Strategy:
  Phase A: ALL distinguished cands × 5 seeds × 100M conflicts (broad)
  Phase B: ALL distinguished cands × 3 seeds × 1B conflicts (deep)
  Phase C: Other cnfs_n32 cands not yet hit at 100M+

Skip jobs already in runs.jsonl with same (candidate_id, seed, conflicts).

Output: work_queue.tsv with format
  STATUS<TAB>cnf_path<TAB>seed<TAB>conflicts<TAB>tag

Usage: python3 build_queue.py [--num-distinguished N] [--phase A|B|C|all]
"""
import argparse
import json
import os
import sys
import yaml

REPO = "/Users/mac/Desktop/sha256_review"

# F12+F17 distinguished cands (highest-priority).
DISTINGUISHED_PATHS = [
    "cnfs_n32/sr61_cascade_m17149975_fffffffff_bit31.cnf",       # verified sr=60
    "cnfs_n32/sr61_cascade_m189b13c7_f80000000_bit31.cnf",       # F12 HW=2 champ
    "cnfs_n32/sr61_n32_bit13_m4e560940_fillaaaaaaaa_enf0.cnf",   # F17 HW=47 champ
    "cnfs_n32/sr61_n32_bit17_m427c281d_fill80000000_enf0.cnf",   # F12 HW=3
    "cnfs_n32/sr61_cascade_m99bf552b_fffffffff_bit18.cnf",       # F12 HW=4
    "cnfs_n32/sr61_cascade_m33ec77ca_fffffffff_bit3.cnf",        # F17 HW=46
]

PHASE_A_SEEDS    = [11, 13, 17, 19, 23, 29, 31, 37]   # 8 seeds × 100M (broad)
PHASE_A_BUDGET   = 100_000_000                         # 100M conflicts
PHASE_B_SEEDS    = [41, 43, 47, 53, 59]                # 5 seeds × 1B (deep)
PHASE_B_BUDGET   = 1_000_000_000                       # 1B conflicts
PHASE_C_BUDGET   = 100_000_000                         # 100M for breadth on other cands
PHASE_D_SEEDS    = [61, 67, 71]                        # 3 seeds × 5B (very deep, top 2 cands only)
PHASE_D_BUDGET   = 5_000_000_000                       # 5B conflicts (will hit time cap)
PHASE_D_CANDS    = [
    "cnfs_n32/sr61_cascade_m17149975_fffffffff_bit31.cnf",     # verified sr=60 (deepest residual)
    "cnfs_n32/sr61_n32_bit13_m4e560940_fillaaaaaaaa_enf0.cnf", # F17 champion
]


def existing_runs_set(runs_jsonl):
    """Return set of (cnf_basename, seed, conflicts) already logged."""
    seen = set()
    if not os.path.exists(runs_jsonl):
        return seen
    with open(runs_jsonl) as f:
        for line in f:
            try:
                r = json.loads(line)
            except Exception:
                continue
            cnf = r.get("command", "")
            # extract basename
            for tok in cnf.split():
                if tok.endswith(".cnf"):
                    cnf_basename = os.path.basename(tok)
                    seen.add((cnf_basename, r.get("seed"), None))
                    break
    return seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["A", "B", "C", "all"], default="all")
    ap.add_argument("--out", default="work_queue.tsv")
    ap.add_argument("--max-jobs", type=int, default=None)
    args = ap.parse_args()

    runs_jsonl = os.path.join(REPO, "headline_hunt/registry/runs.jsonl")
    seen = existing_runs_set(runs_jsonl)
    print(f"# runs.jsonl has {len(seen)} prior (cnf, seed) entries", file=sys.stderr)

    jobs = []  # list of (cnf_path, seed, conflicts, tag)

    # Phase A: distinguished × 5 seeds × 100M
    if args.phase in ("A", "all"):
        for cnf_rel in DISTINGUISHED_PATHS:
            cnf_abs = os.path.join(REPO, cnf_rel)
            if not os.path.exists(cnf_abs):
                print(f"# missing: {cnf_rel}", file=sys.stderr)
                continue
            for seed in PHASE_A_SEEDS:
                tag = f"PhaseA_dist_100M_{os.path.basename(cnf_rel).replace('.cnf','')}"
                jobs.append((cnf_abs, seed, PHASE_A_BUDGET, tag))

    # Phase B: distinguished × 3 seeds × 1B
    if args.phase in ("B", "all"):
        for cnf_rel in DISTINGUISHED_PATHS:
            cnf_abs = os.path.join(REPO, cnf_rel)
            if not os.path.exists(cnf_abs):
                continue
            for seed in PHASE_B_SEEDS:
                tag = f"PhaseB_dist_1B_{os.path.basename(cnf_rel).replace('.cnf','')}"
                jobs.append((cnf_abs, seed, PHASE_B_BUDGET, tag))

    # Phase D: TOP 2 distinguished × 3 deep seeds × 5B (very deep)
    if args.phase in ("D", "all"):
        for cnf_rel in PHASE_D_CANDS:
            cnf_abs = os.path.join(REPO, cnf_rel)
            if not os.path.exists(cnf_abs):
                continue
            for seed in PHASE_D_SEEDS:
                tag = f"PhaseD_top_5B_{os.path.basename(cnf_rel).replace('.cnf','')}"
                jobs.append((cnf_abs, seed, PHASE_D_BUDGET, tag))

    # Phase C: other cnfs_n32 not yet at this budget — pick a representative subset
    if args.phase in ("C", "all"):
        cnf_dir = os.path.join(REPO, "cnfs_n32")
        all_cnfs = [os.path.join(cnf_dir, f) for f in sorted(os.listdir(cnf_dir))
                    if f.endswith(".cnf")]
        # exclude the distinguished ones already covered
        dist_set = {os.path.basename(p) for p in DISTINGUISHED_PATHS}
        for cnf_abs in all_cnfs:
            if os.path.basename(cnf_abs) in dist_set:
                continue
            # 1 seed × 100M for breadth
            tag = f"PhaseC_other_100M_{os.path.basename(cnf_abs).replace('.cnf','')}"
            jobs.append((cnf_abs, 11, PHASE_C_BUDGET, tag))

    if args.max_jobs:
        jobs = jobs[:args.max_jobs]

    with open(args.out, "w") as f:
        f.write("# status\tcnf_path\tseed\tconflicts\ttag\n")
        for cnf, seed, conf, tag in jobs:
            # status field padded to "PENDING" length (7) for in-place updates
            f.write(f"PENDING\t{cnf}\t{seed}\t{conf}\t{tag}\n")

    print(f"Wrote {args.out}: {len(jobs)} jobs", file=sys.stderr)
    print(f"  Phase A jobs: {sum(1 for j in jobs if 'PhaseA' in j[3])}", file=sys.stderr)
    print(f"  Phase B jobs: {sum(1 for j in jobs if 'PhaseB' in j[3])}", file=sys.stderr)
    print(f"  Phase C jobs: {sum(1 for j in jobs if 'PhaseC' in j[3])}", file=sys.stderr)
    print(f"  Phase D jobs: {sum(1 for j in jobs if 'PhaseD' in j[3])}", file=sys.stderr)


if __name__ == "__main__":
    main()
