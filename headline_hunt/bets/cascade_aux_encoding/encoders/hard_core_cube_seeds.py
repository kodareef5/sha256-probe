#!/usr/bin/env python3
"""
hard_core_cube_seeds.py - Rank schedule cube bits with hard-core structure.

This combines identify_hard_core.py JSON output with optional
run_schedule_cubes.py --stats JSONL files. It is a selector helper: it ranks
free schedule bits by structural core membership and by observed solver stats.
"""

from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from schedule_cube_planner import n_free_words, schedule_var


def metric_value(row: dict[str, Any], metric: str) -> float | None:
    stats = row.get("stats") or {}
    if metric in stats:
        return float(stats[metric])
    if metric in row:
        return float(row[metric])
    return None


def summarize(values: list[float]) -> dict[str, float | int] | None:
    if not values:
        return None
    return {
        "count": len(values),
        "mean": round(statistics.mean(values), 6),
        "median": round(statistics.median(values), 6),
        "min": round(min(values), 6),
        "max": round(max(values), 6),
    }


def load_observed_bit_stats(
    paths: list[Path],
    metric: str,
    target: str,
    round_: int,
) -> dict[int, dict[str, Any]]:
    by_bit: dict[int, list[float]] = defaultdict(list)
    by_value: dict[tuple[int, int], list[float]] = defaultdict(list)

    for path in paths:
        with path.open() as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                value = metric_value(row, metric)
                if value is None:
                    continue
                for assignment in row.get("assignments", []):
                    if assignment.get("target") != target:
                        continue
                    if assignment.get("round") != round_:
                        continue
                    bit = int(assignment["bit"])
                    assigned_value = int(assignment["value"])
                    by_bit[bit].append(value)
                    by_value[(bit, assigned_value)].append(value)

    out: dict[int, dict[str, Any]] = {}
    for bit, values in by_bit.items():
        value_summaries = {}
        for assigned_value in (0, 1):
            summary = summarize(by_value.get((bit, assigned_value), []))
            if summary:
                value_summaries[str(assigned_value)] = summary
        out[bit] = {
            "all": summarize(values),
            "by_value": value_summaries,
        }
    return out


def best_value(observed: dict[str, Any] | None) -> int | None:
    if not observed:
        return None
    by_value = observed.get("by_value", {})
    candidates = []
    for value_s, summary in by_value.items():
        candidates.append((float(summary["mean"]), int(summary["count"]), int(value_s)))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][2]


def rank_bits(
    hard_core: dict[str, Any],
    target: str,
    round_: int,
    metric: str,
    observed: dict[int, dict[str, Any]],
    core_weight: float,
) -> list[dict[str, Any]]:
    sr = 64 - int(hard_core["n_free"])
    n_free = n_free_words(sr)
    first_round = 57
    last_round = first_round + n_free - 1
    if round_ < first_round or round_ > last_round:
        raise ValueError(f"round {round_} outside free window {first_round}..{last_round}")

    core_vars = set(int(v) for v in hard_core["core_vars"])
    observed_max = max(
        (float(item["all"]["mean"]) for item in observed.values() if item.get("all")),
        default=0.0,
    )

    rows: list[dict[str, Any]] = []
    for bit in range(32):
        obs = observed.get(bit)
        observed_mean = float(obs["all"]["mean"]) if obs and obs.get("all") else 0.0
        observed_component = observed_mean / observed_max if observed_max else 0.0

        if target == "dw":
            w1 = schedule_var(sr, "w1", round_, bit)
            w2 = schedule_var(sr, "w2", round_, bit)
            w1_core = w1 in core_vars
            w2_core = w2 in core_vars
            core_count = int(w1_core) + int(w2_core)
            if core_count == 2:
                core_class = "both_core"
            elif core_count == 1:
                core_class = "one_core"
            else:
                core_class = "shell"
            base = core_count / 2.0
            row = {
                "target": target,
                "round": round_,
                "bit": bit,
                "w1_var": w1,
                "w2_var": w2,
                "w1_core": w1_core,
                "w2_core": w2_core,
                "core_class": core_class,
            }
        else:
            var = schedule_var(sr, target, round_, bit)
            is_core = var in core_vars
            base = 1.0 if is_core else 0.0
            row = {
                "target": target,
                "round": round_,
                "bit": bit,
                "var": var,
                "core_class": "core" if is_core else "shell",
                "is_core": is_core,
            }

        row.update({
            "metric": metric,
            "score": round(core_weight * base + observed_component, 6),
            "structural_score": base,
            "observed_component": round(observed_component, 6),
            "observed": obs,
            "preferred_value": best_value(obs),
        })
        rows.append(row)

    rows.sort(
        key=lambda item: (
            item["score"],
            item["structural_score"],
            item["observed_component"],
            item["bit"],
        ),
        reverse=True,
    )
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hard-core-json", required=True, type=Path)
    ap.add_argument("--target", choices=("w1", "w2", "dw"), default="dw")
    ap.add_argument("--round", type=int, required=True)
    ap.add_argument("--metric", default="decisions")
    ap.add_argument("--stats-jsonl", action="append", type=Path, default=[],
                    help="optional run_schedule_cubes.py --stats JSONL; repeatable")
    ap.add_argument("--core-weight", type=float, default=2.0,
                    help="weight applied to structural core membership")
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--out-json", type=Path)
    args = ap.parse_args()

    with args.hard_core_json.open() as f:
        hard_core = json.load(f)

    observed = load_observed_bit_stats(
        args.stats_jsonl,
        args.metric,
        args.target,
        args.round,
    )
    rows = rank_bits(
        hard_core,
        args.target,
        args.round,
        args.metric,
        observed,
        args.core_weight,
    )
    summary = {
        "hard_core_json": str(args.hard_core_json),
        "target": args.target,
        "round": args.round,
        "metric": args.metric,
        "stats_jsonl": [str(p) for p in args.stats_jsonl],
        "core_weight": args.core_weight,
        "rows": rows,
        "top": rows[:args.top],
    }

    print(json.dumps({"top": rows[:args.top]}, indent=2, sort_keys=True))
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        with args.out_json.open("w") as f:
            json.dump(summary, f, indent=2, sort_keys=True)
            f.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
