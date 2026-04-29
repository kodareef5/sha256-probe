#!/usr/bin/env python3
"""
build_chamber_seed_pareto_front.py - Pareto search over chamber-seed free vars.

F359 showed that a weighted sum hides the tradeoff between true schedule
proximity, chart membership, and the a57 guard. This script keeps the exact
no-carry W57..W59 chamber constraint and maintains a non-dominated frontier
over:
  - true modular W57..W59 mismatch
  - chart penalty: 0 for (dh,dCh)/(dCh,dh), 1 otherwise
  - a57_xor_hw
  - D61_hw
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

from headline_hunt.bets.math_principles.encoders.chamber_seed_linear_lift import (  # noqa: E402
    DEFAULT_CHAMBER,
    KERNEL_BITS,
    build_target_matrix,
    evaluate_candidate,
    int_to_words,
    parse_chamber,
    rref,
    target_bits,
)
from headline_hunt.bets.math_principles.encoders.optimize_chamber_seed_freevars import (  # noqa: E402
    make_eval,
    propose,
    random_free_bits,
)


DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F360_chamber_seed_pareto_front.json"
)


def repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def chart_penalty(row: dict[str, Any]) -> int:
    rec = row.get("atlas_rec") or {}
    chart = tuple(rec.get("chart_top2") or ())
    return 0 if chart in {("dh", "dCh"), ("dCh", "dh")} else 1


def metrics(row: dict[str, Any]) -> tuple[int, int, int, int]:
    rec = row.get("atlas_rec") or {}
    return (
        int(row["true_mismatch_hw"]),
        chart_penalty(row),
        int(rec.get("a57_xor_hw", 999)),
        int(rec.get("D61_hw", 999)),
    )


def dominates(a: dict[str, Any], b: dict[str, Any]) -> bool:
    ma = metrics(a)
    mb = metrics(b)
    return all(x <= y for x, y in zip(ma, mb)) and any(x < y for x, y in zip(ma, mb))


def dedupe_key(row: dict[str, Any]) -> tuple[int, tuple[int, int, int, int]]:
    return int(row["free_bits"]), metrics(row)


def front_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row.get("atlas_rec") or {}
    return (
        chart_penalty(row),
        rec.get("a57_xor_hw", 999),
        row["true_mismatch_hw"],
        rec.get("D61_hw", 999),
        row["message_hw"],
    )


def mismatch_sort_key(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row.get("atlas_rec") or {}
    return (
        row["true_mismatch_hw"],
        chart_penalty(row),
        rec.get("a57_xor_hw", 999),
        rec.get("D61_hw", 999),
    )


def add_to_front(front: list[dict[str, Any]], row: dict[str, Any], max_front: int) -> bool:
    if any(dedupe_key(existing) == dedupe_key(row) for existing in front):
        return False
    if any(dominates(existing, row) for existing in front):
        return False
    front[:] = [existing for existing in front if not dominates(row, existing)]
    front.append(row)
    if len(front) > max_front:
        front.sort(key=front_sort_key)
        del front[max_front:]
    return True


def compact_row(row: dict[str, Any], target_rounds: list[int], target_words: list[int],
                kernel_bit: int) -> dict[str, Any]:
    full = evaluate_candidate(row["M1"], target_rounds, target_words, kernel_bit)
    return {
        "metrics": {
            "true_mismatch_hw": full["true_mismatch_hw"],
            "chart_penalty": chart_penalty(row),
            "a57_xor_hw": full["atlas_rec"]["a57_xor_hw"],
            "D61_hw": full["atlas_rec"]["D61_hw"],
            "tail63_state_diff_hw": full["atlas_rec"]["tail63_state_diff_hw"],
            "chart_top2": full["atlas_rec"]["chart_top2"],
            "message_hw": row["message_hw"],
        },
        "mismatch_by_round": full["mismatch_by_round"],
        "M1": full["M1"],
        "M2_kernel": full["M2_kernel"],
    }


def representative_rows(front: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    chart_rows = [row for row in front if chart_penalty(row) == 0]
    return {
        "best_mismatch": min(front, key=mismatch_sort_key),
        "best_a57": min(front, key=lambda row: (
            (row.get("atlas_rec") or {}).get("a57_xor_hw", 999),
            chart_penalty(row),
            row["true_mismatch_hw"],
            (row.get("atlas_rec") or {}).get("D61_hw", 999),
        )),
        "best_chart": min(chart_rows or front, key=lambda row: (
            chart_penalty(row),
            (row.get("atlas_rec") or {}).get("a57_xor_hw", 999),
            row["true_mismatch_hw"],
            (row.get("atlas_rec") or {}).get("D61_hw", 999),
        )),
        "best_D61": min(front, key=lambda row: (
            (row.get("atlas_rec") or {}).get("D61_hw", 999),
            chart_penalty(row),
            (row.get("atlas_rec") or {}).get("a57_xor_hw", 999),
            row["true_mismatch_hw"],
        )),
    }


def verdict(reps: dict[str, dict[str, Any]]) -> tuple[str, str]:
    best_mismatch = reps["best_mismatch"]
    best_chart = reps["best_chart"]
    best_a57 = reps["best_a57"]
    if best_mismatch["true_mismatch_hw"] <= 20 and chart_penalty(best_mismatch) == 0:
        return (
            "pareto_found_near_chamber_chart_seed",
            "Promote the best-mismatch chart seed into atlas-loss continuation.",
        )
    if chart_penalty(best_chart) == 0 and best_chart["true_mismatch_hw"] <= 28:
        return (
            "pareto_found_chart_compatible_partial_seed",
            "Use the chart-compatible front member as the next chamber-seed continuation candidate.",
        )
    if (best_a57.get("atlas_rec") or {}).get("a57_xor_hw", 999) <= 8:
        return (
            "pareto_preserved_low_guard_member",
            "Keep low-guard and low-mismatch members separate; scalar weighting should stay demoted.",
        )
    return (
        "pareto_front_mapped_no_seed_yet",
        "The front maps the conflict, but no member is close enough for chamber-seeded continuation yet.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: CHAMBER_SEED_PARETO_FRONT",
        "---",
        "",
        "# F360: chamber-seed Pareto front",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Front size: {payload['front_size']}; evaluations: {payload['evaluations']}.",
        f"Chamber: `{payload['chamber']}`.",
        "",
        "| Representative | Mismatch | Chart | a57 | D61 | Tail |",
        "|---|---:|---|---:|---:|---:|",
    ]
    for label, row in payload["representatives"].items():
        m = row["metrics"]
        lines.append(
            f"| `{label}` | {m['true_mismatch_hw']} | `{','.join(m['chart_top2'])}` | "
            f"{m['a57_xor_hw']} | {m['D61_hw']} | {m['tail63_state_diff_hw']} |"
        )
    lines.extend([
        "",
        "## Front Preview",
        "",
        "| Rank | Mismatch | Chart | a57 | D61 | msgHW |",
        "|---:|---:|---|---:|---:|---:|",
    ])
    for idx, row in enumerate(payload["front_preview"], 1):
        m = row["metrics"]
        lines.append(
            f"| {idx} | {m['true_mismatch_hw']} | `{','.join(m['chart_top2'])}` | "
            f"{m['a57_xor_hw']} | {m['D61_hw']} | {m['message_hw']} |"
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
    ap.add_argument("--warmup-samples", type=int, default=4000)
    ap.add_argument("--steps", type=int, default=80000)
    ap.add_argument("--max-flips", type=int, default=4)
    ap.add_argument("--max-front", type=int, default=256)
    ap.add_argument("--free-prob", type=float, default=0.5)
    ap.add_argument("--seed", type=int, default=36000)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    if args.warmup_samples < 1 or args.steps < 1:
        raise SystemExit("--warmup-samples and --steps must be positive")
    if args.max_flips < 1 or args.max_flips > 6:
        raise SystemExit("--max-flips must be in [1,6]")
    idx, target_words = parse_chamber(args.chamber)
    kernel_bit = KERNEL_BITS.get(idx, 31)
    target_rounds = [57, 58, 59]
    t0 = time.time()
    A = build_target_matrix(target_rounds)
    rows, rhs, pivots = rref(A, target_bits(target_words), 512)
    pivot_set = set(pivots)
    free_cols = [col for col in range(512) if col not in pivot_set]
    rng = random.Random(args.seed)
    objective_weights = {"mismatch": 1.0, "a57": 1.0, "D61": 1.0, "chart": 1.0, "tail": 0.0}

    front: list[dict[str, Any]] = []
    archive: list[dict[str, Any]] = []
    additions = 0
    for _ in range(args.warmup_samples):
        row = make_eval(
            random_free_bits(rng, free_cols, args.free_prob),
            rows,
            rhs,
            pivots,
            target_rounds,
            target_words,
            kernel_bit,
            objective_weights,
        )
        archive.append(row)
        if add_to_front(front, row, args.max_front):
            additions += 1

    for step in range(args.steps):
        if front and rng.random() < 0.75:
            parent = rng.choice(front)
        else:
            parent = rng.choice(archive)
        free_bits = propose(rng, parent["free_bits"], free_cols, args.max_flips)
        row = make_eval(
            free_bits,
            rows,
            rhs,
            pivots,
            target_rounds,
            target_words,
            kernel_bit,
            objective_weights,
        )
        archive.append(row)
        if len(archive) > max(args.max_front * 8, 2048):
            archive.sort(key=front_sort_key)
            del archive[max(args.max_front * 8, 2048):]
        if add_to_front(front, row, args.max_front):
            additions += 1

    front.sort(key=front_sort_key)
    reps_raw = representative_rows(front)
    representatives = {
        label: compact_row(row, target_rounds, target_words, kernel_bit)
        for label, row in reps_raw.items()
    }
    payload = {
        "report_id": "F360",
        "chamber": args.chamber,
        "candidate_idx": idx,
        "kernel_bit": kernel_bit,
        "rank": len(pivots),
        "free_columns": len(free_cols),
        "warmup_samples": args.warmup_samples,
        "steps": args.steps,
        "max_flips": args.max_flips,
        "max_front": args.max_front,
        "seed": args.seed,
        "evaluations": args.warmup_samples + args.steps,
        "front_size": len(front),
        "front_additions": additions,
        "representatives": representatives,
        "front_preview": [
            compact_row(row, target_rounds, target_words, kernel_bit)
            for row in front[:24]
        ],
        "wall_seconds": round(time.time() - t0, 6),
    }
    payload["verdict"], payload["decision"] = verdict(reps_raw)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    out_md = args.out_md or args.out_json.with_suffix(".md")
    write_md(out_md, payload)
    print(json.dumps({
        "verdict": payload["verdict"],
        "front_size": payload["front_size"],
        "evaluations": payload["evaluations"],
        "representatives": {
            label: row["metrics"]
            for label, row in payload["representatives"].items()
        },
        "wall_seconds": payload["wall_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
