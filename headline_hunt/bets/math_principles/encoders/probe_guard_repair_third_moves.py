#!/usr/bin/env python3
"""
probe_guard_repair_third_moves.py - Third-move guard repair from F366.
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
from headline_hunt.bets.math_principles.encoders.probe_atlas_neighborhood import (  # noqa: E402
    apply_move,
    compact_candidate,
    move_positions,
)


DEFAULT_SOURCE = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F366_d61_repair_pair_probe.json"
)
DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F367_guard_repair_third_probe.json"
)


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def rank_score(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        row["score"],
        rec["a57_xor_hw"],
        0 if rec["chart_match"] else 1,
        rec["D61_hw"],
    )


def rank_guard(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        rec["a57_xor_hw"],
        0 if rec["chart_match"] else 1,
        rec["D61_hw"],
        row["score"],
    )


def rank_preserve(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        0 if rec["chart_match"] else 1,
        max(0, rec["D61_hw"] - 8),
        rec["a57_xor_hw"],
        row["score"],
    )


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    if payload["target_preserve_count"]:
        return (
            "next_move_hits_target_constraints",
            "Promote the target-preserving candidate as the next continuation seed.",
        )
    if payload["guard_repair_preserve_count"]:
        return (
            "third_move_repairs_guard_with_D61_chart_preserved",
            "Promote the best guard-repair triple as a new continuation seed.",
        )
    if payload["a57_lower_count"]:
        return (
            "third_move_lowers_guard_only",
            "Guard can move locally, but not yet while preserving the D61/chart pair.",
        )
    return (
        "third_move_no_guard_repair",
        "The F366 D61/chart repaired pair has no one-move guard repair in this neighborhood.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    seed = payload["seed"]
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: GUARD_REPAIR_THIRD_PROBE",
        "---",
        "",
        f"# {payload['report_id']}: guard-repair next-move probe",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Source: `{payload['source']}` candidate `{payload['candidate']}`.",
        f"Seed: score {seed['score']} a57={seed['rec']['a57_xor_hw']} D61={seed['rec']['D61_hw']} chart=`{','.join(seed['rec']['chart_top2'])}`.",
        f"Third moves scanned: {payload['scanned']}.",
        "",
        "| Candidate | Score | a57 | D61 | Chart | Move |",
        "|---|---:|---:|---:|---|---|",
    ]
    for label in ("best_score", "best_guard", "best_preserve"):
        row = payload[label]
        lines.append(
            f"| `{label}` | {row['score']} | {row['rec']['a57_xor_hw']} | "
            f"{row['rec']['D61_hw']} | `{','.join(row['rec']['chart_top2'])}` | "
            f"`{row['flips']}` |"
        )
    lines.extend([
        "",
        "## Counts",
        "",
        f"- a57-lowering moves: {payload['a57_lower_count']}",
        f"- chart-preserving moves: {payload['chart_preserve_count']}",
        f"- D61<=seed moves: {payload['d61_preserve_count']}",
        f"- a57-lowering with chart and D61<=seed: {payload['guard_repair_preserve_count']}",
        f"- target a57/chart/D61 moves: {payload['target_preserve_count']}",
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
    ap.add_argument(
        "--candidate",
        choices=["best_d61", "best_score", "best_repair", "best_guard", "best_preserve"],
        default="best_d61",
    )
    ap.add_argument("--active-words", default="0-15")
    ap.add_argument("--modes", default="raw_m1,raw_m2,common_xor,common_add")
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--alpha", type=float, default=4.0)
    ap.add_argument("--beta", type=float, default=1.0)
    ap.add_argument("--gamma", type=float, default=8.0)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--report-id", default="F367")
    ap.add_argument("--target-a57", type=int, default=None)
    ap.add_argument("--target-d61", type=int, default=None)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    source = read_json(args.source)
    seed = source[args.candidate]
    seed_M1 = from_hex_words(seed["M1"])
    seed_M2 = from_hex_words(seed["M2"])
    active_words = parse_active_words(args.active_words)
    score_kwargs = {
        "atlas_alpha": args.alpha,
        "atlas_beta": args.beta,
        "atlas_gamma": args.gamma,
        "atlas_delta": args.delta,
    }
    seed_rec = atlas_evaluate(seed_M1, seed_M2)
    seed_score = atlas_score(seed_rec, **score_kwargs)
    seed_candidate = compact_candidate(seed_M1, seed_M2, seed_rec, seed_score, [], seed_score, seed_rec)

    t0 = time.time()
    candidates = []
    scanned = 0
    for mode in [part.strip() for part in args.modes.split(",") if part.strip()]:
        for move in move_positions(active_words, mode):
            cand_M1, cand_M2 = apply_move(seed_M1, seed_M2, [move])
            rec = atlas_evaluate(cand_M1, cand_M2)
            score = atlas_score(rec, **score_kwargs)
            candidates.append(compact_candidate(
                cand_M1,
                cand_M2,
                rec,
                score,
                [tuple(move)],
                seed_score,
                seed_rec,
            ))
            scanned += 1
    seed_a57 = seed_rec["a57_xor_hw"]
    seed_d61 = seed_rec["D61_hw"]
    target_a57 = seed_a57 if args.target_a57 is None else args.target_a57
    target_d61 = seed_d61 if args.target_d61 is None else args.target_d61
    best_score = min(candidates, key=rank_score)
    best_guard = min(candidates, key=rank_guard)
    best_preserve = min(candidates, key=rank_preserve)
    payload = {
        "report_id": args.report_id,
        "source": repo_path(args.source),
        "candidate": args.candidate,
        "active_words": active_words,
        "score_kwargs": score_kwargs,
        "seed": seed_candidate,
        "scanned": scanned,
        "a57_lower_count": sum(1 for row in candidates if row["rec"]["a57_xor_hw"] < seed_a57),
        "chart_preserve_count": sum(1 for row in candidates if row["rec"]["chart_match"]),
        "d61_preserve_count": sum(1 for row in candidates if row["rec"]["D61_hw"] <= seed_d61),
        "guard_repair_preserve_count": sum(
            1 for row in candidates
            if row["rec"]["a57_xor_hw"] < seed_a57
            and row["rec"]["chart_match"]
            and row["rec"]["D61_hw"] <= seed_d61
        ),
        "target_a57": target_a57,
        "target_d61": target_d61,
        "target_preserve_count": sum(
            1 for row in candidates
            if row["rec"]["a57_xor_hw"] <= target_a57
            and row["rec"]["chart_match"]
            and row["rec"]["D61_hw"] <= target_d61
        ),
        "best_score": best_score,
        "best_guard": best_guard,
        "best_preserve": best_preserve,
        "top_by_score": sorted(candidates, key=rank_score)[:args.top],
        "top_by_guard": sorted(candidates, key=rank_guard)[:args.top],
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
        "seed": payload["seed"]["rec"],
        "best_score": payload["best_score"]["rec"],
        "best_score_value": payload["best_score"]["score"],
        "best_guard": payload["best_guard"]["rec"],
        "best_guard_score": payload["best_guard"]["score"],
        "best_preserve": payload["best_preserve"]["rec"],
        "best_preserve_score": payload["best_preserve"]["score"],
        "counts": {
            "a57_lower": payload["a57_lower_count"],
            "chart_preserve": payload["chart_preserve_count"],
            "d61_preserve": payload["d61_preserve_count"],
            "guard_repair_preserve": payload["guard_repair_preserve_count"],
        },
        "wall_seconds": payload["wall_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
