#!/usr/bin/env python3
"""
continue_atlas_kernel_safe.py - Kernel-preserving atlas continuation.

This reruns the Pareto-seeded atlas continuation under the strict cascade-1
message-difference kernel:
  M1[0]^M2[0] = 1<<kernel_bit
  M1[9]^M2[9] = 1<<kernel_bit
  all other message-word XORs are zero

Any proposed move that violates that kernel is rejected before scoring.
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
    MASK,
    atlas_evaluate,
    atlas_score,
    parse_active_words,
)
from headline_hunt.bets.math_principles.encoders.continue_atlas_from_seed import (  # noqa: E402
    compact_candidate,
    from_hex_words,
    repo_path,
)


DEFAULT_FRONT = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F360_chamber_seed_pareto_front.json"
)
DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F369_kernel_safe_pareto_continuation.json"
)


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def expected_diff(word: int, kernel_bit: int) -> int:
    return (1 << kernel_bit) if word in (0, 9) else 0


def is_kernel_pair(M1: list[int], M2: list[int], kernel_bit: int) -> bool:
    return all(((a ^ b) & MASK) == expected_diff(i, kernel_bit) for i, (a, b) in enumerate(zip(M1, M2)))


def diff_summary(M1: list[int], M2: list[int]) -> dict[str, Any]:
    diffs = [(i, (a ^ b) & MASK) for i, (a, b) in enumerate(zip(M1, M2)) if ((a ^ b) & MASK)]
    return {
        "nonzero_words": [i for i, _ in diffs],
        "word_diffs": {str(i): f"0x{d:08x}" for i, d in diffs},
        "diff_hw": sum(d.bit_count() for _, d in diffs),
    }


def random_flip(rng: random.Random, active_words: list[int], modes: list[str]) -> tuple[Any, ...]:
    mode = rng.choice(modes)
    word = rng.choice(active_words)
    bit = rng.randrange(32)
    if mode == "common_add":
        return (mode, word, bit, rng.choice([-1, 1]))
    return (mode, word, bit)


def apply_flips(M1: list[int], M2: list[int], flips: list[tuple[Any, ...]]) -> tuple[list[int], list[int]]:
    out1 = list(M1)
    out2 = list(M2)
    for flip in flips:
        mode = flip[0]
        word = int(flip[1])
        bit = int(flip[2])
        if mode == "common_xor":
            out1[word] = (out1[word] ^ (1 << bit)) & MASK
            out2[word] = (out2[word] ^ (1 << bit)) & MASK
        elif mode == "common_add":
            sign = int(flip[3])
            delta = sign * (1 << bit)
            out1[word] = (out1[word] + delta) & MASK
            out2[word] = (out2[word] + delta) & MASK
        else:
            raise ValueError(f"kernel-safe runner only supports common modes, got {mode!r}")
    return out1, out2


def compact_flips(flips: list[tuple[Any, ...]]) -> list[dict[str, Any]]:
    out = []
    for flip in flips:
        row = {"mode": flip[0], "word": flip[1], "bit": flip[2]}
        if len(flip) > 3:
            row["sign"] = flip[3]
        out.append(row)
    return out


def select_representatives(front: dict[str, Any], labels: list[str]) -> list[tuple[str, dict[str, Any]]]:
    reps = front.get("representatives", {})
    out = []
    for label in labels:
        if label not in reps:
            raise ValueError(f"front has no representative {label!r}")
        out.append((label, reps[label]))
    return out


def run_restart(
    seed_M1: list[int],
    seed_M2: list[int],
    kernel_bit: int,
    active_words: list[int],
    modes: list[str],
    score_kwargs: dict[str, float],
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

    cur_rec = atlas_evaluate(cur_M1, cur_M2)
    cur_score = atlas_score(cur_rec, **score_kwargs)
    best_M1 = list(cur_M1)
    best_M2 = list(cur_M2)
    best_rec = cur_rec
    best_score = cur_score
    best_a57 = compact_candidate(cur_M1, cur_M2, cur_rec, cur_score)
    accepts = 0
    improvements = []

    for it in range(iterations):
        n_flips = 1 + (rng.randrange(max_flips) if max_flips > 1 else 0)
        flips = [random_flip(rng, active_words, modes) for _ in range(n_flips)]
        cand_M1, cand_M2 = apply_flips(cur_M1, cur_M2, flips)
        if not is_kernel_pair(cand_M1, cand_M2, kernel_bit):
            invalid_moves += 1
            continue
        cand_rec = atlas_evaluate(cand_M1, cand_M2)
        cand_score = atlas_score(cand_rec, **score_kwargs)
        accept = cand_score < cur_score
        if not accept:
            temp = max(0.15, 3.0 * (1.0 - it / max(1, iterations)))
            if rng.random() < math.exp(-(cand_score - cur_score) / temp):
                accept = True
        if accept:
            cur_M1, cur_M2 = cand_M1, cand_M2
            cur_rec = cand_rec
            cur_score = cand_score
            accepts += 1
            if cand_score < best_score:
                best_M1 = list(cand_M1)
                best_M2 = list(cand_M2)
                best_rec = cand_rec
                best_score = cand_score
                improvements.append({
                    "iteration": it,
                    "score": round(best_score, 6),
                    "rec": compact_candidate(best_M1, best_M2, best_rec, best_score)["rec"],
                    "flips": compact_flips(flips),
                })
            if cand_rec["a57_xor_hw"] < best_a57["rec"]["a57_xor_hw"]:
                best_a57 = compact_candidate(cand_M1, cand_M2, cand_rec, cand_score)

    return {
        "restart": restart,
        "best_score": compact_candidate(best_M1, best_M2, best_rec, best_score),
        "best_a57": best_a57,
        "accepts": accepts,
        "invalid_moves": invalid_moves,
        "improvement_tail": improvements[-12:],
    }


def best_run(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return min(rows, key=lambda row: row["best_score"]["score"])


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    improved = [row for row in payload["representative_runs"] if row["best"]["score"] < row["seed"]["score"]]
    if any(row["best"]["rec"]["a57_xor_hw"] == 0 for row in payload["representative_runs"]):
        return (
            "kernel_safe_found_a57_zero",
            "Promote the strict-kernel candidate to chamber atlas verification.",
        )
    if improved:
        return (
            "kernel_safe_improved_atlas_loss",
            "Continue the improved strict-kernel representative with the same kernel guard.",
        )
    return (
        "kernel_safe_no_descent",
        "Under strict cascade-1 kernel preservation, these Pareto seeds do not descend at this budget.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: KERNEL_SAFE_PARETO_CONTINUATION",
        "---",
        "",
        "# F369: kernel-safe Pareto continuation",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Front: `{payload['front']}`.",
        f"Kernel bit: {payload['kernel_bit']}.",
        "",
        "| Representative | Seed score | Seed a57 | Seed D61 | Best score | Best a57 | Best D61 | Invalid moves |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["representative_runs"]:
        seed = row["seed"]
        best = row["best"]
        lines.append(
            f"| `{row['label']}` | {seed['score']} | {seed['rec']['a57_xor_hw']} | "
            f"{seed['rec']['D61_hw']} | {best['score']} | {best['rec']['a57_xor_hw']} | "
            f"{best['rec']['D61_hw']} | {row['invalid_moves']} |"
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
    ap.add_argument("front", nargs="?", type=Path, default=DEFAULT_FRONT)
    ap.add_argument("--labels", default="best_mismatch,best_chart,best_D61")
    ap.add_argument("--active-words", default="0-15")
    ap.add_argument("--modes", default="common_xor,common_add")
    ap.add_argument("--max-flips", type=int, default=2)
    ap.add_argument("--restarts", type=int, default=3)
    ap.add_argument("--iterations", type=int, default=15000)
    ap.add_argument("--init-kicks", type=int, default=2)
    ap.add_argument("--seed", type=int, default=36900)
    ap.add_argument("--alpha", type=float, default=4.0)
    ap.add_argument("--beta", type=float, default=1.0)
    ap.add_argument("--gamma", type=float, default=8.0)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    front = read_json(args.front)
    labels = [part.strip() for part in args.labels.split(",") if part.strip()]
    active_words = parse_active_words(args.active_words)
    modes = [part.strip() for part in args.modes.split(",") if part.strip()]
    if any(mode not in {"common_xor", "common_add"} for mode in modes):
        raise SystemExit("kernel-safe runner only accepts common_xor/common_add modes")
    kernel_bit = int(front.get("kernel_bit", 31))
    score_kwargs = {
        "atlas_alpha": args.alpha,
        "atlas_beta": args.beta,
        "atlas_gamma": args.gamma,
        "atlas_delta": args.delta,
    }
    rng = random.Random(args.seed)
    t0 = time.time()
    representative_runs = []
    for label, row in select_representatives(front, labels):
        M1 = from_hex_words(row["M1"])
        M2 = from_hex_words(row["M2_kernel"])
        if not is_kernel_pair(M1, M2, kernel_bit):
            raise ValueError(f"representative {label} is not kernel-preserving: {diff_summary(M1, M2)}")
        seed_rec = atlas_evaluate(M1, M2)
        seed = compact_candidate(M1, M2, seed_rec, atlas_score(seed_rec, **score_kwargs))
        restarts = [
            run_restart(
                M1,
                M2,
                kernel_bit,
                active_words,
                modes,
                score_kwargs,
                rng,
                args.iterations,
                restart,
                args.init_kicks,
                args.max_flips,
            )
            for restart in range(args.restarts)
        ]
        best = best_run(restarts)["best_score"]
        if not is_kernel_pair(from_hex_words(best["M1"]), from_hex_words(best["M2"]), kernel_bit):
            raise RuntimeError(f"internal: best for {label} drifted")
        representative_runs.append({
            "label": label,
            "seed": seed,
            "best": best,
            "restarts": restarts,
            "invalid_moves": sum(row["invalid_moves"] for row in restarts),
        })

    payload = {
        "report_id": "F369",
        "front": repo_path(args.front),
        "kernel_bit": kernel_bit,
        "args": {
            **vars(args),
            "front": repo_path(args.front),
            "out_json": repo_path(args.out_json),
            "out_md": repo_path(args.out_md) if args.out_md else None,
        },
        "active_words": active_words,
        "modes": modes,
        "score_kwargs": score_kwargs,
        "representative_runs": representative_runs,
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
        "representatives": [
            {
                "label": row["label"],
                "seed": row["seed"]["rec"],
                "seed_score": row["seed"]["score"],
                "best": row["best"]["rec"],
                "best_score": row["best"]["score"],
                "invalid_moves": row["invalid_moves"],
            }
            for row in representative_runs
        ],
        "wall_seconds": payload["wall_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
