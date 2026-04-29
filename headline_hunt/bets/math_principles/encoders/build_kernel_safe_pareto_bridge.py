#!/usr/bin/env python3
"""
build_kernel_safe_pareto_bridge.py - Nontrivial strict-kernel Pareto bridge.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Callable


REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from headline_hunt.bets.block2_wang.encoders.search_schedule_space import (  # noqa: E402
    parse_active_words,
)
from headline_hunt.bets.math_principles.encoders.continue_atlas_kernel_safe import (  # noqa: E402
    is_kernel_pair,
)
from headline_hunt.bets.math_principles.encoders.probe_atlas_neighborhood import (  # noqa: E402
    apply_move,
    move_positions,
)
from headline_hunt.bets.math_principles.encoders.search_kernel_safe_junction import (  # noqa: E402
    branch_seed,
    chart_penalty,
    compact_from_words,
    from_hex_words,
    literal_union,
    rank_d61,
    rank_guard,
    rank_score,
    read_json,
    repo_path,
    state_key,
    target_violation,
)


DEFAULT_SOURCE = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F372_kernel_safe_beam_probe.json"
)
DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F374_kernel_safe_pareto_bridge.json"
)


def objective(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        chart_penalty(rec),
        rec["a57_xor_hw"],
        rec["D61_hw"],
        row["score"],
        rec["tail63_state_diff_hw"],
    )


def dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    oa = objective(a)
    ob = objective(b)
    return all(x <= y for x, y in zip(oa, ob)) and any(x < y for x, y in zip(oa, ob))


def archive_key(row: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    return tuple(row["M1"]), tuple(row["M2"])


def prune_archive(front: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    if len(front) <= limit:
        return front
    anchors = []
    keyfuncs: list[Callable[[dict[str, Any]], tuple[Any, ...]]] = [
        objective,
        rank_score,
        rank_guard,
        rank_d61,
        rank_balanced,
    ]
    seen = set()
    for keyfunc in keyfuncs:
        for row in sorted(front, key=keyfunc)[: max(4, limit // len(keyfuncs))]:
            key = archive_key(row)
            if key in seen:
                continue
            seen.add(key)
            anchors.append(row)
            if len(anchors) >= limit:
                return anchors
    for row in sorted(front, key=objective):
        key = archive_key(row)
        if key in seen:
            continue
        seen.add(key)
        anchors.append(row)
        if len(anchors) >= limit:
            return anchors
    return anchors


def add_archive(front: list[dict[str, Any]], row: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    if any(archive_key(existing) == archive_key(row) for existing in front):
        return front
    if any(dominates(existing, row) for existing in front):
        return front
    front = [existing for existing in front if not dominates(row, existing)]
    front.append(row)
    return prune_archive(front, limit)


def rank_balanced(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        chart_penalty(rec),
        max(0, rec["a57_xor_hw"] - 6),
        max(0, rec["D61_hw"] - 8),
        row["score"],
        rec["a57_xor_hw"],
        rec["D61_hw"],
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


def annotate(row: dict[str, Any], source_branch: str, repair_depth: int) -> dict[str, Any]:
    out = dict(row)
    out["source_branch"] = source_branch
    out["repair_depth"] = repair_depth
    out["pareto_objective"] = list(objective(row))
    return out


def bridge_rank(row: dict[str, Any], target: dict[str, Any]) -> tuple[Any, ...]:
    return (
        *target_violation(row, target),
        *objective(row),
    )


def scan_branch(
    source: dict[str, Any],
    target: dict[str, Any],
    all_moves: list[tuple[Any, ...]],
    kernel_bit: int,
    depth: int,
    beam_width: int,
    top: int,
    archive_limit: int,
    base: dict[str, Any],
    base_score: float,
    base_rec: dict[str, Any],
    score_kwargs: dict[str, float],
    forbidden_states: set[tuple[tuple[int, ...], tuple[int, ...]]],
) -> dict[str, Any]:
    branch = target["branch"]
    seed_M1, seed_M2, seed_moves, seed = branch_seed(
        source,
        branch,
        base_score,
        base_rec,
        score_kwargs,
    )
    if not is_kernel_pair(seed_M1, seed_M2, kernel_bit):
        raise ValueError(f"{branch} seed is not kernel-preserving")
    seed_row = annotate(seed, branch, 0)
    front = add_archive([], seed_row, archive_limit)
    top_by_score = [seed_row]
    top_by_guard = [seed_row]
    top_by_d61 = [seed_row]
    top_by_balanced = [seed_row]
    beam = [(seed_M1, seed_M2, [])]
    seen = {state_key(seed_M1, seed_M2)}
    evaluated = 0
    invalid = 0
    forbidden_skips = 0
    strict_hits = 0
    depth_summary = []
    for current_depth in range(1, depth + 1):
        generated = []
        depth_invalid = 0
        depth_forbidden = 0
        for M1, M2, repairs in beam:
            for move in all_moves:
                cand_M1, cand_M2 = apply_move(M1, M2, [move])
                if not is_kernel_pair(cand_M1, cand_M2, kernel_bit):
                    depth_invalid += 1
                    continue
                key = state_key(cand_M1, cand_M2)
                if key in forbidden_states:
                    depth_forbidden += 1
                    continue
                if key in seen:
                    continue
                seen.add(key)
                next_repairs = repairs + [move]
                row = compact_from_words(
                    cand_M1,
                    cand_M2,
                    seed_moves + next_repairs,
                    base_score,
                    base_rec,
                    score_kwargs,
                )
                row = annotate(row, branch, len(next_repairs))
                generated.append((cand_M1, cand_M2, next_repairs, row))
                evaluated += 1
                front = add_archive(front, row, archive_limit)
                keep_top(top_by_score, row, rank_score, top)
                keep_top(top_by_guard, row, rank_guard, top)
                keep_top(top_by_d61, row, rank_d61, top)
                keep_top(top_by_balanced, row, rank_balanced, top)
                if strict_benchmark_hit(row, base):
                    strict_hits += 1
        invalid += depth_invalid
        forbidden_skips += depth_forbidden
        generated.sort(key=lambda item: bridge_rank(item[3], target))
        beam = [(M1, M2, repairs) for M1, M2, repairs, _row in generated[:beam_width]]
        best = generated[0][3] if generated else top_by_balanced[0]
        depth_summary.append({
            "depth": current_depth,
            "generated": len(generated),
            "invalid": depth_invalid,
            "forbidden_skips": depth_forbidden,
            "beam_best": best,
        })
        if not generated:
            break
    return {
        "branch": branch,
        "target": target,
        "evaluated": evaluated,
        "invalid_moves": invalid,
        "forbidden_skips": forbidden_skips,
        "strict_benchmark_hit_count": strict_hits,
        "front_size": len(front),
        "front": sorted(front, key=objective),
        "top_by_score": top_by_score,
        "top_by_guard": top_by_guard,
        "top_by_d61": top_by_d61,
        "top_by_balanced": top_by_balanced,
        "depth_summary": depth_summary,
    }


def strict_benchmark_hit(row: dict[str, Any], base: dict[str, Any]) -> bool:
    rec = row["rec"]
    base_rec = base["rec"]
    return (
        row["score"] < base["score"]
        and rec["chart_match"]
        and rec["a57_xor_hw"] <= base_rec["a57_xor_hw"]
        and rec["D61_hw"] <= base_rec["D61_hw"]
    )


def merge_fronts(
    branches: list[dict[str, Any]],
    union: dict[str, Any],
    archive_limit: int,
) -> list[dict[str, Any]]:
    front: list[dict[str, Any]] = []
    if union.get("kernel_valid"):
        union_row = annotate(union, "literal_union", 0)
        front = add_archive(front, union_row, archive_limit)
    for branch in branches:
        for row in branch["front"]:
            front = add_archive(front, row, archive_limit)
    return sorted(front, key=objective)


def chart_histogram(rows: list[dict[str, Any]]) -> dict[str, int]:
    return dict(Counter(",".join(row["rec"]["chart_top2"]) for row in rows))


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    if payload["strict_benchmark_hit_count"]:
        return (
            "pareto_bridge_found_strict_benchmark_descent",
            "Promote the strict-benchmark hit as the next strict-kernel continuation seed.",
        )
    front = payload["global_front"]
    has_low_guard = any(row["rec"]["a57_xor_hw"] < payload["base"]["rec"]["a57_xor_hw"] for row in front)
    has_low_d61 = any(row["rec"]["D61_hw"] < payload["base"]["rec"]["D61_hw"] for row in front)
    has_chart_bridge = any(
        row["rec"]["chart_match"]
        and row["rec"]["a57_xor_hw"] <= payload["base"]["rec"]["a57_xor_hw"]
        for row in front
    )
    if has_low_guard and has_low_d61 and has_chart_bridge:
        return (
            "pareto_bridge_keeps_split_front",
            "Use the nontrivial front as bridge seeds; the combined strict target is still absent.",
        )
    return (
        "pareto_bridge_no_new_front",
        "The nontrivial strict-kernel bridge did not preserve enough coordinate diversity.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    base = payload["base"]
    anchors = payload["anchors"]
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: KERNEL_SAFE_PARETO_BRIDGE",
        "---",
        "",
        "# F374: strict-kernel Pareto bridge",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Source: `{payload['source']}`.",
        f"Base excluded from bridge: score {base['score']} a57={base['rec']['a57_xor_hw']} D61={base['rec']['D61_hw']} chart=`{','.join(base['rec']['chart_top2'])}`.",
        f"Evaluated: {payload['evaluated']}; global front size: {payload['global_front_size']}.",
        "",
        "| Anchor | Score | a57 | D61 | Chart | Source | Depth |",
        "|---|---:|---:|---:|---|---|---:|",
    ]
    for label in ("best_score", "best_balanced", "best_guard", "best_d61"):
        row = anchors[label]
        lines.append(
            f"| `{label}` | {row['score']} | {row['rec']['a57_xor_hw']} | "
            f"{row['rec']['D61_hw']} | `{','.join(row['rec']['chart_top2'])}` | "
            f"`{row['source_branch']}` | {row['repair_depth']} |"
        )
    lines.extend([
        "",
        "## Front",
        "",
        f"- chart histogram: `{payload['global_front_chart_histogram']}`",
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
    ap.add_argument("--active-words", default="0-15")
    ap.add_argument("--modes", default="common_xor,common_add")
    ap.add_argument("--depth", type=int, default=2)
    ap.add_argument("--beam-width", type=int, default=64)
    ap.add_argument("--top", type=int, default=16)
    ap.add_argument("--archive-limit", type=int, default=96)
    ap.add_argument("--alpha", type=float, default=4.0)
    ap.add_argument("--beta", type=float, default=1.0)
    ap.add_argument("--gamma", type=float, default=8.0)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    source = read_json(args.source)
    kernel_bit = int(source.get("kernel_bit", 31))
    active_words = parse_active_words(args.active_words)
    modes = [part.strip() for part in args.modes.split(",") if part.strip()]
    if any(mode not in {"common_xor", "common_add"} for mode in modes):
        raise SystemExit("kernel-safe Pareto bridge only accepts common modes")
    all_moves = [move for mode in modes for move in move_positions(active_words, mode)]
    score_kwargs = {
        "atlas_alpha": args.alpha,
        "atlas_beta": args.beta,
        "atlas_gamma": args.gamma,
        "atlas_delta": args.delta,
    }

    base_M1 = from_hex_words(source["base"]["M1"])
    base_M2 = from_hex_words(source["base"]["M2"])
    base_rec = source["base"]["rec"]
    base_score = source["base"]["score"]
    base = compact_from_words(base_M1, base_M2, [], base_score, base_rec, score_kwargs)
    forbidden_states = {state_key(base_M1, base_M2)}
    targets = [
        {
            "name": "preserve_guard_repair_chart_D61",
            "branch": "best_guard",
            "require_chart": True,
            "target_a57": source["best_guard"]["rec"]["a57_xor_hw"],
            "target_D61": source["base"]["rec"]["D61_hw"],
        },
        {
            "name": "preserve_D61_repair_guard",
            "branch": "best_d61",
            "require_chart": True,
            "target_a57": source["base"]["rec"]["a57_xor_hw"],
            "target_D61": source["best_d61"]["rec"]["D61_hw"],
        },
    ]

    t0 = time.time()
    branches = [
        scan_branch(
            source,
            target,
            all_moves,
            kernel_bit,
            args.depth,
            args.beam_width,
            args.top,
            args.archive_limit,
            base,
            base_score,
            base_rec,
            score_kwargs,
            forbidden_states,
        )
        for target in targets
    ]
    union = literal_union(source, kernel_bit, base_M1, base_M2, base_score, base_rec, score_kwargs)
    global_front = merge_fronts(branches, union, args.archive_limit)
    anchors = {
        "best_score": min(global_front, key=rank_score),
        "best_balanced": min(global_front, key=rank_balanced),
        "best_guard": min(global_front, key=rank_guard),
        "best_d61": min(global_front, key=rank_d61),
    }
    payload = {
        "report_id": "F374",
        "source": repo_path(args.source),
        "kernel_bit": kernel_bit,
        "active_words": active_words,
        "modes": modes,
        "depth": args.depth,
        "beam_width": args.beam_width,
        "archive_limit": args.archive_limit,
        "score_kwargs": score_kwargs,
        "base": base,
        "literal_union": annotate(union, "literal_union", 0),
        "branches": branches,
        "global_front_size": len(global_front),
        "global_front_chart_histogram": chart_histogram(global_front),
        "global_front": global_front,
        "anchors": anchors,
        "evaluated": sum(row["evaluated"] for row in branches),
        "invalid_moves": sum(row["invalid_moves"] for row in branches),
        "forbidden_skips": sum(row["forbidden_skips"] for row in branches),
        "strict_benchmark_hit_count": sum(row["strict_benchmark_hit_count"] for row in branches),
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
        "front_size": payload["global_front_size"],
        "anchors": {
            label: {
                "score": row["score"],
                "rec": row["rec"],
                "source": row["source_branch"],
                "repair_depth": row["repair_depth"],
            }
            for label, row in anchors.items()
        },
        "strict_hits": payload["strict_benchmark_hit_count"],
        "wall_seconds": payload["wall_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
