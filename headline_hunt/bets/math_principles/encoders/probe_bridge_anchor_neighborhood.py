#!/usr/bin/env python3
"""
probe_bridge_anchor_neighborhood.py - Deterministic local check around F375 bridge.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from headline_hunt.bets.block2_wang.encoders.search_schedule_space import (  # noqa: E402
    atlas_evaluate,
    atlas_score,
    parse_active_words,
)
from headline_hunt.bets.math_principles.encoders.continue_atlas_from_seed import (  # noqa: E402
    compact_candidate,
    from_hex_words,
    repo_path,
)
from headline_hunt.bets.math_principles.encoders.continue_atlas_kernel_safe import (  # noqa: E402
    diff_summary,
    is_kernel_pair,
)
from headline_hunt.bets.math_principles.encoders.probe_atlas_neighborhood import (  # noqa: E402
    apply_move,
    move_positions,
)


DEFAULT_SOURCE = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F375_kernel_safe_bridge_anchor_continuation.json"
)
DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F376_bridge_anchor_neighborhood.json"
)


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def selected_anchor(source: dict[str, Any], label: str) -> dict[str, Any]:
    for row in source.get("anchor_runs", []):
        if row["label"] == label:
            return row
    raise ValueError(f"source has no anchor label {label!r}")


def chart_penalty(row: dict[str, Any]) -> int:
    return 0 if row["rec"]["chart_match"] else 1


def rank_default(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        row["default_score"],
        rec["a57_xor_hw"],
        chart_penalty(row),
        rec["D61_hw"],
        rec["tail63_state_diff_hw"],
    )


def rank_profile(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        row["profile_score"],
        rec["a57_xor_hw"],
        chart_penalty(row),
        rec["D61_hw"],
        rec["tail63_state_diff_hw"],
    )


def rank_guard(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        rec["a57_xor_hw"],
        chart_penalty(row),
        rec["D61_hw"],
        row["default_score"],
    )


def rank_d61(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        rec["D61_hw"],
        chart_penalty(row),
        rec["a57_xor_hw"],
        row["default_score"],
    )


def rank_target(row: dict[str, Any], seed: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    seed_rec = seed["rec"]
    return (
        chart_penalty(row),
        max(0, rec["a57_xor_hw"] - seed_rec["a57_xor_hw"]),
        max(0, rec["D61_hw"] - seed_rec["D61_hw"]),
        rec["D61_hw"],
        row["default_score"],
    )


def move_label(move: tuple[Any, ...]) -> dict[str, Any]:
    row = {"mode": move[0], "word": move[1], "bit": move[2]}
    if len(move) > 3:
        row["sign"] = move[3]
    return row


def candidate_row(
    M1: list[int],
    M2: list[int],
    move: tuple[Any, ...] | None,
    default_kwargs: dict[str, float],
    profile_kwargs: dict[str, float],
) -> dict[str, Any]:
    rec = atlas_evaluate(M1, M2)
    row = compact_candidate(M1, M2, rec, atlas_score(rec, **default_kwargs))
    row["default_score"] = row["score"]
    row["profile_score"] = round(atlas_score(rec, **profile_kwargs), 6)
    row["move"] = move_label(move) if move else None
    return row


def strict_benchmark_hit(row: dict[str, Any], base: dict[str, Any]) -> bool:
    rec = row["rec"]
    base_rec = base["rec"]
    return (
        row["default_score"] < base["score"]
        and rec["chart_match"]
        and rec["a57_xor_hw"] <= base_rec["a57_xor_hw"]
        and rec["D61_hw"] <= base_rec["D61_hw"]
    )


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    if payload["strict_benchmark_hit_count"]:
        return (
            "bridge_neighborhood_found_strict_benchmark_hit",
            "Promote the strict benchmark hit to continuation.",
        )
    if payload["target_repair_count"]:
        return (
            "bridge_neighborhood_repairs_D61_with_guard_chart",
            "Promote the best target-repair neighbor as the next bridge point.",
        )
    if payload["d61_lower_count"] or payload["guard_lower_count"]:
        return (
            "bridge_neighborhood_coordinate_descent_only",
            "Coordinates move locally, but not while preserving the repaired guard/chart target.",
        )
    return (
        "bridge_neighborhood_no_coordinate_descent",
        "No strict-kernel one-move neighbor improves default score, profile score, guard, or D61.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    seed = payload["seed"]
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: BRIDGE_ANCHOR_NEIGHBORHOOD",
        "---",
        "",
        "# F376: bridge-anchor deterministic neighborhood",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Source: `{payload['source']}` label `{payload['label']}` candidate `{payload['candidate']}`.",
        f"Seed: default score {seed['default_score']} profile score {seed['profile_score']} a57={seed['rec']['a57_xor_hw']} D61={seed['rec']['D61_hw']} chart=`{','.join(seed['rec']['chart_top2'])}`.",
        f"Scanned valid moves: {payload['valid_moves']}; invalid rejected: {payload['invalid_moves']}.",
        "",
        "| Candidate | Default score | Profile score | a57 | D61 | Chart | Move |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for label in ("best_default", "best_profile", "best_guard", "best_d61", "best_target"):
        row = payload[label]
        lines.append(
            f"| `{label}` | {row['default_score']} | {row['profile_score']} | "
            f"{row['rec']['a57_xor_hw']} | {row['rec']['D61_hw']} | "
            f"`{','.join(row['rec']['chart_top2'])}` | `{row['move']}` |"
        )
    lines.extend([
        "",
        "## Counts",
        "",
        f"- default-score improvements: {payload['default_improve_count']}",
        f"- profile-score improvements: {payload['profile_improve_count']}",
        f"- guard-lowering moves: {payload['guard_lower_count']}",
        f"- D61-lowering moves: {payload['d61_lower_count']}",
        f"- D61-lowering with guard/chart preserved: {payload['target_repair_count']}",
        f"- strict benchmark hits: {payload['strict_benchmark_hit_count']}",
        "",
        "## Decision",
        "",
        payload["decision"],
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", nargs="?", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--label", default="best_d61")
    ap.add_argument("--candidate", default="best_profile")
    ap.add_argument("--active-words", default="0-15")
    ap.add_argument("--modes", default="common_xor,common_add")
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    source = read_json(args.source)
    kernel_bit = int(source.get("kernel_bit", 31))
    anchor = selected_anchor(source, args.label)
    if args.candidate not in anchor:
        raise ValueError(f"anchor has no candidate {args.candidate!r}")
    seed_src = anchor[args.candidate]
    M1 = from_hex_words(seed_src["M1"])
    M2 = from_hex_words(seed_src["M2"])
    if not is_kernel_pair(M1, M2, kernel_bit):
        raise ValueError(f"seed drifted: {diff_summary(M1, M2)}")
    default_kwargs = source.get("default_score_kwargs") or {
        "atlas_alpha": 4.0,
        "atlas_beta": 1.0,
        "atlas_gamma": 8.0,
        "atlas_delta": 0.05,
    }
    profile_kwargs = anchor["profile"]["score_kwargs"]
    seed = candidate_row(M1, M2, None, default_kwargs, profile_kwargs)
    active_words = parse_active_words(args.active_words)
    modes = [part.strip() for part in args.modes.split(",") if part.strip()]
    if any(mode not in {"common_xor", "common_add"} for mode in modes):
        raise SystemExit("bridge neighborhood only accepts common_xor/common_add modes")
    moves = [move for mode in modes for move in move_positions(active_words, mode)]
    base = source["base"]

    t0 = time.time()
    candidates = []
    invalid = 0
    for move in moves:
        cand_M1, cand_M2 = apply_move(M1, M2, [move])
        if not is_kernel_pair(cand_M1, cand_M2, kernel_bit):
            invalid += 1
            continue
        candidates.append(candidate_row(cand_M1, cand_M2, move, default_kwargs, profile_kwargs))

    seed_rec = seed["rec"]
    payload = {
        "report_id": "F376",
        "source": repo_path(args.source),
        "label": args.label,
        "candidate": args.candidate,
        "kernel_bit": kernel_bit,
        "active_words": active_words,
        "modes": modes,
        "default_score_kwargs": default_kwargs,
        "profile": anchor["profile"],
        "seed": seed,
        "valid_moves": len(candidates),
        "invalid_moves": invalid,
        "default_improve_count": sum(1 for row in candidates if row["default_score"] < seed["default_score"]),
        "profile_improve_count": sum(1 for row in candidates if row["profile_score"] < seed["profile_score"]),
        "guard_lower_count": sum(1 for row in candidates if row["rec"]["a57_xor_hw"] < seed_rec["a57_xor_hw"]),
        "d61_lower_count": sum(1 for row in candidates if row["rec"]["D61_hw"] < seed_rec["D61_hw"]),
        "target_repair_count": sum(
            1 for row in candidates
            if row["rec"]["chart_match"]
            and row["rec"]["a57_xor_hw"] <= seed_rec["a57_xor_hw"]
            and row["rec"]["D61_hw"] < seed_rec["D61_hw"]
        ),
        "strict_benchmark_hit_count": sum(1 for row in candidates if strict_benchmark_hit(row, base)),
        "best_default": min(candidates, key=rank_default),
        "best_profile": min(candidates, key=rank_profile),
        "best_guard": min(candidates, key=rank_guard),
        "best_d61": min(candidates, key=rank_d61),
        "best_target": min(candidates, key=lambda row: rank_target(row, seed)),
        "top_by_default": sorted(candidates, key=rank_default)[:16],
        "top_by_profile": sorted(candidates, key=rank_profile)[:16],
        "top_by_d61": sorted(candidates, key=rank_d61)[:16],
        "wall_seconds": round(time.time() - t0, 6),
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
        "seed": payload["seed"]["rec"],
        "best_default": payload["best_default"]["rec"],
        "best_default_score": payload["best_default"]["default_score"],
        "best_profile": payload["best_profile"]["rec"],
        "best_profile_score": payload["best_profile"]["profile_score"],
        "best_target": payload["best_target"]["rec"],
        "counts": {
            "default_improve": payload["default_improve_count"],
            "profile_improve": payload["profile_improve_count"],
            "guard_lower": payload["guard_lower_count"],
            "d61_lower": payload["d61_lower_count"],
            "target_repair": payload["target_repair_count"],
            "strict_hits": payload["strict_benchmark_hit_count"],
            "valid": payload["valid_moves"],
            "invalid": payload["invalid_moves"],
        },
        "wall_seconds": payload["wall_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
