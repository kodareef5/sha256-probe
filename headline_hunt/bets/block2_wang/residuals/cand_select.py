#!/usr/bin/env python3
"""
cand_select.py — Multi-metric candidate ranking from enriched corpus.

Reads F28_deep_corpus_enriched.jsonl and ranks the 67 cands by a
weighted combination of structural metrics:
- HW (residual size at deep min)
- LM cost (cascade-1 carry constraint count, F35/F36)
- Exact-symmetry (a_61 == e_61)

Usage:
  python3 cand_select.py [--weight-hw W_HW] [--weight-lm W_LM]
                          [--require-symmetry] [--top N]

Default: equal weights, list top 10. Lower combined score = better.

Examples:
  # F28-style ranking (HW only)
  python3 cand_select.py --weight-hw 1.0 --weight-lm 0.0

  # F36-style ranking (LM only)
  python3 cand_select.py --weight-hw 0.0 --weight-lm 1.0

  # Combined (HW + LM/100)
  python3 cand_select.py --weight-hw 1.0 --weight-lm 0.01
"""
import argparse
import json
import os
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CORPUS = os.path.join(HERE, "F28_deep_corpus_enriched.jsonl")


def load_min_per_cand(corpus_path):
    """Load enriched corpus, return per-cand min-HW record (with LM fields)."""
    min_per_cand = {}
    with open(corpus_path) as f:
        for line in f:
            r = json.loads(line)
            cid = r["candidate_id"]
            if cid not in min_per_cand or r["hw_total"] < min_per_cand[cid]["hw_total"]:
                min_per_cand[cid] = r
    return min_per_cand


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpus", default=DEFAULT_CORPUS,
                    help=f"Path to enriched corpus (default: {DEFAULT_CORPUS})")
    ap.add_argument("--weight-hw", type=float, default=1.0,
                    help="Weight on HW (default: 1.0)")
    ap.add_argument("--weight-lm", type=float, default=0.01,
                    help="Weight on LM cost (default: 0.01, since LM ~10x larger)")
    ap.add_argument("--require-symmetry", action="store_true",
                    help="Filter to a_61 == e_61 cands only")
    ap.add_argument("--top", type=int, default=10,
                    help="How many top cands to show (default: 10)")
    ap.add_argument("--format", choices=["text", "yaml", "jsonl"], default="text",
                    help="Output format")
    args = ap.parse_args()

    if not os.path.exists(args.corpus):
        print(f"ERROR: corpus not found: {args.corpus}", file=sys.stderr)
        sys.exit(1)

    min_per_cand = load_min_per_cand(args.corpus)

    cands = []
    for cid, rec in min_per_cand.items():
        if "cand_min_lm_cost" not in rec:
            continue  # skip records without LM data
        if args.require_symmetry and not rec.get("a61_eq_e61", False):
            continue
        score = args.weight_hw * rec["hw_total"] + args.weight_lm * rec["cand_min_lm_cost"]
        cands.append({
            "candidate_id": cid,
            "hw": rec["hw_total"],
            "lm_cost": rec["cand_min_lm_cost"],
            "active_adders": rec.get("cand_min_active_adders"),
            "lm_incompat": rec.get("cand_min_lm_incompat"),
            "a61_eq_e61": rec.get("a61_eq_e61", False),
            "a61": rec.get("a61"),
            "e61": rec.get("e61"),
            "w_witness": [rec["w_57"], rec["w_58"], rec["w_59"], rec["w_60"]],
            "score": score,
        })

    cands.sort(key=lambda x: x["score"])
    cands = cands[: args.top]

    if args.format == "text":
        print(f"Top {len(cands)} cands by score = {args.weight_hw}*HW + {args.weight_lm}*LM"
              + (" (symmetry-only)" if args.require_symmetry else ""))
        print(f"{'rank':>4} {'cand':<48} {'HW':>3} {'LM':>4} {'sym':>4} {'score':>8}")
        print("-" * 78)
        for i, c in enumerate(cands, 1):
            cid_short = c["candidate_id"].replace("cand_n32_", "")
            sym_marker = "EXACT" if c["a61_eq_e61"] else " no"
            print(f"{i:>4} {cid_short:<48} {c['hw']:>3} {c['lm_cost']:>4} {sym_marker:>4} {c['score']:>8.2f}")
    elif args.format == "yaml":
        try:
            import yaml
            print(yaml.safe_dump(cands, sort_keys=False))
        except ImportError:
            print("PyYAML not installed; falling back to JSON", file=sys.stderr)
            print(json.dumps(cands, indent=2))
    elif args.format == "jsonl":
        for c in cands:
            print(json.dumps(c))


if __name__ == "__main__":
    main()
