#!/usr/bin/env python3
"""
beam_f322_kernel_safe_depth2.py - Targeted depth-2 strict-kernel F322 probe.
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
    is_kernel_pair,
)
from headline_hunt.bets.math_principles.encoders.probe_atlas_neighborhood import (  # noqa: E402
    apply_move,
    move_positions,
)


DEFAULT_SOURCE = (
    REPO
    / "headline_hunt/bets/block2_wang/results/search_artifacts/20260429_F336_kernel_safe_depth1_from_F322.json"
)
DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F378_f322_kernel_safe_depth2_beam.json"
)
DEFAULT_SCORE_KWARGS = {
    "atlas_alpha": 4.0,
    "atlas_beta": 1.0,
    "atlas_gamma": 8.0,
    "atlas_delta": 0.05,
}


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def state_key(M1: list[int], M2: list[int]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    return tuple(M1), tuple(M2)


def chart_penalty(row: dict[str, Any]) -> int:
    return 0 if row["rec"]["chart_match"] else 1


def move_label(move: tuple[Any, ...]) -> dict[str, Any]:
    row = {"mode": move[0], "word": move[1], "bit": move[2]}
    if len(move) > 3:
        row["sign"] = move[3]
    return row


def candidate_row(
    M1: list[int],
    M2: list[int],
    moves: list[tuple[Any, ...]],
    score_kwargs: dict[str, float],
) -> dict[str, Any]:
    rec = atlas_evaluate(M1, M2)
    score = atlas_score(rec, **score_kwargs)
    row = compact_candidate(M1, M2, rec, score)
    row["moves"] = [move_label(move) for move in moves]
    row["depth"] = len(moves)
    return row


def rank_score(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        row["score"],
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
        row["score"],
    )


def rank_d61(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        rec["D61_hw"],
        chart_penalty(row),
        rec["a57_xor_hw"],
        row["score"],
    )


def rank_target(row: dict[str, Any], base: dict[str, Any], target_d61: int) -> tuple[Any, ...]:
    rec = row["rec"]
    base_rec = base["rec"]
    return (
        chart_penalty(row),
        max(0, rec["a57_xor_hw"] - base_rec["a57_xor_hw"]),
        max(0, rec["D61_hw"] - target_d61),
        rec["D61_hw"],
        row["score"],
    )


def keep_top(top: list[dict[str, Any]], row: dict[str, Any], key, limit: int) -> None:
    top.append(row)
    top.sort(key=key)
    if len(top) > limit:
        top.pop()


def strict_bridge_hit(row: dict[str, Any], base: dict[str, Any], target_d61: int) -> bool:
    rec = row["rec"]
    base_rec = base["rec"]
    return (
        rec["chart_match"]
        and rec["a57_xor_hw"] <= base_rec["a57_xor_hw"]
        and rec["D61_hw"] <= target_d61
    )


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    if payload["score_improve_count"]:
        return (
            "f322_depth2_beam_found_score_descent",
            "Promote the score-improving F322 depth-2 candidate.",
        )
    if payload["strict_bridge_hit_count"]:
        return (
            "f322_depth2_beam_found_D61_bridge",
            "Promote the chart/guard-preserving D61 bridge from the F322 basin.",
        )
    if payload["guard_lower_count"] or payload["d61_lower_count"]:
        return (
            "f322_depth2_beam_coordinate_descent_only",
            "Depth-2 beam moves coordinates but does not combine them into the target.",
        )
    return (
        "f322_depth2_beam_no_descent",
        "No score, guard, D61, or target descent appears in this bounded F322 depth-2 beam.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    base = payload["base"]
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: F322_KERNEL_SAFE_DEPTH2_BEAM",
        "---",
        "",
        "# F378: F322 strict-kernel depth-2 beam",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Source: `{payload['source']}`.",
        f"Base: score {base['score']} a57={base['rec']['a57_xor_hw']} D61={base['rec']['D61_hw']} chart=`{','.join(base['rec']['chart_top2'])}`.",
        f"Evaluated: {payload['evaluated']}; invalid rejected: {payload['invalid_moves']}; target D61={payload['target_D61']}.",
        "",
        "| Candidate | Score | a57 | D61 | Chart | Depth |",
        "|---|---:|---:|---:|---|---:|",
    ]
    for label in ("best_score", "best_target", "best_guard", "best_d61"):
        row = payload[label]
        lines.append(
            f"| `{label}` | {row['score']} | {row['rec']['a57_xor_hw']} | "
            f"{row['rec']['D61_hw']} | `{','.join(row['rec']['chart_top2'])}` | {row['depth']} |"
        )
    lines.extend([
        "",
        "## Counts",
        "",
        f"- score improvements: {payload['score_improve_count']}",
        f"- guard-lowering candidates: {payload['guard_lower_count']}",
        f"- D61-lowering candidates: {payload['d61_lower_count']}",
        f"- chart/guard-preserving D61 target hits: {payload['strict_bridge_hit_count']}",
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
    ap.add_argument("--active-words", default="0-15")
    ap.add_argument("--modes", default="common_xor,common_add")
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--beam-width", type=int, default=64)
    ap.add_argument("--top", type=int, default=16)
    ap.add_argument("--target-D61", type=int, default=8)
    ap.add_argument("--kernel-bit", type=int, default=31)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    if args.depth < 1:
        raise SystemExit("--depth must be positive")
    source = read_json(args.source)
    active_words = parse_active_words(args.active_words)
    modes = [part.strip() for part in args.modes.split(",") if part.strip()]
    if any(mode not in {"common_xor", "common_add"} for mode in modes):
        raise SystemExit("F322 depth-2 beam only accepts common modes")
    all_moves = [move for mode in modes for move in move_positions(active_words, mode)]
    base_M1 = from_hex_words(source["base"]["M1"])
    base_M2 = from_hex_words(source["base"]["M2"])
    if not is_kernel_pair(base_M1, base_M2, args.kernel_bit):
        raise ValueError("F336 base is not kernel-preserving")
    base = candidate_row(base_M1, base_M2, [], DEFAULT_SCORE_KWARGS)
    t0 = time.time()
    beam = [(base_M1, base_M2, [])]
    seen = {state_key(base_M1, base_M2)}
    top_by_score: list[dict[str, Any]] = []
    top_by_target: list[dict[str, Any]] = []
    top_by_guard: list[dict[str, Any]] = []
    top_by_d61: list[dict[str, Any]] = []
    score_improve = 0
    guard_lower = 0
    d61_lower = 0
    strict_hits = 0
    invalid = 0
    evaluated = 0
    depth_summary = []
    for depth in range(1, args.depth + 1):
        generated = []
        depth_invalid = 0
        for M1, M2, moves_so_far in beam:
            for move in all_moves:
                cand_M1, cand_M2 = apply_move(M1, M2, [move])
                if not is_kernel_pair(cand_M1, cand_M2, args.kernel_bit):
                    depth_invalid += 1
                    continue
                key = state_key(cand_M1, cand_M2)
                if key in seen:
                    continue
                seen.add(key)
                moves = moves_so_far + [move]
                row = candidate_row(cand_M1, cand_M2, moves, DEFAULT_SCORE_KWARGS)
                generated.append((cand_M1, cand_M2, moves, row))
                evaluated += 1
                if row["score"] < base["score"]:
                    score_improve += 1
                if row["rec"]["a57_xor_hw"] < base["rec"]["a57_xor_hw"]:
                    guard_lower += 1
                if row["rec"]["D61_hw"] < base["rec"]["D61_hw"]:
                    d61_lower += 1
                if strict_bridge_hit(row, base, args.target_D61):
                    strict_hits += 1
                keep_top(top_by_score, row, rank_score, args.top)
                keep_top(top_by_target, row, lambda item: rank_target(item, base, args.target_D61), args.top)
                keep_top(top_by_guard, row, rank_guard, args.top)
                keep_top(top_by_d61, row, rank_d61, args.top)
        invalid += depth_invalid
        generated.sort(key=lambda item: rank_target(item[3], base, args.target_D61))
        beam = [(M1, M2, moves) for M1, M2, moves, _row in generated[:args.beam_width]]
        best = generated[0][3] if generated else None
        depth_summary.append({
            "depth": depth,
            "generated": len(generated),
            "invalid": depth_invalid,
            "beam_best": best,
        })
        if not generated:
            break

    payload = {
        "report_id": "F378",
        "source": repo_path(args.source),
        "kernel_bit": args.kernel_bit,
        "active_words": active_words,
        "modes": modes,
        "depth": args.depth,
        "beam_width": args.beam_width,
        "target_D61": args.target_D61,
        "base": base,
        "evaluated": evaluated,
        "invalid_moves": invalid,
        "score_improve_count": score_improve,
        "guard_lower_count": guard_lower,
        "d61_lower_count": d61_lower,
        "strict_bridge_hit_count": strict_hits,
        "best_score": top_by_score[0],
        "best_target": top_by_target[0],
        "best_guard": top_by_guard[0],
        "best_d61": top_by_d61[0],
        "top_by_score": top_by_score,
        "top_by_target": top_by_target,
        "top_by_d61": top_by_d61,
        "depth_summary": depth_summary,
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
        "evaluated": payload["evaluated"],
        "best_score": payload["best_score"]["rec"],
        "best_score_value": payload["best_score"]["score"],
        "best_target": payload["best_target"]["rec"],
        "best_d61": payload["best_d61"]["rec"],
        "counts": {
            "score_improve": score_improve,
            "guard_lower": guard_lower,
            "d61_lower": d61_lower,
            "strict_bridge_hits": strict_hits,
            "invalid": invalid,
        },
        "wall_seconds": payload["wall_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
