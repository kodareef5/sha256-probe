#!/usr/bin/env python3
"""Record-wise LM/HW Pareto scan over the F28/F42 corpus.

F35/F36 ranked candidates by the LM cost of each candidate's minimum-HW
record. F42 computed LM cost for all 3,065 records. This joins the full
F28 witness corpus with the F42 LM table and exposes the Pareto surface
directly: low residual HW, low LM cost, and optional a61=e61 symmetry.

Usage:
  python3 scan_record_lm.py --top 20
  python3 scan_record_lm.py --format jsonl --emit pareto
"""
import argparse
import json
import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CORPUS = os.path.join(
    HERE, "..", "residuals", "F28_deep_corpus_enriched.jsonl"
)
DEFAULT_LM = os.path.join(HERE, "F36_extended_all_records_lm_compat.jsonl")


def record_key(rec):
    return (rec["candidate_id"], int(rec["hw_total"]), int(rec["hw_idx"]))


def load_lm(path):
    out = {}
    with open(path) as f:
        for line in f:
            rec = json.loads(line)
            out[record_key(rec)] = rec
    return out


def load_records(corpus_path, lm_path):
    lm_by_key = load_lm(lm_path)
    records = []
    missing = 0
    with open(corpus_path) as f:
        for line in f:
            rec = json.loads(line)
            lm = lm_by_key.get(record_key(rec))
            if lm is None:
                missing += 1
                continue
            out = {
                "candidate_id": rec["candidate_id"],
                "m0": rec["m0"],
                "fill": rec["fill"],
                "kernel_bit": rec["kernel_bit"],
                "hw_total": rec["hw_total"],
                "hw_idx": rec["hw_idx"],
                "a61_eq_e61": rec.get("a61_eq_e61", False),
                "a61": rec.get("a61"),
                "e61": rec.get("e61"),
                "w_witness": [rec["w_57"], rec["w_58"], rec["w_59"], rec["w_60"]],
                "diff63": rec.get("diff63"),
                "lm_cost": lm["lm_cost"],
                "lm_incompat": lm["incompat"],
            }
            records.append(out)
    if missing:
        print(f"WARNING: skipped {missing} records missing LM data", file=sys.stderr)
    return records


def pareto_front(records):
    """Return records not dominated on (HW, LM), both minimized."""
    ordered = sorted(records, key=lambda r: (r["hw_total"], r["lm_cost"]))
    front = []
    best_lm = None
    for rec in ordered:
        if best_lm is None or rec["lm_cost"] < best_lm:
            front.append(rec)
            best_lm = rec["lm_cost"]
    return front


def best_by_candidate(records):
    best = {}
    for rec in records:
        old = best.get(rec["candidate_id"])
        if old is None or (rec["lm_cost"], rec["hw_total"]) < (
            old["lm_cost"],
            old["hw_total"],
        ):
            best[rec["candidate_id"]] = rec
    return sorted(best.values(), key=lambda r: (r["lm_cost"], r["hw_total"]))


def short_cand(rec):
    return rec["candidate_id"].replace("cand_n32_", "")


def print_table(title, records, top):
    print(f"\n{title}:")
    print(f"{'rank':>4} {'LM':>4} {'HW':>3} {'sym':>5} {'candidate':<44} W")
    print("-" * 96)
    for i, rec in enumerate(records[:top], 1):
        sym = "yes" if rec["a61_eq_e61"] else "no"
        print(
            f"{i:>4} {rec['lm_cost']:>4} {rec['hw_total']:>3} {sym:>5} "
            f"{short_cand(rec):<44} " + " ".join(rec["w_witness"])
        )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--corpus", default=DEFAULT_CORPUS)
    ap.add_argument("--lm-data", default=DEFAULT_LM)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument(
        "--emit",
        choices=["all", "pareto", "top-lm", "cand-best", "sym"],
        default="all",
    )
    ap.add_argument("--format", choices=["text", "jsonl"], default="text")
    args = ap.parse_args()

    if not os.path.exists(args.corpus):
        print(f"ERROR: corpus not found: {args.corpus}", file=sys.stderr)
        return 2
    if not os.path.exists(args.lm_data):
        print(f"ERROR: LM data not found: {args.lm_data}", file=sys.stderr)
        return 2

    records = load_records(args.corpus, args.lm_data)
    top_records = sorted(records, key=lambda r: (r["lm_cost"], r["hw_total"]))
    top_cands = best_by_candidate(records)
    front = pareto_front(records)
    sym_records = sorted(
        [r for r in records if r["a61_eq_e61"]],
        key=lambda r: (r["lm_cost"], r["hw_total"]),
    )

    buckets = {
        "pareto": front,
        "top-lm": top_records,
        "cand-best": top_cands,
        "sym": sym_records,
    }

    if args.format == "jsonl":
        emit_names = buckets.keys() if args.emit == "all" else [args.emit]
        for name in emit_names:
            for rec in buckets[name][: args.top]:
                print(json.dumps({"kind": name, **rec}))
        return 0

    print(f"Scanned {len(records)} records from {args.corpus}")
    print(f"Global Pareto points on (HW, LM): {len(front)}")
    print(f"Exact a61=e61 records: {len(sym_records)}")

    if args.emit in ("all", "pareto"):
        print_table("Global Pareto frontier (minimize HW and LM)", front, args.top)
    if args.emit in ("all", "top-lm"):
        print_table("Top records by LM", top_records, args.top)
    if args.emit in ("all", "cand-best"):
        print_table("Top candidate-best records by LM", top_cands, args.top)
    if args.emit in ("all", "sym"):
        print_table("Top exact a61=e61 records by LM", sym_records, args.top)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
