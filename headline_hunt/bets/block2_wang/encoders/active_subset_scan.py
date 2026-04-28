#!/usr/bin/env python3
"""
active_subset_scan.py - scan compact block-2 absorber active-word masks.

This wraps search_block2_absorption.py for a different question: given a
pool of message-word positions, which small active subsets are worth spending
more solver time on?

The output is a JSON file containing every scanned subset and its best runs,
plus a ranked summary by target distance/objective.

Example:
    PYTHONPATH=. python3 active_subset_scan.py bundle.json \
      --pool 0,1,5,7,8,9,10,11,12,13,14 --sizes 3-5 \
      --restarts 3 --iterations 4000 --limit 80 \
      --init-json previous_sparse_search.json --out-json subset_scan.json
"""
import argparse
import itertools
import json
import os
import random
import sys
import time
from types import SimpleNamespace


REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)

from headline_hunt.bets.block2_wang.encoders.search_block2_absorption import (
    block2_context,
    candidate_words,
    load_init_pair,
    parse_active_words,
    run_restart,
)


def parse_sizes(spec):
    sizes = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = [int(x) for x in part.split("-", 1)]
            sizes.extend(range(lo, hi + 1))
        else:
            sizes.append(int(part))
    sizes = sorted(set(sizes))
    if not sizes or any(n < 1 or n > 16 for n in sizes):
        raise ValueError("--sizes must name subset sizes in [1,16]")
    return sizes


def subset_iter(pool, sizes, include_words):
    pool = sorted(set(pool))
    include_words = sorted(set(include_words))
    missing = [w for w in include_words if w not in pool]
    if missing:
        raise ValueError(f"--include words are absent from --pool: {missing}")

    include = tuple(include_words)
    rest = [w for w in pool if w not in include]
    for size in sizes:
        if size < len(include) or size > len(pool):
            continue
        for extra in itertools.combinations(rest, size - len(include)):
            yield tuple(sorted(include + extra))


def scan_subset(bundle, subset, subset_idx, args, hints, init_pair):
    search_args = SimpleNamespace(
        seed=args.seed + subset_idx * args.seed_stride,
        iterations=args.iterations,
        anchor=args.anchor,
        start=args.start,
        temp_start=args.temp_start,
        temp_end=args.temp_end,
        hw_penalty=args.hw_penalty,
        word_penalty=args.word_penalty,
        polish=args.polish,
        progress=0,
    )
    runs = []
    for restart in range(args.restarts):
        this_init = init_pair if restart == 0 else None
        run = run_restart(
            bundle,
            restart,
            search_args,
            hints,
            list(subset),
            init_pair=this_init,
        )
        runs.append(run)
    runs.sort(key=lambda r: (r.get("objective", r["score"]), r["score"]))
    ranked_runs = runs
    min_used = len(subset) if args.require_all_used else args.min_used_words
    if min_used:
        strict_runs = [
            run for run in runs
            if run["nonzero_message_words"] >= min_used
        ]
        if strict_runs:
            ranked_runs = strict_runs
    return {
        "active_words": list(subset),
        "seed": search_args.seed,
        "min_used_words": min_used,
        "strict_match": ranked_runs is not runs,
        "best": ranked_runs[0],
        "runs": runs if args.keep_runs else runs[: min(3, len(runs))],
    }


def rank_key(entry):
    best = entry["best"]
    return (
        best["score"],
        best.get("objective", best["score"]),
        best["message_diff_hw"],
        best["nonzero_message_words"],
    )


def print_top(entries, top_n):
    print("rank  score  objective  msgHW  words  sched  strict  active")
    for i, entry in enumerate(sorted(entries, key=rank_key)[:top_n], 1):
        best = entry["best"]
        active = ",".join(str(w) for w in entry["active_words"])
        strict = "yes" if entry.get("strict_match") else "no"
        print(f"{i:>4}  {best['score']:>5}  {best.get('objective', best['score']):>9.3f}  "
              f"{best['message_diff_hw']:>5}  {best['nonzero_message_words']:>5}  "
              f"{best['nonzero_schedule_words']:>5}  {strict:>6}  {active}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bundle", help="2blockcertpin/v1 trail bundle JSON")
    ap.add_argument("--pool", default="0-15",
                    help="Comma/range list of candidate message words")
    ap.add_argument("--sizes", default="4",
                    help="Comma/range list of subset sizes to scan")
    ap.add_argument("--include", default="",
                    help="Comma/range list of message words forced into every subset")
    ap.add_argument("--limit", type=int, default=0,
                    help="Stop after scanning this many subsets; 0 means no limit")
    ap.add_argument("--start-index", type=int, default=0,
                    help="Skip this many subsets after optional shuffle")
    ap.add_argument("--shuffle", action="store_true",
                    help="Shuffle subset order before applying --limit")
    ap.add_argument("--restarts", type=int, default=2)
    ap.add_argument("--iterations", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--seed-stride", type=int, default=1009)
    ap.add_argument("--anchor", choices=["random", "zero"], default="random")
    ap.add_argument("--start", choices=["same", "random", "zero"], default="same")
    ap.add_argument("--temp-start", type=float, default=2.5)
    ap.add_argument("--temp-end", type=float, default=0.05)
    ap.add_argument("--hw-penalty", type=float, default=0.0)
    ap.add_argument("--word-penalty", type=float, default=0.0)
    ap.add_argument("--polish", action="store_true")
    ap.add_argument("--init-json", default=None,
                    help="Seed restart 0 of every subset from a previous search JSON")
    ap.add_argument("--keep-runs", action="store_true",
                    help="Store all per-restart runs instead of only the top few")
    ap.add_argument("--min-used-words", type=int, default=0,
                    help="Rank by candidates using at least this many message words when available")
    ap.add_argument("--require-all-used", action="store_true",
                    help="Rank by candidates using every allowed active word when available")
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--out-json", default=None)
    args = ap.parse_args()
    if args.min_used_words < 0 or args.min_used_words > 16:
        raise SystemExit("--min-used-words must be in [0,16]")
    if args.start_index < 0:
        raise SystemExit("--start-index must be non-negative")

    with open(args.bundle) as f:
        bundle = json.load(f)

    pool = parse_active_words(args.pool)
    sizes = parse_sizes(args.sizes)
    include = parse_active_words(args.include) if args.include else []
    all_subsets = list(subset_iter(pool, sizes, include))
    if args.shuffle:
        random.Random(args.seed).shuffle(all_subsets)
    total_available = len(all_subsets)
    if args.start_index:
        all_subsets = all_subsets[args.start_index:]
    if args.limit:
        all_subsets = all_subsets[:args.limit]
    total = len(all_subsets)
    if total == 0:
        raise SystemExit("no subsets selected")

    _, _, working_diff, chain_diff = block2_context(bundle)
    hints = candidate_words(working_diff, chain_diff)
    init_pair = load_init_pair(args.init_json) if args.init_json else None

    t0 = time.time()
    scanned = []
    for subset_idx, subset in enumerate(all_subsets):
        entry = scan_subset(bundle, subset, subset_idx, args, hints, init_pair)
        scanned.append(entry)
        best = entry["best"]
        print(f"[{len(scanned)}/{total}] active={','.join(str(w) for w in subset)} "
              f"score={best['score']} obj={best.get('objective', best['score']):.3f} "
              f"msgHW={best['message_diff_hw']}", file=sys.stderr)

    scanned.sort(key=rank_key)

    print("=== active subset scan ===")
    print(f"Bundle:              {args.bundle}")
    print(f"Pool:                {','.join(str(w) for w in pool)}")
    print(f"Sizes:               {','.join(str(s) for s in sizes)}")
    print(f"Include:             {','.join(str(w) for w in include) if include else '(none)'}")
    print(f"Subsets scanned:     {len(scanned)}")
    print(f"Total available:     {total_available}")
    print(f"Start index:         {args.start_index}")
    print(f"Restarts/iterations: {args.restarts}/{args.iterations}")
    print(f"Penalties hw/word:   {args.hw_penalty}/{args.word_penalty}")
    min_used_label = "all allowed" if args.require_all_used else str(args.min_used_words)
    print(f"Min used words:      {min_used_label}")
    print()
    print_top(scanned, min(args.top, len(scanned)))

    if args.out_json:
        with open(args.out_json, "w") as f:
            json.dump({
                "bundle": args.bundle,
                "args": vars(args),
                "total_available": total_available,
                "start_index": args.start_index,
                "elapsed_seconds": round(time.time() - t0, 3),
                "subsets_scanned": len(scanned),
                "subsets": scanned,
            }, f, indent=2)
        print(f"\nFull JSON: {args.out_json}", file=sys.stderr)


if __name__ == "__main__":
    main()
