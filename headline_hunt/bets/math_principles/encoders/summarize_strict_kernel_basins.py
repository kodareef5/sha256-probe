#!/usr/bin/env python3
"""
summarize_strict_kernel_basins.py - Compare current strict-kernel basins.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from headline_hunt.bets.math_principles.encoders.continue_atlas_from_seed import repo_path  # noqa: E402


DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F377_strict_kernel_basin_comparison.json"
)
SOURCES = {
    "F336": REPO / "headline_hunt/bets/block2_wang/results/search_artifacts/20260429_F336_kernel_safe_depth1_from_F322.json",
    "F372": REPO / "headline_hunt/bets/math_principles/results/20260429_F372_kernel_safe_beam_probe.json",
    "F374": REPO / "headline_hunt/bets/math_principles/results/20260429_F374_kernel_safe_pareto_bridge.json",
    "F375": REPO / "headline_hunt/bets/math_principles/results/20260429_F375_kernel_safe_bridge_anchor_continuation.json",
    "F376": REPO / "headline_hunt/bets/math_principles/results/20260429_F376_bridge_anchor_neighborhood.json",
}


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def chart(row: dict[str, Any]) -> str:
    return ",".join(row["rec"]["chart_top2"])


def row_from_candidate(
    basin: str,
    label: str,
    candidate: dict[str, Any],
    source: str,
    note: str,
    default_score_key: str = "score",
) -> dict[str, Any]:
    return {
        "basin": basin,
        "label": label,
        "source": source,
        "score": candidate.get(default_score_key, candidate.get("score")),
        "profile_score": candidate.get("profile_score"),
        "a57": candidate["rec"]["a57_xor_hw"],
        "D61": candidate["rec"]["D61_hw"],
        "chart": chart(candidate),
        "tail63": candidate["rec"]["tail63_state_diff_hw"],
        "note": note,
    }


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    if payload["combined_target_hits"]:
        return (
            "strict_kernel_basins_have_combined_target",
            "Promote the combined target hit to verification.",
        )
    if payload["distinct_basin_count"] >= 2 and payload["bridge_count"] > 0:
        return (
            "strict_kernel_basins_split_with_bridges",
            "The strict-kernel front has distinct basins and coordinate bridges, but no combined chamber-attractor hit.",
        )
    return (
        "strict_kernel_basin_record_incomplete",
        "Need more basin probes before drawing a strict-kernel basin conclusion.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: STRICT_KERNEL_BASIN_COMPARISON",
        "---",
        "",
        "# F377: strict-kernel basin comparison",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        payload["decision"],
        "",
        "| Basin | Label | Source | Score | Profile | a57 | D61 | Chart | Note |",
        "|---|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in payload["front_rows"]:
        profile = "" if row["profile_score"] is None else str(row["profile_score"])
        lines.append(
            f"| `{row['basin']}` | `{row['label']}` | `{row['source']}` | "
            f"{row['score']} | {profile} | {row['a57']} | {row['D61']} | "
            f"`{row['chart']}` | {row['note']} |"
        )
    lines.extend([
        "",
        "## Local Checks",
        "",
        "| Probe | Base | Moves | Score improves | Guard improves | D61 improves | Target repairs | Strict hits |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ])
    for row in payload["local_checks"]:
        lines.append(
            f"| `{row['probe']}` | {row['base']} | {row['moves']} | "
            f"{row['score_improve']} | {row['guard_improve']} | {row['D61_improve']} | "
            f"{row['target_repair']} | {row['strict_hits']} |"
        )
    lines.extend([
        "",
        "## Conclusion",
        "",
        "The current strict-kernel evidence is not a single basin slowly approaching the chamber attractor. "
        "It is a split Pareto front: random-init holds the low-a57 chamber-chart corner, "
        "the chamber-seed path holds the D61=5 corner and an off-chart a57=4 corner, "
        "and F375 proves one bridge direction exists only by trading D61 back away.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    f336 = read_json(SOURCES["F336"])
    f372 = read_json(SOURCES["F372"])
    f374 = read_json(SOURCES["F374"])
    f375 = read_json(SOURCES["F375"])
    f376 = read_json(SOURCES["F376"])

    front_rows = [
        row_from_candidate("random_init", "F322_seed_F336", f336["base"], "F336", "depth-1 local minimum"),
        row_from_candidate("chamber_seed", "F372_best_score", f372["best_score"], "F372", "best strict scalar score"),
        row_from_candidate("chamber_seed", "F372_best_D61", f372["best_d61"], "F372", "strict D61=5 corner"),
        row_from_candidate("chamber_seed", "F374_low_guard", f374["anchors"]["best_guard"], "F374", "nontrivial a57=4 corner"),
        row_from_candidate("chamber_seed", "F374_balanced", f374["anchors"]["best_balanced"], "F374", "chart bridge anchor"),
        row_from_candidate("chamber_seed", "F374_low_D61", f374["anchors"]["best_d61"], "F374", "Pareto D61=5 anchor"),
    ]
    f375_bridge = None
    for row in f375["anchor_runs"]:
        if row["label"] == "best_d61":
            f375_bridge = row["best_profile"]
            break
    if f375_bridge is None:
        raise ValueError("F375 has no best_d61 bridge row")
    front_rows.append(row_from_candidate(
        "bridge",
        "F375_D61_to_guard",
        f375_bridge,
        "F375",
        "D61-side bridge repairs guard but loses D61=5",
        default_score_key="default_score",
    ))
    front_rows = sorted(front_rows, key=lambda row: (row["a57"], row["D61"], row["score"]))
    combined_target_hits = [
        row for row in front_rows
        if row["a57"] <= 4 and row["D61"] <= 5 and row["chart"] in {"dh,dCh", "dCh,dh"}
    ]
    local_checks = [
        {
            "probe": "F336_depth1_from_F322",
            "base": "a57=5 D61=14 chart=dh,dCh",
            "moves": 1536,
            "score_improve": f336["score_break_count"],
            "guard_improve": f336["a57_break_count"],
            "D61_improve": f336["D61_break_count"],
            "target_repair": 0,
            "strict_hits": 0,
        },
        {
            "probe": "F376_depth1_from_F375_bridge",
            "base": "a57=5 D61=13 chart=dCh,dh",
            "moves": f376["valid_moves"],
            "score_improve": f376["default_improve_count"],
            "guard_improve": f376["guard_lower_count"],
            "D61_improve": f376["d61_lower_count"],
            "target_repair": f376["target_repair_count"],
            "strict_hits": f376["strict_benchmark_hit_count"],
        },
    ]
    payload = {
        "report_id": "F377",
        "sources": {key: repo_path(path) for key, path in SOURCES.items()},
        "front_rows": front_rows,
        "local_checks": local_checks,
        "combined_target_hits": combined_target_hits,
        "distinct_basin_count": len({row["basin"] for row in front_rows if row["basin"] != "bridge"}),
        "bridge_count": sum(1 for row in front_rows if row["basin"] == "bridge"),
    }
    payload["verdict"], payload["decision"] = verdict(payload)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    out_md = args.out_md or args.out_json.with_suffix(".md")
    write_md(out_md, payload)
    print(json.dumps({
        "verdict": payload["verdict"],
        "front_rows": len(front_rows),
        "combined_target_hits": len(combined_target_hits),
        "local_checks": local_checks,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
