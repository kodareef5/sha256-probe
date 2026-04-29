#!/usr/bin/env python3
"""
summarize_submodular_scan.py - Summarize F343/F344 calibration scans.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[4]
DEFAULT_SELECTORS = REPO / "headline_hunt/bets/math_principles/results/20260429_F343_submodular_selectors.json"
DEFAULT_SCAN = REPO / "headline_hunt/bets/math_principles/results/20260429_F344_submodular_mask_calibration_scan.json"
DEFAULT_OUT_JSON = REPO / "headline_hunt/bets/math_principles/results/20260429_F344_submodular_mask_calibration_scan_summary.json"
DEFAULT_OUT_MD = REPO / "headline_hunt/bets/math_principles/results/20260429_F344_submodular_mask_calibration_scan_summary.md"


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


def selector_index(selectors: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows = {}
    for row in selectors.get("mask_list_rows", []):
        rows[row["active_mask"]] = row
    return rows


def scan_rows(scan: dict[str, Any], selectors: dict[str, Any]) -> list[dict[str, Any]]:
    idx = selector_index(selectors)
    rows = []
    for entry in scan.get("subsets", []):
        mask = mask_key(entry["active_words"])
        best = entry["best"]
        selector = idx.get(mask, {})
        exact = selector.get("exact_observed")
        historical_score = exact.get("best_score") if exact else None
        delta = None if historical_score is None else best["score"] - historical_score
        rows.append({
            "active_mask": mask,
            "label": selector.get("label"),
            "scan_score": best["score"],
            "scan_objective": best.get("objective", best["score"]),
            "message_diff_hw": best.get("message_diff_hw"),
            "nonzero_message_words": best.get("nonzero_message_words"),
            "historical_score": historical_score,
            "delta_vs_historical": delta,
            "selector_objective_rank": selector.get("objective_rank"),
            "selector_objective": selector.get("objective"),
            "pair_prior_diagnostic": selector.get("pair_prior_diagnostic"),
        })
    rows.sort(key=lambda row: (
        row["scan_score"],
        row["message_diff_hw"] if row["message_diff_hw"] is not None else 9999,
        row["active_mask"],
    ))
    return rows


def summarize(rows: list[dict[str, Any]], selectors: dict[str, Any], scan: dict[str, Any]) -> dict[str, Any]:
    best = rows[0] if rows else None
    unseen = [row for row in rows if row["historical_score"] is None]
    controls = [row for row in rows if row["label"] == "known_good_control"]
    improvements = [
        row for row in rows
        if row["delta_vs_historical"] is not None and row["delta_vs_historical"] < 0
    ]
    matched_headline = [row for row in rows if row["scan_score"] <= 90]
    if matched_headline:
        verdict = "scan_found_low_score"
    elif best and best["scan_score"] <= 92:
        verdict = "negative_but_near_control"
    else:
        verdict = "negative_calibration_scan"
    return {
        "selectors": selectors.get("mask_list"),
        "selector_verdict": selectors.get("calibration", {}).get("verdict"),
        "scan_args": scan.get("args", {}),
        "subsets_scanned": len(rows),
        "best": best,
        "best_unseen": unseen[0] if unseen else None,
        "best_control": controls[0] if controls else None,
        "improvement_count": len(improvements),
        "low_score_count": len(matched_headline),
        "verdict": verdict,
        "ranked_rows": rows,
    }


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: SUBMODULAR_SCAN_CALIBRATION",
        "---",
        "",
        "# F344: submodular mask calibration scan",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Selector verdict entering scan: `{payload['selector_verdict']}`.",
        f"Subsets scanned: {payload['subsets_scanned']}.",
    ]
    if payload["best"]:
        best = payload["best"]
        lines.append(
            f"Best scan score: {best['scan_score']} on `{best['active_mask']}` "
            f"({best['label'] or 'unlabeled'})."
        )
    if payload["best_unseen"]:
        unseen = payload["best_unseen"]
        lines.append(
            f"Best unseen score: {unseen['scan_score']} on `{unseen['active_mask']}` "
            f"(selector rank {unseen['selector_objective_rank']})."
        )
    lines.extend([
        "",
        "## Ranked Scan Rows",
        "",
        "| Rank | Mask | Label | Score | Hist | Delta | msgHW | Selector rank |",
        "|---:|---|---|---:|---:|---:|---:|---:|",
    ])
    for idx, row in enumerate(payload["ranked_rows"], 1):
        hist = "-" if row["historical_score"] is None else str(row["historical_score"])
        delta = "-" if row["delta_vs_historical"] is None else f"{row['delta_vs_historical']:+d}"
        label = row["label"] or "-"
        selector_rank = "-" if row["selector_objective_rank"] is None else str(row["selector_objective_rank"])
        lines.append(
            f"| {idx} | `{row['active_mask']}` | `{label}` | {row['scan_score']} | "
            f"{hist} | {delta} | {row['message_diff_hw']} | {selector_rank} |"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        "This budget does not validate the submodular selector as a search accelerator. Keep the F343 priors as descriptive features, but do not spend broad scan budget on the raw coverage objective without adding outcome-aware calibration.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selectors", type=Path, default=DEFAULT_SELECTORS)
    ap.add_argument("--scan", type=Path, default=DEFAULT_SCAN)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    args = ap.parse_args()

    selectors = read_json(args.selectors)
    scan = read_json(args.scan)
    rows = scan_rows(scan, selectors)
    payload = summarize(rows, selectors, scan)
    payload["selectors_path"] = repo_path(args.selectors)
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
