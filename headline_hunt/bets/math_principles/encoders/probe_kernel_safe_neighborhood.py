#!/usr/bin/env python3
"""
probe_kernel_safe_neighborhood.py - Deterministic strict-kernel local probe.
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
    compact_candidate,
    move_positions,
)


DEFAULT_SOURCE = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F370_kernel_safe_descendant_continuation.json"
)
DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F371_kernel_safe_neighborhood_r1.json"
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


def rank_score(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        row["score"],
        rec["a57_xor_hw"],
        0 if rec["chart_match"] else 1,
        rec["D61_hw"],
        rec["tail63_state_diff_hw"],
    )


def rank_guard(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        rec["a57_xor_hw"],
        0 if rec["chart_match"] else 1,
        rec["D61_hw"],
        row["score"],
    )


def rank_d61(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        rec["D61_hw"],
        0 if rec["chart_match"] else 1,
        rec["a57_xor_hw"],
        row["score"],
    )


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    if payload["better_than_base_count"]:
        return (
            "kernel_probe_found_local_descent",
            "Promote the best local strict-kernel move to continuation.",
        )
    if payload["a57_lower_count"] or payload["d61_lower_count"]:
        return (
            "kernel_probe_found_coordinate_descent_only",
            "A coordinate can move locally, but scalar atlas loss does not improve.",
        )
    return (
        "kernel_probe_no_local_descent",
        "No strict-kernel single common move improves score, guard, or D61.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    base = payload["base"]
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: KERNEL_SAFE_NEIGHBORHOOD_PROBE",
        "---",
        "",
        "# F371: kernel-safe neighborhood probe",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Source: `{payload['source']}` label `{payload['label']}`.",
        f"Base score: {base['score']} a57={base['rec']['a57_xor_hw']} D61={base['rec']['D61_hw']} chart=`{','.join(base['rec']['chart_top2'])}`.",
        f"Scanned valid moves: {payload['valid_moves']}; invalid rejected: {payload['invalid_moves']}.",
        "",
        "| Candidate | Score | a57 | D61 | Chart | Move |",
        "|---|---:|---:|---:|---|---|",
    ]
    for label in ("best_score", "best_guard", "best_d61"):
        row = payload[label]
        lines.append(
            f"| `{label}` | {row['score']} | {row['rec']['a57_xor_hw']} | "
            f"{row['rec']['D61_hw']} | `{','.join(row['rec']['chart_top2'])}` | `{row['flips']}` |"
        )
    lines.extend([
        "",
        "## Counts",
        "",
        f"- Better than base: {payload['better_than_base_count']}",
        f"- a57-lowering: {payload['a57_lower_count']}",
        f"- D61-lowering: {payload['d61_lower_count']}",
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
    ap.add_argument("--alpha", type=float, default=4.0)
    ap.add_argument("--beta", type=float, default=1.0)
    ap.add_argument("--gamma", type=float, default=8.0)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

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
        raise SystemExit("kernel-safe probe only accepts common modes")
    score_kwargs = {
        "atlas_alpha": args.alpha,
        "atlas_beta": args.beta,
        "atlas_gamma": args.gamma,
        "atlas_delta": args.delta,
    }
    base_rec = atlas_evaluate(base_M1, base_M2)
    base_score = atlas_score(base_rec, **score_kwargs)
    t0 = time.time()
    candidates = []
    invalid = 0
    for mode in modes:
        for move in move_positions(active_words, mode):
            cand_M1, cand_M2 = apply_move(base_M1, base_M2, [move])
            if not is_kernel_pair(cand_M1, cand_M2, kernel_bit):
                invalid += 1
                continue
            rec = atlas_evaluate(cand_M1, cand_M2)
            score = atlas_score(rec, **score_kwargs)
            candidates.append(compact_candidate(
                cand_M1,
                cand_M2,
                rec,
                score,
                [move],
                base_score,
                base_rec,
            ))
    best_score = min(candidates, key=rank_score)
    best_guard = min(candidates, key=rank_guard)
    best_d61 = min(candidates, key=rank_d61)
    payload = {
        "report_id": "F371",
        "source": repo_path(args.source),
        "label": args.label,
        "kernel_bit": kernel_bit,
        "active_words": active_words,
        "modes": modes,
        "score_kwargs": score_kwargs,
        "base": compact_candidate(base_M1, base_M2, base_rec, base_score, [], base_score, base_rec),
        "valid_moves": len(candidates),
        "invalid_moves": invalid,
        "better_than_base_count": sum(1 for candidate in candidates if candidate["score"] < base_score),
        "a57_lower_count": sum(1 for candidate in candidates if candidate["rec"]["a57_xor_hw"] < base_rec["a57_xor_hw"]),
        "d61_lower_count": sum(1 for candidate in candidates if candidate["rec"]["D61_hw"] < base_rec["D61_hw"]),
        "best_score": best_score,
        "best_guard": best_guard,
        "best_d61": best_d61,
        "top_by_score": sorted(candidates, key=rank_score)[:12],
        "top_by_guard": sorted(candidates, key=rank_guard)[:12],
        "top_by_d61": sorted(candidates, key=rank_d61)[:12],
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
        "counts": {
            "better_than_base": payload["better_than_base_count"],
            "a57_lower": payload["a57_lower_count"],
            "d61_lower": payload["d61_lower_count"],
            "valid": payload["valid_moves"],
            "invalid": payload["invalid_moves"],
        },
        "wall_seconds": payload["wall_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
