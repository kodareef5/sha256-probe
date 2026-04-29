#!/usr/bin/env python3
"""
summarize_new88_continuation.py - Summarize the F347 score-88 follow-up.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[4]
DEFAULT_DISCOVERY = REPO / "headline_hunt/bets/math_principles/results/20260429_F347_radius1_basin_walk_scan_summary.json"
DEFAULT_KICKED = REPO / "headline_hunt/bets/math_principles/results/20260429_F348_radius1_new88_continuation_8x50k.json"
DEFAULT_SEEDED = REPO / "headline_hunt/bets/math_principles/results/20260429_F349_radius1_new88_seeded_8x50k.json"
DEFAULT_POLISH = REPO / "headline_hunt/bets/math_principles/results/20260429_F350_radius1_new88_polish.json"
DEFAULT_OUT_JSON = REPO / "headline_hunt/bets/math_principles/results/20260429_F350_radius1_new88_continuation_summary.json"
DEFAULT_OUT_MD = REPO / "headline_hunt/bets/math_principles/results/20260429_F350_radius1_new88_continuation_summary.md"


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


def best_result(run: dict[str, Any]) -> dict[str, Any]:
    results = list(run.get("results", []))
    if not results:
        raise ValueError("run JSON has no results")
    return min(results, key=lambda row: (row.get("objective", row["score"]), row["score"]))


def run_summary(label: str, path: Path, run: dict[str, Any]) -> dict[str, Any]:
    best = best_result(run)
    return {
        "label": label,
        "path": repo_path(path),
        "active_words": run.get("active_words"),
        "restarts": run.get("args", {}).get("restarts"),
        "iterations": run.get("args", {}).get("iterations"),
        "init_kicks": run.get("args", {}).get("init_kicks"),
        "polish": bool(run.get("args", {}).get("polish")),
        "best_score": best["score"],
        "best_objective": best.get("objective", best["score"]),
        "message_diff_hw": best.get("message_diff_hw"),
        "nonzero_message_words": best.get("nonzero_message_words"),
        "nonzero_schedule_words": best.get("nonzero_schedule_words"),
    }


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: RADIUS1_NEW88_CONTINUATION",
        "---",
        "",
        "# F350: radius-one score-88 continuation",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Discovery mask: `{payload['discovery_mask']}`.",
        "",
        "| Run | Restarts | Iterations | Kicks | Polish | Best | msgHW | Words |",
        "|---|---:|---:|---:|---|---:|---:|---:|",
    ]
    for row in payload["runs"]:
        lines.append(
            f"| `{row['label']}` | {row['restarts']} | {row['iterations']} | "
            f"{row['init_kicks']} | {row['polish']} | {row['best_score']} | "
            f"{row['message_diff_hw']} | {row['nonzero_message_words']} |"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        "The score-88 mask is real but narrow. No-kick seeding preserves it; kicked continuation loses it; single-bit polish finds no immediate descent. Promote it as a basin seed and rebuild the shared manifest before using it in later priors.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--discovery", type=Path, default=DEFAULT_DISCOVERY)
    ap.add_argument("--kicked", type=Path, default=DEFAULT_KICKED)
    ap.add_argument("--seeded", type=Path, default=DEFAULT_SEEDED)
    ap.add_argument("--polish", type=Path, default=DEFAULT_POLISH)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    args = ap.parse_args()

    discovery = read_json(args.discovery)
    kicked = read_json(args.kicked)
    seeded = read_json(args.seeded)
    polish = read_json(args.polish)
    runs = [
        run_summary("kicked_8x50k", args.kicked, kicked),
        run_summary("seeded_8x50k", args.seeded, seeded),
        run_summary("polish", args.polish, polish),
    ]
    discovery_mask = discovery.get("best", {}).get("active_mask")
    best_score = min(row["best_score"] for row in runs)
    if best_score < discovery.get("best", {}).get("scan_score", 999):
        verdict = "continuation_improved"
    elif any(row["label"] == "seeded_8x50k" and row["best_score"] == 88 for row in runs):
        verdict = "narrow_reproducible_score88_no_descent"
    else:
        verdict = "continuation_failed_to_reproduce"
    payload = {
        "discovery": repo_path(args.discovery),
        "discovery_mask": discovery_mask,
        "discovery_score": discovery.get("best", {}).get("scan_score"),
        "runs": runs,
        "verdict": verdict,
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    write_md(args.out_md, payload)
    print(json.dumps({
        "discovery_mask": discovery_mask,
        "runs": runs,
        "verdict": verdict,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
