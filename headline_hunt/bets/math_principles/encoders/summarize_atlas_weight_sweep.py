#!/usr/bin/env python3
"""
summarize_atlas_weight_sweep.py - Summarize atlas-loss weight sweeps.
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[4]
DEFAULT_PATTERN = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F352_new88_atlas_alpha*_4x20k.json"
)
DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F352_new88_atlas_weight_sweep_summary.json"
)
DEFAULT_OUT_MD = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F352_new88_atlas_weight_sweep_summary.md"
)


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


def chart_tuple(value: Any) -> tuple[str, str]:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return str(value[0]), str(value[1])
    return "?", "?"


def chart_match(value: Any) -> bool:
    chart = chart_tuple(value)
    return chart in {("dh", "dCh"), ("dCh", "dh")}


def best_by(
    restarts: list[dict[str, Any]],
    key: Any,
) -> dict[str, Any] | None:
    if not restarts:
        return None
    return min(restarts, key=key)


def run_row(path: Path, run: dict[str, Any]) -> dict[str, Any]:
    restarts = list(run.get("restarts", []))
    best_score = best_by(restarts, lambda row: row["best_score"])
    best_a57 = best_by(
        restarts,
        lambda row: (
            row["best_rec"]["a57_xor_hw"],
            0 if chart_match(row["best_rec"].get("chart_top2")) else 1,
            row["best_rec"]["D61_hw"],
            row["best_score"],
        ),
    )
    best_chart = best_by(
        [row for row in restarts if chart_match(row["best_rec"].get("chart_top2"))],
        lambda row: (
            row["best_rec"]["a57_xor_hw"],
            row["best_rec"]["D61_hw"],
            row["best_score"],
        ),
    )
    args = run.get("args", {})
    def compact(row: dict[str, Any] | None) -> dict[str, Any] | None:
        if row is None:
            return None
        rec = row["best_rec"]
        return {
            "restart": row.get("restart"),
            "score": row["best_score"],
            "a57_xor_hw": rec["a57_xor_hw"],
            "D61_hw": rec["D61_hw"],
            "chart_top2": list(chart_tuple(rec.get("chart_top2"))),
            "chart_match": chart_match(rec.get("chart_top2")),
            "tail63_state_diff_hw": rec["tail63_state_diff_hw"],
            "accepts": row.get("accepts"),
            "chart_matches": row.get("chart_matches"),
        }

    return {
        "path": repo_path(path),
        "active_words": run.get("active_words"),
        "restarts": args.get("restarts"),
        "iterations": args.get("iterations"),
        "alpha": args.get("alpha"),
        "beta": args.get("beta"),
        "gamma": args.get("gamma"),
        "delta": args.get("delta"),
        "seed": args.get("seed"),
        "wall_seconds": run.get("wall_seconds"),
        "best_score": compact(best_score),
        "best_a57": compact(best_a57),
        "best_chart_match": compact(best_chart),
        "any_chart_match_best": bool(run.get("any_chart_match_best")),
        "any_a57_zero_best": bool(run.get("any_a57_zero_best")),
    }


def verdict(rows: list[dict[str, Any]]) -> str:
    if any(row["best_a57"] and row["best_a57"]["a57_xor_hw"] == 0 for row in rows):
        return "a57_zero_found"
    if any(
        row["best_chart_match"] and row["best_chart_match"]["a57_xor_hw"] <= 4
        for row in rows
    ):
        return "near_chamber_candidate_found"
    if any(row["best_a57"] and row["best_a57"]["a57_xor_hw"] <= 4 for row in rows):
        return "a57_improves_but_chart_not_locked"
    return "alpha_sweep_did_not_improve_a57"


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: ATLAS_WEIGHT_SWEEP",
        "---",
        "",
        "# F352: new score-88 mask atlas-loss weight sweep",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Active words: `{','.join(str(x) for x in payload['active_words'])}`.",
        "",
        "| Alpha | Best score | Best a57 | Best a57 chart | Best chart-match a57 | Best chart-match D61 |",
        "|---:|---:|---:|---|---:|---:|",
    ]
    for row in payload["rows"]:
        score = row["best_score"]
        a57 = row["best_a57"]
        chart = row["best_chart_match"]
        chart_label = "-" if a57 is None else ",".join(a57["chart_top2"])
        chart_a57 = "-" if chart is None else str(chart["a57_xor_hw"])
        chart_d61 = "-" if chart is None else str(chart["D61_hw"])
        lines.append(
            f"| {row['alpha']} | {score['score'] if score else '-'} | "
            f"{a57['a57_xor_hw'] if a57 else '-'} | `{chart_label}` | "
            f"{chart_a57} | {chart_d61} |"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        "Raising the `a57_xor` weight alone is not enough to lock the score-88 mask into the `(dh,dCh)` chamber. Keep the mask as a useful basin seed, but treat chart membership as a coordinate that needs its own proposal operator rather than a scalar penalty.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", type=Path)
    ap.add_argument("--pattern", default=str(DEFAULT_PATTERN))
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    args = ap.parse_args()

    paths = args.paths or [Path(p) for p in sorted(glob.glob(args.pattern))]
    if not paths:
        raise SystemExit(f"no sweep files matched {args.pattern}")
    rows = [run_row(path, read_json(path)) for path in paths]
    rows.sort(key=lambda row: float(row["alpha"]))
    active_words = rows[0].get("active_words") or []
    payload = {
        "report_id": "F352",
        "active_words": active_words,
        "rows": rows,
        "verdict": verdict(rows),
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    write_md(args.out_md, payload)
    print(json.dumps({
        "verdict": payload["verdict"],
        "rows": [
            {
                "alpha": row["alpha"],
                "best_a57": row["best_a57"],
                "best_chart_match": row["best_chart_match"],
            }
            for row in rows
        ],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
