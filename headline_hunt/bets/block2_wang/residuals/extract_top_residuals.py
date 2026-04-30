#!/usr/bin/env python3
"""
extract_top_residuals.py — emit per-candidate top-K lowest-HW residuals
with FULL W-witness vectors, ready for downstream trail-search input.

The existing F100_registry_top10_sweep.json reports top10 HWs per cand but
omits the W-witnesses that produced them. This tool fills that gap by
walking `by_candidate/corpus_*.jsonl` and emitting per-cand top-K records
including w1_{57..60}, w2_{57..60}, iv1_63, iv2_63, hw63, etc.

Usage:
    # All cands, top-3 lowest-HW each
    python3 extract_top_residuals.py --top-k 3

    # One cand, top-10
    python3 extract_top_residuals.py --cand bit06_m6781a62a_fillaaaaaaaa --top-k 10

    # Below an HW ceiling, no per-cand limit
    python3 extract_top_residuals.py --hw-max 70

    # Output JSON file (default: stdout)
    python3 extract_top_residuals.py --top-k 3 --out /tmp/top3.json
"""
import argparse
import glob
import heapq
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BY_CAND_DIR = os.path.join(HERE, "by_candidate")


def cand_id_from_corpus_name(name):
    """corpus_bit06_m6781a62a_fillaaaaaaaa.jsonl → bit06_m6781a62a_fillaaaaaaaa"""
    base = os.path.basename(name)
    if base.startswith("corpus_") and base.endswith(".jsonl"):
        return base[len("corpus_"):-len(".jsonl")]
    return base


def iter_corpus(path):
    """Yield records from a JSONL corpus, skipping malformed lines."""
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def extract_one_corpus(path, top_k=None, hw_max=None):
    """Return list of records sorted ascending by hw_total."""
    if top_k is not None and hw_max is None:
        # heap of size top_k
        heap = []  # max-heap via negated hw
        for rec in iter_corpus(path):
            hw = rec.get("hw_total")
            if hw is None:
                continue
            if len(heap) < top_k:
                heapq.heappush(heap, (-hw, len(heap), rec))
            elif -heap[0][0] > hw:
                heapq.heapreplace(heap, (-hw, len(heap), rec))
        return sorted([r for (_, _, r) in heap], key=lambda r: r["hw_total"])
    else:
        # gather everything matching threshold, then sort/truncate
        out = []
        for rec in iter_corpus(path):
            hw = rec.get("hw_total")
            if hw is None:
                continue
            if hw_max is not None and hw > hw_max:
                continue
            out.append(rec)
        out.sort(key=lambda r: r["hw_total"])
        if top_k is not None:
            out = out[:top_k]
        return out


def main():
    ap = argparse.ArgumentParser(
        description=__doc__.strip(),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    ap.add_argument("--cand", help="cand suffix (e.g. bit06_m6781a62a_fillaaaaaaaa); default = all cands found")
    ap.add_argument("--top-k", type=int, default=3, help="per-cand top K (default 3)")
    ap.add_argument("--hw-max", type=int, default=None, help="filter records with hw_total ≤ this; if set, --top-k is the cap after filtering")
    ap.add_argument("--out", default=None, help="output JSON path (default stdout)")
    ap.add_argument("--corpus-dir", default=BY_CAND_DIR, help="directory of corpus_*.jsonl (default: residuals/by_candidate)")
    args = ap.parse_args()

    if not os.path.isdir(args.corpus_dir):
        print(f"ERROR: corpus dir not found: {args.corpus_dir}", file=sys.stderr)
        sys.exit(2)

    pattern = os.path.join(args.corpus_dir, "corpus_*.jsonl")
    files = sorted(glob.glob(pattern))
    if args.cand:
        files = [f for f in files if args.cand in f]
        if not files:
            print(f"ERROR: no corpus matching cand suffix `{args.cand}`", file=sys.stderr)
            sys.exit(2)

    out = {
        "tool": "extract_top_residuals",
        "args": vars(args),
        "corpora_count": len(files),
        "results": {},
    }
    grand_min = None
    grand_min_cand = None
    for path in files:
        cid = cand_id_from_corpus_name(path)
        recs = extract_one_corpus(path, top_k=args.top_k, hw_max=args.hw_max)
        out["results"][cid] = {
            "corpus_path": os.path.relpath(path),
            "records": recs,
            "n_emitted": len(recs),
            "min_hw_total": recs[0]["hw_total"] if recs else None,
        }
        if recs:
            mh = recs[0]["hw_total"]
            if grand_min is None or mh < grand_min:
                grand_min = mh
                grand_min_cand = cid

    out["summary"] = {
        "grand_min_hw_total": grand_min,
        "grand_min_cand": grand_min_cand,
        "cands_with_records": sum(1 for v in out["results"].values() if v["records"]),
    }

    text = json.dumps(out, indent=2)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text)
        print(f"wrote {args.out}: {len(files)} corpora, grand_min hw_total = {grand_min} ({grand_min_cand})", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
