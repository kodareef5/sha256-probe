#!/usr/bin/env python3
"""
rank_cube_surfaces.py - Compare labelled cube-result surfaces.

This is a small companion to rank_cube_stats.py for experiments that compare
structural cube families, such as universal-core dW bits versus shell schedule
bits. Inputs are labelled JSONL result files from run_schedule_cubes.py.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def parse_input(spec: str) -> tuple[str, Path]:
    if "=" not in spec:
        raise argparse.ArgumentTypeError("--input must be LABEL=PATH")
    label, path_s = spec.split("=", 1)
    label = label.strip()
    if not label:
        raise argparse.ArgumentTypeError("input label cannot be empty")
    path = Path(path_s)
    return label, path


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


def load_rows(inputs: list[tuple[str, Path]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for label, path in inputs:
        with path.open() as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                row["_surface"] = label
                row["_source"] = str(path)
                rows.append(row)
    return rows


def surface_summaries(rows: list[dict[str, Any]], metric: str) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["_surface"]].append(row)

    out = []
    for label, items in sorted(grouped.items()):
        metric_values = [metric_value(row, metric) for row in items]
        wall_values = [float(row["wall_seconds"]) for row in items if "wall_seconds" in row]
        statuses = Counter(str(row.get("status")) for row in items)
        summary = {
            "surface": label,
            "rows": len(items),
            "statuses": dict(sorted(statuses.items())),
            metric: summarize_values(metric_values),
        }
        if wall_values:
            summary["wall_seconds"] = summarize_values(wall_values)
        out.append(summary)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", action="append", required=True, type=parse_input,
                    help="labelled result JSONL, formatted LABEL=PATH")
    ap.add_argument("--metric", default="decisions",
                    help="metric to rank by; e.g. decisions, propagations, wall_seconds")
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--ascending", action="store_true",
                    help="rank smaller metric values first")
    ap.add_argument("--min-assignment-count", type=int, default=1)
    ap.add_argument("--out-json", type=Path)
    args = ap.parse_args()

    rows = load_rows(args.input)
    if not rows:
        raise SystemExit("no rows loaded")

    reverse = not args.ascending
    scored = [(metric_value(row, args.metric), row) for row in rows]

    top_cubes = []
    for value, row in sorted(scored, key=lambda item: item[0], reverse=reverse)[:args.top]:
        top_cubes.append({
            "surface": row["_surface"],
            "source": row["_source"],
            "cube_id": row["cube_id"],
            "metric": args.metric,
            "value": value,
            "status": row.get("status"),
            "wall_seconds": row.get("wall_seconds"),
            "assignments": row.get("assignments", []),
        })

    assignment_scores: dict[str, list[float]] = defaultdict(list)
    assignment_surfaces: dict[str, Counter[str]] = defaultdict(Counter)
    for value, row in scored:
        for assignment in row.get("assignments", []):
            key = assignment_key(assignment)
            assignment_scores[key].append(value)
            assignment_surfaces[key][row["_surface"]] += 1

    top_assignments = []
    for key, values in assignment_scores.items():
        if len(values) < args.min_assignment_count:
            continue
        top_assignments.append({
            "assignment": key,
            "surfaces": dict(sorted(assignment_surfaces[key].items())),
            **summarize_values(values),
        })
    top_assignments.sort(
        key=lambda item: (item["mean"], item["count"]),
        reverse=reverse,
    )

    summary = {
        "metric": args.metric,
        "order": "ascending" if args.ascending else "descending",
        "rows": len(rows),
        "inputs": [
            {"surface": label, "path": str(path)}
            for label, path in args.input
        ],
        "surface_summaries": surface_summaries(rows, args.metric),
        "top_cubes": top_cubes,
        "top_assignments": top_assignments[:args.top],
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
