#!/usr/bin/env python3
"""
summarize_radius1_scan.py - Summarize F346/F347 basin-walk scans.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[4]
DEFAULT_PLAN = REPO / "headline_hunt/bets/math_principles/results/20260429_F346_radius1_basin_walk_plan.json"
DEFAULT_SCAN = REPO / "headline_hunt/bets/math_principles/results/20260429_F347_radius1_basin_walk_scan.json"
DEFAULT_OUT_JSON = REPO / "headline_hunt/bets/math_principles/results/20260429_F347_radius1_basin_walk_scan_summary.json"
DEFAULT_OUT_MD = REPO / "headline_hunt/bets/math_principles/results/20260429_F347_radius1_basin_walk_scan_summary.md"


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def mask_key(words: list[int]) -> str:
    return ",".join(str(word) for word in sorted(words))


def plan_index(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["active_mask"]: row for row in plan.get("queue", [])}


def scan_rows(plan: dict[str, Any], scan: dict[str, Any]) -> list[dict[str, Any]]:
    idx = plan_index(plan)
    rows = []
    for entry in scan.get("subsets", []):
        mask = mask_key(entry["active_words"])
        best = entry["best"]
        planned = idx.get(mask, {})
        exact = planned.get("exact_observed")
        historical = exact.get("best_score") if exact else None
        delta = None if historical is None else best["score"] - historical
        rows.append({
            "active_mask": mask,
            "label": planned.get("label"),
            "scan_score": best["score"],
            "scan_objective": best.get("objective", best["score"]),
            "message_diff_hw": best.get("message_diff_hw"),
            "nonzero_message_words": best.get("nonzero_message_words"),
            "nonzero_schedule_words": best.get("nonzero_schedule_words"),
            "historical_score": historical,
            "delta_vs_historical": delta,
            "best_parent_score": planned.get("best_parent_score"),
            "parent_count": planned.get("parent_count"),
            "parents": planned.get("parents", []),
            "priority": planned.get("priority"),
            "pair_prior_diagnostic": planned.get("pair_prior_diagnostic"),
        })
    rows.sort(key=lambda row: (
        row["scan_score"],
        row["message_diff_hw"] if row["message_diff_hw"] is not None else 9999,
        row["active_mask"],
    ))
    return rows


def summarize(plan: dict[str, Any], scan: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    unseen = [row for row in rows if row["historical_score"] is None]
    controls = [row for row in rows if row["label"] == "known_bridge_control"]
    low_hits = [row for row in rows if row["scan_score"] <= 90]
    unseen_low_hits = [row for row in unseen if row["scan_score"] <= 90]
    improvements = [
        row for row in rows
        if row["delta_vs_historical"] is not None and row["delta_vs_historical"] < 0
    ]
    if unseen_low_hits:
        verdict = "radius1_unseen_basin_hit"
    elif low_hits:
        verdict = "radius1_reproduced_known_low"
    elif unseen and unseen[0]["scan_score"] <= 95:
        verdict = "radius1_near_hit"
    else:
        verdict = "radius1_negative"
    return {
        "plan": plan.get("mask_list"),
        "scan_args": scan.get("args", {}),
        "subsets_scanned": len(rows),
        "best": rows[0] if rows else None,
        "best_unseen": unseen[0] if unseen else None,
        "best_control": controls[0] if controls else None,
        "low_hit_count": len(low_hits),
        "unseen_low_hit_count": len(unseen_low_hits),
        "improvement_count": len(improvements),
        "verdict": verdict,
        "ranked_rows": rows,
    }


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: RADIUS1_BASIN_WALK_SCAN",
        "---",
        "",
        "# F347: radius-one basin-walk scan",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Subsets scanned: {payload['subsets_scanned']}.",
        f"Low hits: {payload['low_hit_count']}; unseen low hits: {payload['unseen_low_hit_count']}.",
    ]
    if payload["best"]:
        best = payload["best"]
        lines.append(
            f"Best score: {best['scan_score']} on `{best['active_mask']}` "
            f"({best['label'] or 'unplanned'})."
        )
    if payload["best_unseen"]:
        unseen = payload["best_unseen"]
        parent = unseen["parents"][0]["active_mask"] if unseen["parents"] else "-"
        lines.append(
            f"Best unseen: {unseen['scan_score']} on `{unseen['active_mask']}`, "
            f"parent {parent}."
        )
    lines.extend([
        "",
        "## Ranked Rows",
        "",
        "| Rank | Mask | Label | Score | Hist | Delta | Parent best | msgHW |",
        "|---:|---|---|---:|---:|---:|---:|---:|",
    ])
    for idx, row in enumerate(payload["ranked_rows"], 1):
        hist = "-" if row["historical_score"] is None else str(row["historical_score"])
        delta = "-" if row["delta_vs_historical"] is None else f"{row['delta_vs_historical']:+d}"
        parent = "-" if row["best_parent_score"] is None else str(row["best_parent_score"])
        label = row["label"] or "-"
        lines.append(
            f"| {idx} | `{row['active_mask']}` | `{label}` | {row['scan_score']} | "
            f"{hist} | {delta} | {parent} | {row['message_diff_hw']} |"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        "Promote the unseen score-88 mask to a focused continuation. The radius-one queue is a better next operator than the raw F343 submodular objective.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--plan", type=Path, default=DEFAULT_PLAN)
    ap.add_argument("--scan", type=Path, default=DEFAULT_SCAN)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    args = ap.parse_args()

    plan = read_json(args.plan)
    scan = read_json(args.scan)
    rows = scan_rows(plan, scan)
    payload = summarize(plan, scan, rows)
    payload["plan_path"] = repo_path(args.plan)
    payload["scan_path"] = repo_path(args.scan)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    write_md(args.out_md, payload)
    print(json.dumps({
        "best": payload["best"],
        "best_unseen": payload["best_unseen"],
        "subsets_scanned": payload["subsets_scanned"],
        "verdict": payload["verdict"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
