#!/usr/bin/env python3
"""Analyze absorber matrix correction profiles.

The absorber probe ranks residuals by final state-difference HW after a free
second block. This script adds a more two-block-native view: for each run, how
many original residual bits survive, how many are cleared, and which lanes
grow or shrink relative to the block-1 residual signature.
"""

import argparse
import csv
import glob
import json
from pathlib import Path
from statistics import mean
from typing import Any

LANES = ("a", "b", "c", "d", "e", "f", "g", "h")


def parse_words(raw: str | list[str]) -> list[int]:
    if isinstance(raw, list):
        return [int(x, 16) if isinstance(x, str) else int(x) for x in raw]
    return [int(part, 16) for part in raw.split(",") if part.strip()]


def popcount(x: int) -> int:
    return int(x & 0xFFFFFFFF).bit_count()


def load_residuals(path: Path) -> dict[int, dict[str, Any]]:
    rows = {}
    with path.open("r", encoding="utf-8") as fh:
        for idx, line in enumerate(fh, start=1):
            row = json.loads(line)
            row["diff63_int"] = parse_words(row["diff63"])
            row["input_lane_hw"] = [popcount(x) for x in row["diff63_int"]]
            rows[idx] = row
    return rows


def analyze_row(residual: dict[str, Any], raw: dict[str, str], csv_path: Path) -> dict[str, Any]:
    diff = residual["diff63_int"]
    best = parse_words(raw["best_state_diff"])

    overlap = [popcount(d & b) for d, b in zip(diff, best)]
    cleared = [popcount(d & ~b) for d, b in zip(diff, best)]
    new_bits = [popcount((~d) & b) for d, b in zip(diff, best)]
    best_lane_hw = [popcount(x) for x in best]
    lane_delta = [b - i for b, i in zip(best_lane_hw, residual["input_lane_hw"])]

    return {
        "csv": str(csv_path),
        "record": int(raw["record"]),
        "rank": int(residual["source_rank"]),
        "candidate": residual["candidate_id"],
        "block1_hw": int(raw["input_hw"]),
        "bridge_score": residual.get("score"),
        "rounds": int(raw["rounds"]),
        "start_hw": int(raw["start_hw"]),
        "best_hw": int(raw["best_hw"]),
        "improvement": int(raw["improvement"]),
        "W": [residual.get(f"w_{slot}") for slot in range(57, 61)],
        "best_m2": raw["best_m2"],
        "best_state_diff": [f"0x{x:08x}" for x in best],
        "input_lane_hw": residual["input_lane_hw"],
        "best_lane_hw": best_lane_hw,
        "lane_delta": lane_delta,
        "overlap_lane_hw": overlap,
        "cleared_lane_hw": cleared,
        "new_lane_hw": new_bits,
        "overlap_total": sum(overlap),
        "cleared_total": sum(cleared),
        "new_total": sum(new_bits),
        "cg_best_hw": best_lane_hw[2] + best_lane_hw[6],
        "cg_new_hw": new_bits[2] + new_bits[6],
        "cg_cleared_hw": cleared[2] + cleared[6],
    }


def summarize(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_rank: dict[int, list[dict[str, Any]]] = {}
    for obs in observations:
        by_rank.setdefault(obs["rank"], []).append(obs)

    rows = []
    for rank, items in by_rank.items():
        best = min(items, key=lambda x: (x["best_hw"], -x["cleared_total"], x["new_total"], x["rounds"]))
        late = [x for x in items if x["rounds"] >= 20]
        late_best = min(late, key=lambda x: (x["best_hw"], -x["cleared_total"], x["new_total"])) if late else None
        rows.append({
            "rank": rank,
            "block1_hw": best["block1_hw"],
            "bridge_score": best["bridge_score"],
            "best_hw_min": best["best_hw"],
            "best_hw_mean": round(mean(x["best_hw"] for x in items), 3),
            "cleared_max": max(x["cleared_total"] for x in items),
            "cleared_mean": round(mean(x["cleared_total"] for x in items), 3),
            "new_mean": round(mean(x["new_total"] for x in items), 3),
            "overlap_mean": round(mean(x["overlap_total"] for x in items), 3),
            "cg_best_min": min(x["cg_best_hw"] for x in items),
            "late_best_hw": late_best["best_hw"] if late_best else None,
            "late_cleared": late_best["cleared_total"] if late_best else None,
            "best_rounds": best["rounds"],
            "best_W": best["W"],
        })

    rows.sort(key=lambda x: (
        x["late_best_hw"] if x["late_best_hw"] is not None else 999,
        x["best_hw_min"],
        -x["cleared_max"],
        x["new_mean"],
        x["rank"],
    ))
    return rows


def write_md(path: Path, ranking: list[dict[str, Any]], observations: list[dict[str, Any]]) -> None:
    lines = [
        "# Absorber Profile Summary",
        "",
        "Ranking favors late-round absorber quality first, then global best HW and residual-bit clearing.",
        "",
        "| Rank | Block-1 HW | Bridge | Best HW | Mean HW | Late Best | Max Cleared | Mean Cleared | Mean New | Min c/g HW | Best Rounds | W57..W60 |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in ranking[:30]:
        words = ",".join(str(w) for w in row["best_W"])
        lines.append(
            f"| {row['rank']} | {row['block1_hw']} | {row['bridge_score']} | "
            f"{row['best_hw_min']} | {row['best_hw_mean']} | {row['late_best_hw']} | "
            f"{row['cleared_max']} | {row['cleared_mean']} | {row['new_mean']} | "
            f"{row['cg_best_min']} | {row['best_rounds']} | `{words}` |"
        )

    lines += [
        "",
        "## Best Observations By Round",
        "",
        "| Rounds | Rank | Best HW | Cleared | New | c/g HW | W57..W60 |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for rounds in sorted({obs["rounds"] for obs in observations}):
        subset = [obs for obs in observations if obs["rounds"] == rounds]
        subset.sort(key=lambda x: (x["best_hw"], -x["cleared_total"], x["new_total"], x["rank"]))
        for obs in subset[:5]:
            words = ",".join(str(w) for w in obs["W"])
            lines.append(
                f"| {rounds} | {obs['rank']} | {obs['best_hw']} | "
                f"{obs['cleared_total']} | {obs['new_total']} | {obs['cg_best_hw']} | `{words}` |"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--residuals", required=True)
    ap.add_argument("--csv-glob", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    residuals = load_residuals(Path(args.residuals))
    observations = []
    for raw_path in sorted(glob.glob(args.csv_glob)):
        path = Path(raw_path)
        with path.open("r", encoding="utf-8", newline="") as fh:
            for raw in csv.DictReader(fh):
                observations.append(analyze_row(residuals[int(raw["record"])], raw, path))

    ranking = summarize(observations)
    payload = {
        "description": "absorber profile analysis",
        "residuals": args.residuals,
        "csv_glob": args.csv_glob,
        "ranking": ranking,
        "observations": observations,
    }
    Path(args.out_json).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_md(Path(args.out_md), ranking, observations)
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
