#!/usr/bin/env python3
"""
rank_cube_stats.py - Aggregate run_schedule_cubes.py JSONL outputs.

This turns cube-run result files into ranked cube, assignment, and pair
summaries. It is intentionally simple: a selector seed for future cube batches,
not a learned policy.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any


def metric_value(row: dict[str, Any], metric: str) -> float:
    stats = row.get("stats") or {}
    if metric in stats:
        return float(stats[metric])
    if metric in row:
        return float(row[metric])
    raise KeyError(f"metric {metric!r} missing from row {row.get('cube_id')}")


def assignment_key(assignment: dict[str, Any]) -> str:
    return (
        f"{assignment['target']}[{assignment['round']}]."
        f"b{assignment['bit']}={assignment['value']}"
    )


def summarize_values(values: list[float]) -> dict[str, float | int]:
    return {
        "count": len(values),
        "mean": round(statistics.mean(values), 6),
        "median": round(statistics.median(values), 6),
        "min": round(min(values), 6),
        "max": round(max(values), 6),
    }


def load_rows(paths: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in paths:
        with path.open() as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                row["_source"] = str(path)
                rows.append(row)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("jsonl", nargs="+", type=Path, help="cube result JSONL files")
    ap.add_argument("--metric", default="decisions",
                    help="stats metric to rank by; e.g. decisions, propagations, ticks, wall_seconds")
    ap.add_argument("--top", type=int, default=10, help="number of top rows to keep")
    ap.add_argument("--min-assignment-count", type=int, default=1,
                    help="minimum observations required for assignment aggregates")
    ap.add_argument("--min-pair-count", type=int, default=1,
                    help="minimum observations required for pair aggregates")
    ap.add_argument("--out-json", type=Path, help="optional JSON summary output")
    args = ap.parse_args()

    rows = load_rows(args.jsonl)
    if not rows:
        raise SystemExit("no rows loaded")

    scored: list[tuple[float, dict[str, Any]]] = []
    assignment_scores: dict[str, list[float]] = defaultdict(list)
    pair_scores: dict[str, list[float]] = defaultdict(list)

    for row in rows:
        value = metric_value(row, args.metric)
        scored.append((value, row))
        keys = [assignment_key(a) for a in row.get("assignments", [])]
        for key in keys:
            assignment_scores[key].append(value)
        for i, left in enumerate(keys):
            for right in keys[i + 1:]:
                pair_scores[" & ".join(sorted((left, right)))].append(value)

    top_cubes = []
    for value, row in sorted(scored, key=lambda x: x[0], reverse=True)[:args.top]:
        top_cubes.append({
            "cube_id": row["cube_id"],
            "metric": args.metric,
            "value": value,
            "status": row.get("status"),
            "source": row.get("_source"),
            "assignments": row.get("assignments", []),
        })

    top_assignments = [
        {"assignment": key, **summarize_values(values)}
        for key, values in assignment_scores.items()
        if len(values) >= args.min_assignment_count
    ]
    top_assignments.sort(key=lambda item: (item["mean"], item["count"]), reverse=True)

    top_pairs = [
        {"pair": key, **summarize_values(values)}
        for key, values in pair_scores.items()
        if len(values) >= args.min_pair_count
    ]
    top_pairs.sort(key=lambda item: (item["mean"], item["count"]), reverse=True)

    summary = {
        "metric": args.metric,
        "min_assignment_count": args.min_assignment_count,
        "min_pair_count": args.min_pair_count,
        "rows": len(rows),
        "sources": [str(p) for p in args.jsonl],
        "top_cubes": top_cubes,
        "top_assignments": top_assignments[:args.top],
        "top_pairs": top_pairs[:args.top],
    }

    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        with args.out_json.open("w") as f:
            json.dump(summary, f, indent=2, sort_keys=True)
            f.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
