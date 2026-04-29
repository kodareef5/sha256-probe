#!/usr/bin/env python3
"""
search_kernel_safe_junction.py - Targeted strict-kernel repair from F372 branches.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Callable


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
    compact_candidate,
    move_positions,
)


DEFAULT_SOURCE = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F372_kernel_safe_beam_probe.json"
)
DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F373_kernel_safe_junction_search.json"
)


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def state_key(M1: list[int], M2: list[int]) -> tuple[tuple[int, ...], tuple[int, ...]]:
    return tuple(M1), tuple(M2)


def move_tuple(row: dict[str, Any]) -> tuple[Any, ...]:
    if row["mode"] == "common_add":
        return (row["mode"], row["word"], row["bit"], row["sign"])
    return (row["mode"], row["word"], row["bit"])


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


def target_violation(row: dict[str, Any], target: dict[str, Any]) -> tuple[int, int, int]:
    rec = row["rec"]
    return (
        chart_penalty(rec) if target["require_chart"] else 0,
        max(0, rec["a57_xor_hw"] - target["target_a57"]),
        max(0, rec["D61_hw"] - target["target_D61"]),
    )


def rank_target(row: dict[str, Any], target: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        *target_violation(row, target),
        row["score"],
        rec["tail63_state_diff_hw"],
        len(row["flips"]),
    )


def target_hit(row: dict[str, Any], target: dict[str, Any]) -> bool:
    return target_violation(row, target) == (0, 0, 0)


def strict_benchmark_hit(row: dict[str, Any], base: dict[str, Any]) -> bool:
    rec = row["rec"]
    base_rec = base["rec"]
    return (
        row["score"] < base["score"]
        and rec["chart_match"]
        and rec["a57_xor_hw"] <= base_rec["a57_xor_hw"]
        and rec["D61_hw"] <= base_rec["D61_hw"]
    )


def keep_top(
    top: list[dict[str, Any]],
    row: dict[str, Any],
    key: Callable[[dict[str, Any]], tuple[Any, ...]],
    limit: int,
) -> None:
    top.append(row)
    top.sort(key=key)
    if len(top) > limit:
        top.pop()


def annotate(row: dict[str, Any], target: dict[str, Any], repair_depth: int) -> dict[str, Any]:
    out = dict(row)
    out["repair_depth"] = repair_depth
    out["target_violation"] = list(target_violation(row, target))
    return out


def compact_from_words(
    M1: list[int],
    M2: list[int],
    flips: list[tuple[Any, ...]],
    base_score: float,
    base_rec: dict[str, Any],
    score_kwargs: dict[str, float],
) -> dict[str, Any]:
    rec = atlas_evaluate(M1, M2)
    score = atlas_score(rec, **score_kwargs)
    return compact_candidate(M1, M2, rec, score, flips, base_score, base_rec)


def branch_seed(
    source: dict[str, Any],
    branch: str,
    base_score: float,
    base_rec: dict[str, Any],
    score_kwargs: dict[str, float],
) -> tuple[list[int], list[int], list[tuple[Any, ...]], dict[str, Any]]:
    src = source[branch]
    M1 = from_hex_words(src["M1"])
    M2 = from_hex_words(src["M2"])
    moves = [move_tuple(move) for move in src["moves"]]
    row = compact_from_words(M1, M2, moves, base_score, base_rec, score_kwargs)
    return M1, M2, moves, row


def search_branch(
    source: dict[str, Any],
    branch: str,
    target: dict[str, Any],
    all_moves: list[tuple[Any, ...]],
    kernel_bit: int,
    depth: int,
    beam_width: int,
    top: int,
    base: dict[str, Any],
    base_score: float,
    base_rec: dict[str, Any],
    score_kwargs: dict[str, float],
    forbidden_states: set[tuple[tuple[int, ...], tuple[int, ...]]],
) -> dict[str, Any]:
    seed_M1, seed_M2, seed_moves, seed = branch_seed(
        source,
        branch,
        base_score,
        base_rec,
        score_kwargs,
    )
    if not is_kernel_pair(seed_M1, seed_M2, kernel_bit):
        raise ValueError(f"{branch} seed is not kernel-preserving")

    t0 = time.time()
    seed_row = annotate(seed, target, 0)
    beam = [(seed_M1, seed_M2, [])]
    seen = {state_key(seed_M1, seed_M2)}
    evaluated = 0
    invalid = 0
    forbidden_skips = 0
    target_hit_count = 1 if target_hit(seed_row, target) else 0
    benchmark_hit_count = 1 if strict_benchmark_hit(seed_row, base) else 0
    top_by_target = [seed_row]
    top_by_score = [seed_row]
    top_by_guard = [seed_row]
    top_by_d61 = [seed_row]
    top_hits: list[dict[str, Any]] = [seed_row] if target_hit(seed_row, target) else []
    depth_summary = []

    for current_depth in range(1, depth + 1):
        generated = []
        depth_invalid = 0
        for M1, M2, repair_moves in beam:
            for move in all_moves:
                cand_M1, cand_M2 = apply_move(M1, M2, [move])
                if not is_kernel_pair(cand_M1, cand_M2, kernel_bit):
                    depth_invalid += 1
                    continue
                key = state_key(cand_M1, cand_M2)
                if key in forbidden_states:
                    forbidden_skips += 1
                    continue
                if key in seen:
                    continue
                seen.add(key)
                next_repairs = repair_moves + [move]
                row = compact_from_words(
                    cand_M1,
                    cand_M2,
                    seed_moves + next_repairs,
                    base_score,
                    base_rec,
                    score_kwargs,
                )
                annotated = annotate(row, target, len(next_repairs))
                generated.append((cand_M1, cand_M2, next_repairs, annotated))
                evaluated += 1
                if target_hit(annotated, target):
                    target_hit_count += 1
                    keep_top(top_hits, annotated, rank_score, top)
                if strict_benchmark_hit(annotated, base):
                    benchmark_hit_count += 1
                keep_top(top_by_target, annotated, lambda item: rank_target(item, target), top)
                keep_top(top_by_score, annotated, rank_score, top)
                keep_top(top_by_guard, annotated, rank_guard, top)
                keep_top(top_by_d61, annotated, rank_d61, top)
        invalid += depth_invalid
        generated.sort(key=lambda item: rank_target(item[3], target))
        beam = [(M1, M2, repairs) for M1, M2, repairs, _row in generated[:beam_width]]
        best = generated[0][3] if generated else top_by_target[0]
        depth_summary.append({
            "depth": current_depth,
            "generated": len(generated),
            "invalid": depth_invalid,
            "best_target": best,
        })
        if not generated:
            break

    seed_violation = target_violation(seed_row, target)
    best_violation = target_violation(top_by_target[0], target)
    return {
        "branch": branch,
        "target": target,
        "seed": seed_row,
        "seed_target_violation": list(seed_violation),
        "best_target_violation": list(best_violation),
        "reduced_violation": best_violation < seed_violation,
        "evaluated": evaluated,
        "invalid_moves": invalid,
        "forbidden_skips": forbidden_skips,
        "target_hit_count": target_hit_count,
        "strict_benchmark_hit_count": benchmark_hit_count,
        "best_target": top_by_target[0],
        "best_score": top_by_score[0],
        "best_guard": top_by_guard[0],
        "best_d61": top_by_d61[0],
        "top_by_target": top_by_target,
        "top_by_score": top_by_score,
        "top_by_guard": top_by_guard,
        "top_by_d61": top_by_d61,
        "top_hits": top_hits,
        "depth_summary": depth_summary,
        "wall_seconds": round(time.time() - t0, 6),
    }


def literal_union(
    source: dict[str, Any],
    kernel_bit: int,
    base_M1: list[int],
    base_M2: list[int],
    base_score: float,
    base_rec: dict[str, Any],
    score_kwargs: dict[str, float],
) -> dict[str, Any]:
    union_moves = [move_tuple(move) for move in source["best_guard"]["moves"]]
    union_moves.extend(move_tuple(move) for move in source["best_d61"]["moves"])
    M1, M2 = apply_move(base_M1, base_M2, union_moves)
    row = compact_from_words(M1, M2, union_moves, base_score, base_rec, score_kwargs)
    row["kernel_valid"] = is_kernel_pair(M1, M2, kernel_bit)
    return row


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    if any(row["strict_benchmark_hit_count"] for row in payload["branches"]):
        return (
            "junction_found_strict_benchmark_descent",
            "Promote the best strict-benchmark hit to continuation.",
        )
    if any(row["target_hit_count"] for row in payload["branches"]):
        return (
            "junction_hits_target_without_score_descent",
            "A branch can be repaired to its target constraints, but not below the F370/F371 score floor.",
        )
    if any(row["reduced_violation"] for row in payload["branches"]):
        return (
            "junction_reduces_target_distance",
            "The repair beams move toward the target constraints but do not close them.",
        )
    return (
        "junction_no_repair_progress",
        "The F372 branch points do not repair toward each other under this strict-kernel beam.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    base = payload["base"]
    union = payload["literal_union"]
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: KERNEL_SAFE_JUNCTION_SEARCH",
        "---",
        "",
        "# F373: strict-kernel junction search",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Source: `{payload['source']}`.",
        f"Base: score {base['score']} a57={base['rec']['a57_xor_hw']} D61={base['rec']['D61_hw']} chart=`{','.join(base['rec']['chart_top2'])}`.",
        f"Literal union: score {union['score']} a57={union['rec']['a57_xor_hw']} D61={union['rec']['D61_hw']} chart=`{','.join(union['rec']['chart_top2'])}` kernel={union['kernel_valid']}.",
        "",
        "| Branch | Target | Evaluated | Hits | Best target score | a57 | D61 | Chart | Violation |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in payload["branches"]:
        best = row["best_target"]
        target = row["target"]
        lines.append(
            f"| `{row['branch']}` | `{target['name']}` | {row['evaluated']} | "
            f"{row['target_hit_count']} | {best['score']} | {best['rec']['a57_xor_hw']} | "
            f"{best['rec']['D61_hw']} | `{','.join(best['rec']['chart_top2'])}` | "
            f"`{best['target_violation']}` |"
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
    ap.add_argument("--active-words", default="0-15")
    ap.add_argument("--modes", default="common_xor,common_add")
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--beam-width", type=int, default=48)
    ap.add_argument("--top", type=int, default=12)
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
    active_words = parse_active_words(args.active_words)
    modes = [part.strip() for part in args.modes.split(",") if part.strip()]
    if any(mode not in {"common_xor", "common_add"} for mode in modes):
        raise SystemExit("kernel-safe junction search only accepts common modes")
    all_moves = [move for mode in modes for move in move_positions(active_words, mode)]
    score_kwargs = {
        "atlas_alpha": args.alpha,
        "atlas_beta": args.beta,
        "atlas_gamma": args.gamma,
        "atlas_delta": args.delta,
    }

    base_M1 = from_hex_words(source["base"]["M1"])
    base_M2 = from_hex_words(source["base"]["M2"])
    if not is_kernel_pair(base_M1, base_M2, kernel_bit):
        raise ValueError("F372 base is not kernel-preserving")
    base_rec = atlas_evaluate(base_M1, base_M2)
    base_score = atlas_score(base_rec, **score_kwargs)
    base = compact_candidate(base_M1, base_M2, base_rec, base_score, [], base_score, base_rec)
    branch_targets = [
        {
            "name": "guard_branch_preserve_guard_repair_D61",
            "branch": "best_guard",
            "require_chart": True,
            "target_a57": source["best_guard"]["rec"]["a57_xor_hw"],
            "target_D61": base["rec"]["D61_hw"],
        },
        {
            "name": "D61_branch_guard_repair_preserve_D61",
            "branch": "best_d61",
            "require_chart": True,
            "target_a57": base["rec"]["a57_xor_hw"],
            "target_D61": source["best_d61"]["rec"]["D61_hw"],
        },
    ]
    t0 = time.time()
    forbidden_states = {state_key(base_M1, base_M2)}
    branches = [
        search_branch(
            source,
            target["branch"],
            target,
            all_moves,
            kernel_bit,
            args.depth,
            args.beam_width,
            args.top,
            base,
            base_score,
            base_rec,
            score_kwargs,
            forbidden_states,
        )
        for target in branch_targets
    ]
    union = literal_union(source, kernel_bit, base_M1, base_M2, base_score, base_rec, score_kwargs)
    payload = {
        "report_id": "F373",
        "source": repo_path(args.source),
        "kernel_bit": kernel_bit,
        "active_words": active_words,
        "modes": modes,
        "depth": args.depth,
        "beam_width": args.beam_width,
        "score_kwargs": score_kwargs,
        "base": base,
        "literal_union": union,
        "branches": branches,
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
        "union": payload["literal_union"]["rec"],
        "branches": [
            {
                "branch": row["branch"],
                "target": row["target"]["name"],
                "evaluated": row["evaluated"],
                "hits": row["target_hit_count"],
                "seed_violation": row["seed_target_violation"],
                "best_violation": row["best_target_violation"],
                "best_target": row["best_target"]["rec"],
                "best_target_score": row["best_target"]["score"],
            }
            for row in payload["branches"]
        ],
        "wall_seconds": payload["wall_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
