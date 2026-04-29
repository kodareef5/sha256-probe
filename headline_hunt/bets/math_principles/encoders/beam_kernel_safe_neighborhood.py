#!/usr/bin/env python3
"""
beam_kernel_safe_neighborhood.py - Multi-move strict-kernel common-mode beam.
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
    / "headline_hunt/bets/math_principles/results/20260429_F370_kernel_safe_descendant_continuation.json"
)
DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F372_kernel_safe_beam_probe.json"
)


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def selected_row(source: dict[str, Any], label: str) -> dict[str, Any]:
    rows = source.get("descendant_runs") or source.get("representative_runs", [])
    for row in rows:
        if row["label"] == label:
            return row
    raise ValueError(f"source has no run label {label!r}")


def state_key(M1: list[int], M2: list[int]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    return tuple(M1), tuple(M2)


def chart_penalty(rec: dict[str, Any]) -> int:
    return 0 if rec["chart_match"] else 1


def rank_score(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        row["score"],
        rec["a57_xor_hw"],
        chart_penalty(rec),
        rec["D61_hw"],
        rec["tail63_state_diff_hw"],
    )


def rank_beam(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        row["score"],
        rec["a57_xor_hw"],
        chart_penalty(rec),
        rec["D61_hw"],
        len(row["moves"]),
    )


def rank_guard(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        rec["a57_xor_hw"],
        chart_penalty(rec),
        rec["D61_hw"],
        row["score"],
    )


def rank_d61(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        rec["D61_hw"],
        chart_penalty(rec),
        rec["a57_xor_hw"],
        row["score"],
    )


def move_label(move: tuple[Any, ...]) -> dict[str, Any]:
    row = {"mode": move[0], "word": move[1], "bit": move[2]}
    if len(move) > 3:
        row["sign"] = move[3]
    return row


def candidate_row(
    M1: list[int],
    M2: list[int],
    rec: dict[str, Any],
    score: float,
    moves: list[tuple[Any, ...]],
) -> dict[str, Any]:
    return {
        "score": round(score, 6),
        "rec": {
            "a57_xor_hw": rec["a57_xor_hw"],
            "D61_hw": rec["D61_hw"],
            "chart_top2": list(rec["chart_top2"]),
            "chart_match": tuple(rec["chart_top2"]) in {("dh", "dCh"), ("dCh", "dh")},
            "tail63_state_diff_hw": rec["tail63_state_diff_hw"],
        },
        "moves": [move_label(move) for move in moves],
        "M1": [f"0x{word:08x}" for word in M1],
        "M2": [f"0x{word:08x}" for word in M2],
    }


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    base = payload["base"]
    best = payload["best_score"]
    if best["score"] < base["score"]:
        return (
            "kernel_beam_found_descent",
            "Promote the best beam candidate to strict-kernel continuation.",
        )
    guard_improved = payload["best_guard"]["rec"]["a57_xor_hw"] < base["rec"]["a57_xor_hw"]
    d61_improved = payload["best_d61"]["rec"]["D61_hw"] < base["rec"]["D61_hw"]
    if guard_improved and d61_improved:
        return (
            "kernel_beam_found_split_guard_D61_descent",
            "Guard and D61 both move under strict kernel, but on separate higher-score branches.",
        )
    if guard_improved:
        return (
            "kernel_beam_found_guard_descent_only",
            "Guard moves under strict kernel, but not with scalar atlas descent.",
        )
    if d61_improved:
        return (
            "kernel_beam_found_D61_descent_only",
            "D61 moves under strict kernel, but not with scalar atlas descent.",
        )
    return (
        "kernel_beam_no_descent",
        "No strict-kernel multi-move beam candidate improves score, guard, or D61.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    base = payload["base"]
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: KERNEL_SAFE_BEAM_PROBE",
        "---",
        "",
        "# F372: kernel-safe beam probe",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Source: `{payload['source']}` label `{payload['label']}`.",
        f"Base score: {base['score']} a57={base['rec']['a57_xor_hw']} D61={base['rec']['D61_hw']} chart=`{','.join(base['rec']['chart_top2'])}`.",
        f"Evaluated: {payload['evaluated']}; invalid rejected: {payload['invalid_moves']}.",
        "",
        "| Candidate | Score | a57 | D61 | Chart | Depth |",
        "|---|---:|---:|---:|---|---:|",
    ]
    for label in ("best_score", "best_guard", "best_d61"):
        row = payload[label]
        lines.append(
            f"| `{label}` | {row['score']} | {row['rec']['a57_xor_hw']} | "
            f"{row['rec']['D61_hw']} | `{','.join(row['rec']['chart_top2'])}` | "
            f"{len(row['moves'])} |"
        )
    lines.extend([
        "",
        "## Depth Summary",
        "",
        "| Depth | Generated | Invalid | Beam best score | Beam best a57 | Beam best D61 |",
        "|---:|---:|---:|---:|---:|---:|",
    ])
    for row in payload["depth_summary"]:
        best = row["best"]
        lines.append(
            f"| {row['depth']} | {row['generated']} | {row['invalid']} | "
            f"{best['score']} | {best['rec']['a57_xor_hw']} | {best['rec']['D61_hw']} |"
        )
    lines.extend([
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
    ap.add_argument("--label", default="best_D61")
    ap.add_argument("--active-words", default="0-15")
    ap.add_argument("--modes", default="common_xor,common_add")
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--beam-width", type=int, default=32)
    ap.add_argument("--alpha", type=float, default=4.0)
    ap.add_argument("--beta", type=float, default=1.0)
    ap.add_argument("--gamma", type=float, default=8.0)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    if args.depth < 1:
        raise SystemExit("--depth must be positive")
    source = read_json(args.source)
    kernel_bit = int(source.get("kernel_bit", 31))
    row = selected_row(source, args.label)
    seed = row["best"]
    base_M1 = from_hex_words(seed["M1"])
    base_M2 = from_hex_words(seed["M2"])
    if not is_kernel_pair(base_M1, base_M2, kernel_bit):
        raise ValueError("source seed is not kernel-preserving")
    active_words = parse_active_words(args.active_words)
    modes = [part.strip() for part in args.modes.split(",") if part.strip()]
    if any(mode not in {"common_xor", "common_add"} for mode in modes):
        raise SystemExit("kernel-safe beam only accepts common modes")
    all_moves = [move for mode in modes for move in move_positions(active_words, mode)]
    score_kwargs = {
        "atlas_alpha": args.alpha,
        "atlas_beta": args.beta,
        "atlas_gamma": args.gamma,
        "atlas_delta": args.delta,
    }
    base_rec = atlas_evaluate(base_M1, base_M2)
    base_score = atlas_score(base_rec, **score_kwargs)
    base = candidate_row(base_M1, base_M2, base_rec, base_score, [])
    t0 = time.time()
    beam = [(base_M1, base_M2, [])]
    seen = {state_key(base_M1, base_M2)}
    all_candidates = [base]
    invalid_total = 0
    evaluated = 0
    depth_summary = []
    for depth in range(1, args.depth + 1):
        generated = []
        invalid = 0
        for M1, M2, moves_so_far in beam:
            for move in all_moves:
                cand_M1, cand_M2 = apply_move(M1, M2, [move])
                if not is_kernel_pair(cand_M1, cand_M2, kernel_bit):
                    invalid += 1
                    continue
                key = state_key(cand_M1, cand_M2)
                if key in seen:
                    continue
                seen.add(key)
                rec = atlas_evaluate(cand_M1, cand_M2)
                score = atlas_score(rec, **score_kwargs)
                moves = moves_so_far + [move]
                row = candidate_row(cand_M1, cand_M2, rec, score, moves)
                generated.append((cand_M1, cand_M2, moves, row))
                all_candidates.append(row)
        evaluated += len(generated)
        invalid_total += invalid
        generated.sort(key=lambda item: rank_beam(item[3]))
        beam = [(M1, M2, moves) for M1, M2, moves, _row in generated[:args.beam_width]]
        best = generated[0][3] if generated else base
        depth_summary.append({
            "depth": depth,
            "generated": len(generated),
            "invalid": invalid,
            "best": best,
        })
        if not generated:
            break

    best_score = min(all_candidates, key=rank_score)
    best_guard = min(all_candidates, key=rank_guard)
    best_d61 = min(all_candidates, key=rank_d61)
    payload = {
        "report_id": "F372",
        "source": repo_path(args.source),
        "label": args.label,
        "kernel_bit": kernel_bit,
        "active_words": active_words,
        "modes": modes,
        "depth": args.depth,
        "beam_width": args.beam_width,
        "score_kwargs": score_kwargs,
        "base": base,
        "evaluated": evaluated,
        "invalid_moves": invalid_total,
        "candidate_count": len(all_candidates),
        "best_score": best_score,
        "best_guard": best_guard,
        "best_d61": best_d61,
        "top_by_score": sorted(all_candidates, key=rank_score)[:16],
        "top_by_guard": sorted(all_candidates, key=rank_guard)[:16],
        "top_by_d61": sorted(all_candidates, key=rank_d61)[:16],
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
        "base": payload["base"]["rec"],
        "best_score": payload["best_score"]["rec"],
        "best_score_value": payload["best_score"]["score"],
        "best_guard": payload["best_guard"]["rec"],
        "best_guard_score": payload["best_guard"]["score"],
        "best_d61": payload["best_d61"]["rec"],
        "best_d61_score": payload["best_d61"]["score"],
        "evaluated": payload["evaluated"],
        "invalid": payload["invalid_moves"],
        "wall_seconds": payload["wall_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
