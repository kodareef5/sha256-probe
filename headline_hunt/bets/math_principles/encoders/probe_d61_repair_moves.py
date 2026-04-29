#!/usr/bin/env python3
"""
probe_d61_repair_moves.py - Pair a D61-lowering move with repair moves.
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
    / "headline_hunt/bets/math_principles/results/20260429_F365_descendant_neighborhood_r1.json"
)
DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F366_d61_repair_pair_probe.json"
)


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def flip_tuple(row: dict[str, Any]) -> tuple[Any, ...]:
    mode = row["mode"]
    if mode == "common_add":
        return (mode, row["word"], row["bit"], row["sign"])
    return (mode, row["word"], row["bit"])


def rank_score(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        row["score"],
        rec["a57_xor_hw"],
        0 if rec["chart_match"] else 1,
        rec["D61_hw"],
        rec["tail63_state_diff_hw"],
    )


def rank_repair(row: dict[str, Any]) -> tuple[Any, ...]:
    rec = row["rec"]
    return (
        0 if rec["chart_match"] else 1,
        rec["a57_xor_hw"],
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


def write_md(path: Path, payload: dict[str, Any]) -> None:
    base = payload["base"]
    fixed = payload["fixed_move_candidate"]
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: D61_REPAIR_PAIR_PROBE",
        "---",
        "",
        "# F366: D61-lowering repair pair probe",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Base: score {base['score']} a57={base['rec']['a57_xor_hw']} D61={base['rec']['D61_hw']} chart=`{','.join(base['rec']['chart_top2'])}`.",
        f"Fixed D61 move: score {fixed['score']} a57={fixed['rec']['a57_xor_hw']} D61={fixed['rec']['D61_hw']} chart=`{','.join(fixed['rec']['chart_top2'])}`.",
        f"Repair moves scanned: {payload['scanned']}.",
        "",
        "| Candidate | Score | a57 | D61 | Chart | Move |",
        "|---|---:|---:|---:|---|---|",
    ]
    for label in ("best_score", "best_repair", "best_d61"):
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
        f"- Better than fixed D61 move: {payload['better_than_fixed_count']}",
        f"- Better than original base: {payload['better_than_base_count']}",
        f"- Chart repaired: {payload['chart_repaired_count']}",
        f"- D61 preserved at <= fixed: {payload['d61_preserved_count']}",
        "",
        "## Decision",
        "",
        payload["decision"],
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    base = payload["base"]
    if payload["better_than_base_count"]:
        return (
            "repair_pair_found_base_descent",
            "Promote the best pair move as the next atlas continuation seed.",
        )
    if payload["chart_repaired_count"] and payload["d61_preserved_count"]:
        return (
            "repair_pair_chart_repairs_with_d61_preserved",
            "Use the repaired D61-preserving pair as a new front member, even though scalar score is worse.",
        )
    if payload["best_d61"]["rec"]["D61_hw"] < base["rec"]["D61_hw"]:
        return (
            "repair_pair_keeps_D61_gain_only",
            "D61 can be lowered by pairs, but chart/guard repair still needs a larger move family.",
        )
    return (
        "repair_pair_no_useful_repair",
        "The forced D61-lowering bit is not repairable by one additional message move.",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", nargs="?", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--active-words", default="0-15")
    ap.add_argument("--modes", default="raw_m1,raw_m2,common_xor,common_add")
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--alpha", type=float, default=4.0)
    ap.add_argument("--beta", type=float, default=1.0)
    ap.add_argument("--gamma", type=float, default=8.0)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    source = read_json(args.source)
    if not source.get("best_d61_lower"):
        raise SystemExit("source has no best_d61_lower move")
    active_words = parse_active_words(args.active_words)
    score_kwargs = {
        "atlas_alpha": args.alpha,
        "atlas_beta": args.beta,
        "atlas_gamma": args.gamma,
        "atlas_delta": args.delta,
    }
    base = source["base"]
    base_M1 = from_hex_words(base["M1"])
    base_M2 = from_hex_words(base["M2"])
    base_rec = atlas_evaluate(base_M1, base_M2)
    base_score = atlas_score(base_rec, **score_kwargs)
    fixed_flips = [flip_tuple(row) for row in source["best_d61_lower"]["flips"]]
    fixed_M1, fixed_M2 = apply_move(base_M1, base_M2, fixed_flips)
    fixed_rec = atlas_evaluate(fixed_M1, fixed_M2)
    fixed_score = atlas_score(fixed_rec, **score_kwargs)
    fixed_candidate = compact_candidate(
        fixed_M1,
        fixed_M2,
        fixed_rec,
        fixed_score,
        fixed_flips,
        base_score,
        base_rec,
    )

    t0 = time.time()
    candidates = []
    scanned = 0
    for mode in [part.strip() for part in args.modes.split(",") if part.strip()]:
        for move in move_positions(active_words, mode):
            cand_M1, cand_M2 = apply_move(fixed_M1, fixed_M2, [move])
            if cand_M1 == base_M1 and cand_M2 == base_M2:
                continue
            rec = atlas_evaluate(cand_M1, cand_M2)
            score = atlas_score(rec, **score_kwargs)
            candidates.append(compact_candidate(
                cand_M1,
                cand_M2,
                rec,
                score,
                fixed_flips + [move],
                base_score,
                base_rec,
            ))
            scanned += 1
    best_score = min(candidates, key=rank_score)
    best_repair = min(candidates, key=rank_repair)
    best_d61 = min(candidates, key=rank_d61)
    payload = {
        "report_id": "F366",
        "source": repo_path(args.source),
        "active_words": active_words,
        "score_kwargs": score_kwargs,
        "base": compact_candidate(base_M1, base_M2, base_rec, base_score, [], base_score, base_rec),
        "fixed_move_candidate": fixed_candidate,
        "scanned": scanned,
        "better_than_fixed_count": sum(1 for row in candidates if row["score"] < fixed_score),
        "better_than_base_count": sum(1 for row in candidates if row["score"] < base_score),
        "chart_repaired_count": sum(1 for row in candidates if row["rec"]["chart_match"]),
        "d61_preserved_count": sum(1 for row in candidates if row["rec"]["D61_hw"] <= fixed_rec["D61_hw"]),
        "best_score": best_score,
        "best_repair": best_repair,
        "best_d61": best_d61,
        "top_by_score": sorted(candidates, key=rank_score)[:args.top],
        "top_by_d61": sorted(candidates, key=rank_d61)[:args.top],
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
        "fixed": payload["fixed_move_candidate"]["rec"],
        "best_score": payload["best_score"]["rec"],
        "best_score_value": payload["best_score"]["score"],
        "best_repair": payload["best_repair"]["rec"],
        "best_repair_score": payload["best_repair"]["score"],
        "best_d61": payload["best_d61"]["rec"],
        "best_d61_score": payload["best_d61"]["score"],
        "counts": {
            "better_than_fixed": payload["better_than_fixed_count"],
            "better_than_base": payload["better_than_base_count"],
            "chart_repaired": payload["chart_repaired_count"],
            "d61_preserved": payload["d61_preserved_count"],
        },
        "wall_seconds": payload["wall_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
