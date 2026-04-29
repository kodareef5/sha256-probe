#!/usr/bin/env python3
"""
continue_kernel_safe_bridge_anchors.py - Target-weighted continuation from F374.
"""

from __future__ import annotations

import argparse
import json
import math
import random
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
    apply_flips,
    compact_flips,
    diff_summary,
    is_kernel_pair,
    random_flip,
)


DEFAULT_SOURCE = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F374_kernel_safe_pareto_bridge.json"
)
DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F375_kernel_safe_bridge_anchor_continuation.json"
)

PROFILE_BY_LABEL = {
    "best_score": {
        "name": "repair_low_guard_chart_D61",
        "atlas_alpha": 4.0,
        "atlas_beta": 3.0,
        "atlas_gamma": 20.0,
        "atlas_delta": 0.05,
    },
    "best_guard": {
        "name": "repair_low_guard_chart_D61",
        "atlas_alpha": 4.0,
        "atlas_beta": 3.0,
        "atlas_gamma": 20.0,
        "atlas_delta": 0.05,
    },
    "best_balanced": {
        "name": "balanced_chart_D61_pressure",
        "atlas_alpha": 6.0,
        "atlas_beta": 3.0,
        "atlas_gamma": 16.0,
        "atlas_delta": 0.05,
    },
    "best_d61": {
        "name": "repair_low_D61_guard",
        "atlas_alpha": 10.0,
        "atlas_beta": 1.0,
        "atlas_gamma": 16.0,
        "atlas_delta": 0.05,
    },
}


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def chart_penalty(row: dict[str, Any]) -> int:
    return 0 if row["rec"]["chart_match"] else 1


def rank_profile(row: dict[str, Any]) -> tuple[Any, ...]:
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


def rank_chart(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        chart_penalty(row),
        rec["a57_xor_hw"],
        rec["D61_hw"],
        row["score"],
    )


def candidate_row(
    M1: list[int],
    M2: list[int],
    profile_kwargs: dict[str, float],
    default_kwargs: dict[str, float],
) -> dict[str, Any]:
    rec = atlas_evaluate(M1, M2)
    profile_score = atlas_score(rec, **profile_kwargs)
    row = compact_candidate(M1, M2, rec, profile_score)
    row["default_score"] = round(atlas_score(rec, **default_kwargs), 6)
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


def run_restart(
    seed_M1: list[int],
    seed_M2: list[int],
    kernel_bit: int,
    active_words: list[int],
    modes: list[str],
    profile_kwargs: dict[str, float],
    default_kwargs: dict[str, float],
    base: dict[str, Any],
    rng: random.Random,
    iterations: int,
    restart: int,
    init_kicks: int,
    max_flips: int,
) -> dict[str, Any]:
    cur_M1 = list(seed_M1)
    cur_M2 = list(seed_M2)
    invalid_moves = 0
    for _ in range(init_kicks if restart else 0):
        for _attempt in range(100):
            flips = [random_flip(rng, active_words, modes)]
            cand_M1, cand_M2 = apply_flips(cur_M1, cur_M2, flips)
            if is_kernel_pair(cand_M1, cand_M2, kernel_bit):
                cur_M1, cur_M2 = cand_M1, cand_M2
                break
            invalid_moves += 1

    cur = candidate_row(cur_M1, cur_M2, profile_kwargs, default_kwargs)
    best_profile = cur
    best_guard = cur
    best_d61 = cur
    best_chart = cur
    accepts = 0
    strict_hits = 1 if strict_benchmark_hit(cur, base) else 0
    improvements = []

    for it in range(iterations):
        n_flips = 1 + (rng.randrange(max_flips) if max_flips > 1 else 0)
        flips = [random_flip(rng, active_words, modes) for _ in range(n_flips)]
        cand_M1, cand_M2 = apply_flips(cur_M1, cur_M2, flips)
        if not is_kernel_pair(cand_M1, cand_M2, kernel_bit):
            invalid_moves += 1
            continue
        cand = candidate_row(cand_M1, cand_M2, profile_kwargs, default_kwargs)
        if rank_profile(cand) < rank_profile(best_profile):
            best_profile = cand
            improvements.append({
                "iteration": it,
                "kind": "profile",
                "score": cand["score"],
                "default_score": cand["default_score"],
                "rec": cand["rec"],
                "flips": compact_flips(flips),
            })
        if rank_guard(cand) < rank_guard(best_guard):
            best_guard = cand
        if rank_d61(cand) < rank_d61(best_d61):
            best_d61 = cand
        if rank_chart(cand) < rank_chart(best_chart):
            best_chart = cand
        if strict_benchmark_hit(cand, base):
            strict_hits += 1

        accept = cand["score"] < cur["score"]
        if not accept:
            temp = max(0.15, 3.0 * (1.0 - it / max(1, iterations)))
            if rng.random() < math.exp(-(cand["score"] - cur["score"]) / temp):
                accept = True
        if accept:
            cur_M1, cur_M2 = cand_M1, cand_M2
            cur = cand
            accepts += 1

    return {
        "restart": restart,
        "best_profile": best_profile,
        "best_guard": best_guard,
        "best_d61": best_d61,
        "best_chart": best_chart,
        "accepts": accepts,
        "invalid_moves": invalid_moves,
        "strict_benchmark_hit_count": strict_hits,
        "improvement_tail": improvements[-12:],
    }


def best_of(restarts: list[dict[str, Any]], key: str, ranker) -> dict[str, Any]:
    return min((row[key] for row in restarts), key=ranker)


def label_profile(label: str) -> dict[str, Any]:
    if label not in PROFILE_BY_LABEL:
        raise ValueError(f"no target-weight profile for label {label!r}")
    profile = dict(PROFILE_BY_LABEL[label])
    name = profile.pop("name")
    return {"name": name, "score_kwargs": profile}


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    if payload["strict_benchmark_hit_count"]:
        return (
            "bridge_anchor_continuation_found_strict_benchmark_hit",
            "Promote the strict benchmark hit to deterministic verification.",
        )
    improved = [row for row in payload["anchor_runs"] if row["best_profile"]["score"] < row["seed"]["score"]]
    if improved:
        return (
            "bridge_anchor_continuation_improves_profile",
            "Continue the improved target-weighted anchor with deterministic neighborhood checks.",
        )
    return (
        "bridge_anchor_continuation_no_profile_descent",
        "The F374 anchors are stiff under this target-weighted strict-kernel budget.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: KERNEL_SAFE_BRIDGE_ANCHOR_CONTINUATION",
        "---",
        "",
        "# F375: strict-kernel bridge-anchor continuation",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Source: `{payload['source']}`.",
        f"Strict benchmark hits: {payload['strict_benchmark_hit_count']}.",
        "",
        "| Label | Profile | Seed score | Seed a57 | Seed D61 | Best score | Best a57 | Best D61 | Best chart | Invalid |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for row in payload["anchor_runs"]:
        seed = row["seed"]
        best = row["best_profile"]
        lines.append(
            f"| `{row['label']}` | `{row['profile']['name']}` | {seed['score']} | "
            f"{seed['rec']['a57_xor_hw']} | {seed['rec']['D61_hw']} | "
            f"{best['score']} | {best['rec']['a57_xor_hw']} | {best['rec']['D61_hw']} | "
            f"`{','.join(best['rec']['chart_top2'])}` | {row['invalid_moves']} |"
        )
    lines.extend([
        "",
        "## Coordinate Bests",
        "",
        "| Label | Best guard | Best D61 | Best chart candidate |",
        "|---|---|---|---|",
    ])
    for row in payload["anchor_runs"]:
        guard = row["best_guard"]
        d61 = row["best_d61"]
        chart = row["best_chart"]
        lines.append(
            f"| `{row['label']}` | a57={guard['rec']['a57_xor_hw']} D61={guard['rec']['D61_hw']} chart=`{','.join(guard['rec']['chart_top2'])}` | "
            f"a57={d61['rec']['a57_xor_hw']} D61={d61['rec']['D61_hw']} chart=`{','.join(d61['rec']['chart_top2'])}` | "
            f"score={chart['score']} a57={chart['rec']['a57_xor_hw']} D61={chart['rec']['D61_hw']} chart=`{','.join(chart['rec']['chart_top2'])}` |"
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
    ap.add_argument("--labels", default="best_score,best_balanced,best_d61")
    ap.add_argument("--active-words", default="0-15")
    ap.add_argument("--modes", default="common_xor,common_add")
    ap.add_argument("--max-flips", type=int, default=2)
    ap.add_argument("--restarts", type=int, default=3)
    ap.add_argument("--iterations", type=int, default=20000)
    ap.add_argument("--init-kicks", type=int, default=1)
    ap.add_argument("--seed", type=int, default=37500)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    source = read_json(args.source)
    labels = [part.strip() for part in args.labels.split(",") if part.strip()]
    active_words = parse_active_words(args.active_words)
    modes = [part.strip() for part in args.modes.split(",") if part.strip()]
    if any(mode not in {"common_xor", "common_add"} for mode in modes):
        raise SystemExit("kernel-safe bridge continuation only accepts common modes")
    kernel_bit = int(source.get("kernel_bit", 31))
    default_kwargs = source.get("score_kwargs") or {
        "atlas_alpha": 4.0,
        "atlas_beta": 1.0,
        "atlas_gamma": 8.0,
        "atlas_delta": 0.05,
    }
    base = source["base"]
    rng = random.Random(args.seed)
    t0 = time.time()
    anchor_runs = []
    for label in labels:
        anchor = source["anchors"][label]
        profile = label_profile(label)
        M1 = from_hex_words(anchor["M1"])
        M2 = from_hex_words(anchor["M2"])
        if not is_kernel_pair(M1, M2, kernel_bit):
            raise ValueError(f"anchor {label} drifted: {diff_summary(M1, M2)}")
        seed_row = candidate_row(M1, M2, profile["score_kwargs"], default_kwargs)
        restarts = [
            run_restart(
                M1,
                M2,
                kernel_bit,
                active_words,
                modes,
                profile["score_kwargs"],
                default_kwargs,
                base,
                rng,
                args.iterations,
                restart,
                args.init_kicks,
                args.max_flips,
            )
            for restart in range(args.restarts)
        ]
        anchor_runs.append({
            "label": label,
            "profile": profile,
            "seed": seed_row,
            "best_profile": best_of(restarts, "best_profile", rank_profile),
            "best_guard": best_of(restarts, "best_guard", rank_guard),
            "best_d61": best_of(restarts, "best_d61", rank_d61),
            "best_chart": best_of(restarts, "best_chart", rank_chart),
            "restarts": restarts,
            "invalid_moves": sum(row["invalid_moves"] for row in restarts),
            "strict_benchmark_hit_count": sum(row["strict_benchmark_hit_count"] for row in restarts),
        })

    payload = {
        "report_id": "F375",
        "source": repo_path(args.source),
        "kernel_bit": kernel_bit,
        "args": {
            **vars(args),
            "source": repo_path(args.source),
            "out_json": repo_path(args.out_json),
            "out_md": repo_path(args.out_md) if args.out_md else None,
        },
        "active_words": active_words,
        "modes": modes,
        "default_score_kwargs": default_kwargs,
        "base": base,
        "anchor_runs": anchor_runs,
        "strict_benchmark_hit_count": sum(row["strict_benchmark_hit_count"] for row in anchor_runs),
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
        "strict_hits": payload["strict_benchmark_hit_count"],
        "anchors": [
            {
                "label": row["label"],
                "profile": row["profile"]["name"],
                "seed_score": row["seed"]["score"],
                "best_profile_score": row["best_profile"]["score"],
                "best_profile_rec": row["best_profile"]["rec"],
                "best_guard_rec": row["best_guard"]["rec"],
                "best_d61_rec": row["best_d61"]["rec"],
                "invalid": row["invalid_moves"],
            }
            for row in anchor_runs
        ],
        "wall_seconds": payload["wall_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
