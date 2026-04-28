#!/usr/bin/env python3
"""
analyze_absorption_search.py - summarize block-2 absorption search outputs.

Consumes JSON files written by search_block2_absorption.py and reports:
- best runs by score
- active message-word frequency among top runs
- recurring low-HW message diffs
- recurring low-HW schedule diffs

This is meant to turn dense local-search candidates into trail-design hints.
"""
import argparse
import json
from collections import Counter, defaultdict


def hw32(x):
    return bin(x & 0xFFFFFFFF).count("1")


def load_runs(paths):
    runs = []
    for path in paths:
        with open(path) as f:
            data = json.load(f)
        for run in data.get("results", []):
            run = dict(run)
            run["_source"] = path
            run["_active_words"] = active_words_from_run(run)
            runs.append(run)
        for subset in data.get("subsets", []):
            run = dict(subset["best"])
            run["_source"] = path
            run["_allowed_words"] = list(subset["active_words"])
            run["_active_words"] = active_words_from_run(run)
            runs.append(run)
    runs.sort(key=lambda r: r["score"])
    return runs


def dedupe_runs(runs):
    seen = set()
    unique = []
    for run in runs:
        key = (tuple(run["M1"]), tuple(run["M2"]))
        if key in seen:
            continue
        seen.add(key)
        unique.append(run)
    return unique


def parse_words(words):
    return [int(x, 16) for x in words]


def active_words_from_run(run):
    m1 = parse_words(run["M1"])
    m2 = parse_words(run["M2"])
    return [i for i, (a, b) in enumerate(zip(m1, m2)) if a != b]


def print_best(runs, n):
    print("Best runs:")
    print("rank  score  objective  msgHW  msgWords  schedWords  active  source")
    for i, run in enumerate(runs[:n], 1):
        objective = run.get("objective", run["score"])
        active = ",".join(str(w) for w in run.get("_active_words", []))
        print(f"{i:>4}  {run['score']:>5}  {objective:>9.3f}  "
              f"{run['message_diff_hw']:>5}  "
              f"{run['nonzero_message_words']:>8}  "
              f"{run['nonzero_schedule_words']:>10}  {active:>6}  "
              f"{run['_source']}")


def dominates(a, b):
    a_tuple = (
        a["score"],
        a["message_diff_hw"],
        a["nonzero_message_words"],
        a["nonzero_schedule_words"],
    )
    b_tuple = (
        b["score"],
        b["message_diff_hw"],
        b["nonzero_message_words"],
        b["nonzero_schedule_words"],
    )
    return all(x <= y for x, y in zip(a_tuple, b_tuple)) and a_tuple != b_tuple


def pareto_frontier(runs):
    frontier = []
    for run in runs:
        if any(dominates(other, run) for other in runs):
            continue
        frontier.append(run)
    frontier.sort(key=lambda r: (
        r["score"],
        r["message_diff_hw"],
        r["nonzero_message_words"],
        r["nonzero_schedule_words"],
    ))
    return frontier


def print_pareto(runs, n):
    frontier = pareto_frontier(runs)
    print()
    print(f"Pareto frontier among {len(runs)} runs:")
    print("rank  score  msgHW  msgWords  schedWords  active  source")
    for i, run in enumerate(frontier[:n], 1):
        active = ",".join(str(w) for w in run.get("_active_words", []))
        print(f"{i:>4}  {run['score']:>5}  {run['message_diff_hw']:>5}  "
              f"{run['nonzero_message_words']:>8}  "
              f"{run['nonzero_schedule_words']:>10}  {active:>6}  "
              f"{run['_source']}")


def analyze_message_words(runs, top_n):
    freq = Counter()
    diff_freq = defaultdict(Counter)
    for run in runs[:top_n]:
        m1 = parse_words(run["M1"])
        m2 = parse_words(run["M2"])
        for i, (a, b) in enumerate(zip(m1, m2)):
            d = a ^ b
            if d:
                freq[i] += 1
                diff_freq[i][d] += 1

    print()
    print(f"Message-word activity among top {min(top_n, len(runs))}:")
    print("word  active  most_common_diff  count  hw")
    for i, count in freq.most_common():
        diff, dcount = diff_freq[i].most_common(1)[0]
        print(f"{i:>4}  {count:>6}  0x{diff:08x}        {dcount:>5}  {hw32(diff):>2}")


def analyze_schedule_words(runs, top_n):
    by_round = Counter()
    diff_by_round = defaultdict(Counter)
    for run in runs[:top_n]:
        for entry in run["schedule_diffs"]:
            rnd = entry["round"]
            diff = int(entry["diff"], 16)
            by_round[rnd] += 1
            diff_by_round[rnd][diff] += 1

    print()
    print(f"Schedule activity among top {min(top_n, len(runs))}:")
    print("round  active  most_common_diff  count  hw")
    for rnd, count in by_round.most_common(24):
        diff, dcount = diff_by_round[rnd].most_common(1)[0]
        print(f"{rnd:>5}  {count:>6}  0x{diff:08x}        {dcount:>5}  {hw32(diff):>2}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("json_files", nargs="+")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--dedupe", action="store_true",
                    help="Collapse duplicate M1/M2 candidates across artifacts")
    ap.add_argument("--pareto", action="store_true",
                    help="Print non-dominated score/sparsity tradeoff candidates")
    args = ap.parse_args()

    runs = load_runs(args.json_files)
    if args.dedupe:
        runs = dedupe_runs(runs)
    if not runs:
        print("No runs found.")
        return

    dedupe_note = " unique" if args.dedupe else ""
    print(f"Loaded {len(runs)}{dedupe_note} runs from {len(args.json_files)} file(s).")
    print_best(runs, min(args.top, len(runs)))
    if args.pareto:
        print_pareto(runs, min(args.top, len(runs)))
    analyze_message_words(runs, args.top)
    analyze_schedule_words(runs, args.top)


if __name__ == "__main__":
    main()
