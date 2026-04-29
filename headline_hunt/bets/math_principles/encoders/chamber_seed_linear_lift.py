#!/usr/bin/env python3
"""
chamber_seed_linear_lift.py - No-carry schedule lift for chamber W57..W59 seeds.

This is a deliberately small feasibility probe for the F314 "chamber-seeded
initialization" idea. It solves the GF(2) no-carry schedule recurrence for an
M[0..15] whose W[57..59] match a chamber witness, then evaluates the true
modular-addition schedule to measure carry breakage.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from lib.sha256 import MASK, add, hw, sigma0, sigma1  # noqa: E402
from headline_hunt.bets.block2_wang.encoders.preimage_lift import (  # noqa: E402
    SIGMA0_MAT,
    SIGMA1_MAT,
    apply_gf2_mat,
)
from headline_hunt.bets.block2_wang.encoders.search_schedule_space import (  # noqa: E402
    atlas_evaluate,
)


DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F356_chamber_seed_linear_lift.json"
)

DEFAULT_CHAMBER = "0:0x370fef5f:0x6ced4182:0x9af03606"

KERNEL_BITS = {
    0: 31,
    1: 19,
    8: 3,
    17: 15,
}


def repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def parse_chamber(spec: str) -> tuple[int, list[int]]:
    parts = spec.split(":")
    if len(parts) != 4:
        raise ValueError("chamber spec must be idx:W57:W58:W59")
    idx = int(parts[0])
    words = [int(part, 16) & MASK for part in parts[1:]]
    return idx, words


def schedule_xor_linear(M: list[int], max_round: int) -> list[int]:
    W = list(M) + [0] * max(0, max_round + 1 - 16)
    for i in range(16, max_round + 1):
        W[i] = (
            apply_gf2_mat(SIGMA1_MAT, W[i - 2])
            ^ W[i - 7]
            ^ apply_gf2_mat(SIGMA0_MAT, W[i - 15])
            ^ W[i - 16]
        ) & MASK
    return W


def schedule_modular(M: list[int], max_round: int = 63) -> list[int]:
    W = list(M) + [0] * max(0, max_round + 1 - 16)
    for i in range(16, max_round + 1):
        W[i] = add(sigma1(W[i - 2]), W[i - 7], sigma0(W[i - 15]), W[i - 16])
    return W


def build_target_matrix(rounds: list[int]) -> list[int]:
    rows = [0] * (32 * len(rounds))
    max_round = max(rounds)
    for inp_bit in range(512):
        word = inp_bit // 32
        bit = inp_bit % 32
        M = [0] * 16
        M[word] = 1 << bit
        W = schedule_xor_linear(M, max_round)
        for ridx, round_idx in enumerate(rounds):
            value = W[round_idx]
            for out_bit in range(32):
                if (value >> out_bit) & 1:
                    rows[ridx * 32 + out_bit] |= 1 << inp_bit
    return rows


def rref(
    A_rows: list[int],
    B_vals: list[int],
    n_cols: int,
) -> tuple[list[int], list[int], list[int]]:
    A = list(A_rows)
    B = list(B_vals)
    pivots: list[int] = []
    r = 0
    for col in range(n_cols):
        bit = 1 << col
        pivot = None
        for idx in range(r, len(A)):
            if A[idx] & bit:
                pivot = idx
                break
        if pivot is None:
            continue
        A[r], A[pivot] = A[pivot], A[r]
        B[r], B[pivot] = B[pivot], B[r]
        for idx in range(len(A)):
            if idx != r and (A[idx] & bit):
                A[idx] ^= A[r]
                B[idx] ^= B[r]
        pivots.append(col)
        r += 1
    for idx in range(r, len(A)):
        if A[idx] == 0 and B[idx] != 0:
            raise ValueError("target is outside the no-carry schedule image")
    return A[:r], B[:r], pivots


def target_bits(words: list[int]) -> list[int]:
    bits = []
    for word in words:
        for bit in range(32):
            bits.append((word >> bit) & 1)
    return bits


def sample_solution(
    rows: list[int],
    rhs: list[int],
    pivots: list[int],
    rng: random.Random,
    free_prob: float,
) -> int:
    pivot_set = set(pivots)
    x = 0
    for col in range(512):
        if col not in pivot_set and rng.random() < free_prob:
            x |= 1 << col
    for row, b, pivot in zip(rows, rhs, pivots):
        parity = (row & x).bit_count() & 1
        if parity != b:
            x |= 1 << pivot
        else:
            x &= ~(1 << pivot)
    return x


def int_to_words(x: int) -> list[int]:
    return [(x >> (32 * word)) & MASK for word in range(16)]


def evaluate_candidate(
    M1: list[int],
    target_rounds: list[int],
    target_words: list[int],
    kernel_bit: int,
) -> dict[str, Any]:
    W_linear = schedule_xor_linear(M1, max(target_rounds))
    W_true = schedule_modular(M1, 63)
    mismatch_by_round = []
    for round_idx, target in zip(target_rounds, target_words):
        mismatch_by_round.append({
            "round": round_idx,
            "target": f"0x{target:08x}",
            "linear": f"0x{W_linear[round_idx]:08x}",
            "true": f"0x{W_true[round_idx]:08x}",
            "linear_mismatch_hw": hw(W_linear[round_idx] ^ target),
            "true_mismatch_hw": hw(W_true[round_idx] ^ target),
        })
    M2 = list(M1)
    M2[0] ^= 1 << kernel_bit
    M2[9] ^= 1 << kernel_bit
    atlas = atlas_evaluate(M1, M2)
    return {
        "true_mismatch_hw": sum(row["true_mismatch_hw"] for row in mismatch_by_round),
        "linear_mismatch_hw": sum(row["linear_mismatch_hw"] for row in mismatch_by_round),
        "message_hw": sum(hw(word) for word in M1),
        "mismatch_by_round": mismatch_by_round,
        "atlas_rec": {
            "a57_xor_hw": atlas["a57_xor_hw"],
            "D61_hw": atlas["D61_hw"],
            "chart_top2": list(atlas["chart_top2"]),
            "tail63_state_diff_hw": atlas["tail63_state_diff_hw"],
        },
        "M1": [f"0x{word:08x}" for word in M1],
        "M2_kernel": [f"0x{word:08x}" for word in M2],
    }


def verdict(best: dict[str, Any]) -> tuple[str, str]:
    mismatch = best["true_mismatch_hw"]
    if mismatch == 0:
        return (
            "linear_lift_exact_true_schedule_seed",
            "Promote this as a chamber-seeded M1 and run atlas-loss search around it.",
        )
    if mismatch <= 24:
        return (
            "linear_lift_near_seed",
            "Use this as a seed for carry-correction search over the free variables.",
        )
    if mismatch <= 36:
        return (
            "linear_lift_partial_seed",
            "The no-carry lift has signal, but it needs carry-aware correction before atlas search.",
        )
    return (
        "linear_lift_carry_breakage_large",
        "No-carry chamber seeding is too lossy by itself; the next lift must model carries or optimize the RREF free variables against true schedule mismatch.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    best = payload["best"]
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: CHAMBER_SEED_LINEAR_LIFT",
        "---",
        "",
        "# F356: chamber-seed no-carry linear lift",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Chamber: `{payload['chamber']}`.",
        f"Rank/free columns: {payload['rank']}/{payload['free_columns']}.",
        f"Samples: {payload['samples']}.",
        f"Best true W57..W59 mismatch: {best['true_mismatch_hw']} bits.",
        f"Best atlas rec under kernel-pair check: a57={best['atlas_rec']['a57_xor_hw']} D61={best['atlas_rec']['D61_hw']} chart=`{','.join(best['atlas_rec']['chart_top2'])}`.",
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
    ap.add_argument("--chamber", default=DEFAULT_CHAMBER,
                    help="idx:W57:W58:W59 chamber witness")
    ap.add_argument("--samples", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=35600)
    ap.add_argument("--free-prob", type=float, default=0.5)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    if args.samples < 1:
        raise SystemExit("--samples must be positive")
    if not 0.0 <= args.free_prob <= 1.0:
        raise SystemExit("--free-prob must be in [0,1]")
    idx, target_words = parse_chamber(args.chamber)
    kernel_bit = KERNEL_BITS.get(idx, 31)
    target_rounds = [57, 58, 59]
    t0 = time.time()
    A = build_target_matrix(target_rounds)
    rhs = target_bits(target_words)
    rows, reduced_rhs, pivots = rref(A, rhs, 512)
    rng = random.Random(args.seed)

    candidates = []
    # Include the zero-free solution, then random free-variable samples.
    zero_rng = random.Random(args.seed)
    candidates.append(
        evaluate_candidate(
            int_to_words(sample_solution(rows, reduced_rhs, pivots, zero_rng, 0.0)),
            target_rounds,
            target_words,
            kernel_bit,
        )
    )
    for _ in range(args.samples):
        x = sample_solution(rows, reduced_rhs, pivots, rng, args.free_prob)
        candidates.append(
            evaluate_candidate(int_to_words(x), target_rounds, target_words, kernel_bit)
        )
    candidates.sort(key=lambda row: (
        row["true_mismatch_hw"],
        row["atlas_rec"]["a57_xor_hw"],
        row["atlas_rec"]["D61_hw"],
        row["message_hw"],
    ))
    payload = {
        "report_id": "F356",
        "chamber": args.chamber,
        "candidate_idx": idx,
        "kernel_bit": kernel_bit,
        "target_rounds": target_rounds,
        "target_words": [f"0x{word:08x}" for word in target_words],
        "rank": len(pivots),
        "free_columns": 512 - len(pivots),
        "samples": args.samples,
        "free_prob": args.free_prob,
        "seed": args.seed,
        "best": candidates[0],
        "top": candidates[:16],
        "wall_seconds": round(time.time() - t0, 6),
    }
    payload["verdict"], payload["decision"] = verdict(candidates[0])
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    out_md = args.out_md or args.out_json.with_suffix(".md")
    write_md(out_md, payload)
    print(json.dumps({
        "verdict": payload["verdict"],
        "rank": payload["rank"],
        "free_columns": payload["free_columns"],
        "best_true_mismatch_hw": payload["best"]["true_mismatch_hw"],
        "best_atlas_rec": payload["best"]["atlas_rec"],
        "wall_seconds": payload["wall_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
