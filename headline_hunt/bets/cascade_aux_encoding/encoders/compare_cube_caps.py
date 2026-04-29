#!/usr/bin/env python3
"""
compare_cube_caps.py - Compare cube metrics across two solver caps.

The tool joins two run_schedule_cubes.py JSONL files by cube_id and reports
rank movement, metric ratios, and a simple Spearman rank correlation.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def metric_value(row: dict[str, Any], metric: str) -> float:
    stats = row.get("stats") or {}
    if metric in stats:
        return float(stats[metric])
    if metric in row:
        return float(row[metric])
    raise KeyError(f"metric {metric!r} missing from row {row.get('cube_id')}")


def load_by_cube(path: Path) -> dict[str, dict[str, Any]]:
    rows = {}
    with path.open() as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            rows[row["cube_id"]] = row
    return rows


def ranks(rows: dict[str, dict[str, Any]], metric: str, descending: bool) -> dict[str, int]:
    scored = [
        (metric_value(row, metric), cube_id)
        for cube_id, row in rows.items()
    ]
    scored.sort(reverse=descending)
    return {cube_id: idx + 1 for idx, (_, cube_id) in enumerate(scored)}


def spearman_from_ranks(left: list[int], right: list[int]) -> float | None:
    n = len(left)
    if n < 2:
        return None
    total = sum((a - b) ** 2 for a, b in zip(left, right))
    return round(1.0 - (6.0 * total) / (n * (n * n - 1)), 6)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", required=True, type=Path)
    ap.add_argument("--followup", required=True, type=Path)
    ap.add_argument("--baseline-label", default="baseline")
    ap.add_argument("--followup-label", default="followup")
    ap.add_argument("--metric", default="decisions")
    ap.add_argument("--ascending", action="store_true",
                    help="rank smaller metric values first")
    ap.add_argument("--out-json", type=Path)
    args = ap.parse_args()

    baseline = load_by_cube(args.baseline)
    followup = load_by_cube(args.followup)
    shared_ids = sorted(set(baseline) & set(followup))
    if not shared_ids:
        raise SystemExit("no overlapping cube_id values")

    descending = not args.ascending
    baseline_ranks = ranks(
        {cube_id: baseline[cube_id] for cube_id in shared_ids},
        args.metric,
        descending,
    )
    followup_ranks = ranks(
        {cube_id: followup[cube_id] for cube_id in shared_ids},
        args.metric,
        descending,
    )

    rows = []
    for cube_id in shared_ids:
        b_value = metric_value(baseline[cube_id], args.metric)
        f_value = metric_value(followup[cube_id], args.metric)
        rows.append({
            "cube_id": cube_id,
            f"{args.baseline_label}_{args.metric}": b_value,
            f"{args.followup_label}_{args.metric}": f_value,
            "ratio": round(f_value / b_value, 6) if b_value else None,
            "baseline_rank": baseline_ranks[cube_id],
            "followup_rank": followup_ranks[cube_id],
            "rank_delta": followup_ranks[cube_id] - baseline_ranks[cube_id],
            "baseline_status": baseline[cube_id].get("status"),
            "followup_status": followup[cube_id].get("status"),
        })

    rows.sort(key=lambda row: (row["followup_rank"], row["baseline_rank"]))
    summary = {
        "metric": args.metric,
        "order": "ascending" if args.ascending else "descending",
        "baseline": str(args.baseline),
        "followup": str(args.followup),
        "baseline_label": args.baseline_label,
        "followup_label": args.followup_label,
        "shared_cubes": len(shared_ids),
        "spearman_rank_correlation": spearman_from_ranks(
            [baseline_ranks[cube_id] for cube_id in shared_ids],
            [followup_ranks[cube_id] for cube_id in shared_ids],
        ),
        "rows": rows,
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
