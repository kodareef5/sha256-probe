#!/usr/bin/env python3
"""
optimize_chamber_seed_freevars.py - Carry-aware search over F356 free vars.

The F356 no-carry lift leaves 416 free variables. This script keeps the exact
GF(2) W57..W59 solution constraint but hill-climbs those free variables against
the true modular-addition W57..W59 mismatch.
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

from lib.sha256 import MASK, hw  # noqa: E402
from headline_hunt.bets.math_principles.encoders.chamber_seed_linear_lift import (  # noqa: E402
    DEFAULT_CHAMBER,
    KERNEL_BITS,
    build_target_matrix,
    evaluate_candidate,
    int_to_words,
    parse_chamber,
    rref,
    schedule_modular,
    target_bits,
)


DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F357_chamber_seed_freevar_opt.json"
)


def repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def solution_from_free(
    rows: list[int],
    rhs: list[int],
    pivots: list[int],
    free_bits: int,
) -> int:
    x = free_bits
    for row, b, pivot in zip(rows, rhs, pivots):
        parity = (row & x).bit_count() & 1
        if parity != b:
            x |= 1 << pivot
        else:
            x &= ~(1 << pivot)
    return x


def random_free_bits(
    rng: random.Random,
    free_cols: list[int],
    free_prob: float,
) -> int:
    x = 0
    for col in free_cols:
        if rng.random() < free_prob:
            x |= 1 << col
    return x


def true_mismatch_hw(
    M1: list[int],
    target_rounds: list[int],
    target_words: list[int],
) -> tuple[int, list[int]]:
    W = schedule_modular(M1, max(target_rounds))
    by_round = [hw(W[round_idx] ^ target) for round_idx, target in zip(target_rounds, target_words)]
    return sum(by_round), by_round


def free_bit_count(free_bits: int) -> int:
    return free_bits.bit_count()


def make_eval(
    free_bits: int,
    rows: list[int],
    rhs: list[int],
    pivots: list[int],
    target_rounds: list[int],
    target_words: list[int],
) -> dict[str, Any]:
    x = solution_from_free(rows, rhs, pivots, free_bits)
    M1 = int_to_words(x)
    mismatch, by_round = true_mismatch_hw(M1, target_rounds, target_words)
    return {
        "free_bits": free_bits,
        "solution": x,
        "M1": M1,
        "true_mismatch_hw": mismatch,
        "mismatch_by_round": by_round,
        "message_hw": sum(hw(word) for word in M1),
        "free_bit_count": free_bit_count(free_bits),
    }


def rank_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["true_mismatch_hw"],
        row["message_hw"],
        abs(row["free_bit_count"] - 208),
    )


def propose(
    rng: random.Random,
    free_bits: int,
    free_cols: list[int],
    max_flips: int,
) -> int:
    out = free_bits
    n = 1 + (rng.randrange(max_flips) if max_flips > 1 else 0)
    for col in rng.sample(free_cols, k=min(n, len(free_cols))):
        out ^= 1 << col
    return out


def verdict(seed_best: dict[str, Any], best: dict[str, Any]) -> tuple[str, str]:
    delta = best["true_mismatch_hw"] - seed_best["true_mismatch_hw"]
    if best["true_mismatch_hw"] == 0:
        return (
            "freevar_opt_found_exact_chamber_schedule",
            "Promote the seed to atlas-loss chamber initialization immediately.",
        )
    if best["true_mismatch_hw"] <= 24:
        return (
            "freevar_opt_near_chamber_schedule",
            "Run a longer free-variable search and then test atlas-loss continuation from the best seed.",
        )
    if delta < 0:
        return (
            "freevar_opt_improved_partial_seed",
            "The free variables carry real correction signal; continue with larger restarts or add a carry-feature objective.",
        )
    return (
        "freevar_opt_no_improvement",
        "The random F356 seed remains the best found; the next optimizer needs richer moves or carry features.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    best = payload["best"]
    seed = payload["seed_best"]
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: CHAMBER_SEED_FREEVAR_OPT",
        "---",
        "",
        "# F357: chamber-seed free-variable optimization",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Chamber: `{payload['chamber']}`.",
        f"Warmup samples: {payload['warmup_samples']}; hill steps: {payload['steps']}; restarts: {payload['restarts']}.",
        f"Warmup best mismatch: {seed['true_mismatch_hw']} bits.",
        f"Optimized best mismatch: {best['true_mismatch_hw']} bits.",
        f"Best atlas rec: a57={best['atlas_rec']['a57_xor_hw']} D61={best['atlas_rec']['D61_hw']} chart=`{','.join(best['atlas_rec']['chart_top2'])}`.",
        "",
        "| Round | Target | Linear | True | Linear HW | True HW |",
        "|---:|---|---|---|---:|---:|",
    ]
    for row in best["mismatch_by_round"]:
        lines.append(
            f"| {row['round']} | `{row['target']}` | `{row['linear']}` | `{row['true']}` | "
            f"{row['linear_mismatch_hw']} | {row['true_mismatch_hw']} |"
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
    ap.add_argument("--chamber", default=DEFAULT_CHAMBER)
    ap.add_argument("--warmup-samples", type=int, default=5000)
    ap.add_argument("--steps", type=int, default=50000)
    ap.add_argument("--restarts", type=int, default=4)
    ap.add_argument("--max-flips", type=int, default=2)
    ap.add_argument("--free-prob", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=35700)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    if args.warmup_samples < 1 or args.steps < 1 or args.restarts < 1:
        raise SystemExit("warmup, steps, and restarts must be positive")
    if args.max_flips < 1 or args.max_flips > 4:
        raise SystemExit("--max-flips must be in [1,4]")
    idx, target_words = parse_chamber(args.chamber)
    kernel_bit = KERNEL_BITS.get(idx, 31)
    target_rounds = [57, 58, 59]
    t0 = time.time()
    A = build_target_matrix(target_rounds)
    rows, rhs, pivots = rref(A, target_bits(target_words), 512)
    pivot_set = set(pivots)
    free_cols = [col for col in range(512) if col not in pivot_set]
    rng = random.Random(args.seed)

    warmup = [
        make_eval(
            random_free_bits(rng, free_cols, args.free_prob),
            rows,
            rhs,
            pivots,
            target_rounds,
            target_words,
        )
        for _ in range(args.warmup_samples)
    ]
    seed_best = min(warmup, key=rank_key)
    global_best = dict(seed_best)
    improvements = []
    restart_summaries = []

    for restart in range(args.restarts):
        if restart == 0:
            current = dict(seed_best)
        else:
            current = dict(min(rng.sample(warmup, k=min(64, len(warmup))), key=rank_key))
        restart_best = dict(current)
        accepts = 0
        for step in range(args.steps):
            cand_free = propose(rng, current["free_bits"], free_cols, args.max_flips)
            cand = make_eval(cand_free, rows, rhs, pivots, target_rounds, target_words)
            accept = rank_key(cand) < rank_key(current)
            if not accept:
                temp = max(0.25, 4.0 * (1.0 - step / max(1, args.steps)))
                delta = cand["true_mismatch_hw"] - current["true_mismatch_hw"]
                if delta <= 0 or rng.random() < math.exp(-delta / temp):
                    accept = True
            if accept:
                current = cand
                accepts += 1
                if rank_key(current) < rank_key(restart_best):
                    restart_best = dict(current)
                if rank_key(current) < rank_key(global_best):
                    global_best = dict(current)
                    improvements.append({
                        "restart": restart,
                        "step": step,
                        "true_mismatch_hw": current["true_mismatch_hw"],
                        "mismatch_by_round": current["mismatch_by_round"],
                        "message_hw": current["message_hw"],
                    })
        restart_summaries.append({
            "restart": restart,
            "accepts": accepts,
            "start_mismatch_hw": seed_best["true_mismatch_hw"] if restart == 0 else None,
            "best_mismatch_hw": restart_best["true_mismatch_hw"],
            "best_mismatch_by_round": restart_best["mismatch_by_round"],
            "best_message_hw": restart_best["message_hw"],
        })

    best_full = evaluate_candidate(
        global_best["M1"],
        target_rounds,
        target_words,
        kernel_bit,
    )
    seed_full = evaluate_candidate(
        seed_best["M1"],
        target_rounds,
        target_words,
        kernel_bit,
    )
    payload = {
        "report_id": "F357",
        "chamber": args.chamber,
        "candidate_idx": idx,
        "kernel_bit": kernel_bit,
        "rank": len(pivots),
        "free_columns": len(free_cols),
        "warmup_samples": args.warmup_samples,
        "steps": args.steps,
        "restarts": args.restarts,
        "max_flips": args.max_flips,
        "free_prob": args.free_prob,
        "seed": args.seed,
        "seed_best": seed_full,
        "best": best_full,
        "improvements": improvements[-32:],
        "restart_summaries": restart_summaries,
        "wall_seconds": round(time.time() - t0, 6),
    }
    payload["verdict"], payload["decision"] = verdict(seed_full, best_full)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    out_md = args.out_md or args.out_json.with_suffix(".md")
    write_md(out_md, payload)
    print(json.dumps({
        "verdict": payload["verdict"],
        "warmup_best_mismatch": seed_full["true_mismatch_hw"],
        "optimized_best_mismatch": best_full["true_mismatch_hw"],
        "best_atlas_rec": best_full["atlas_rec"],
        "improvements": improvements[-8:],
        "wall_seconds": payload["wall_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
