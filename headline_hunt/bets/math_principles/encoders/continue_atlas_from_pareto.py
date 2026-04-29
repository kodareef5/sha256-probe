#!/usr/bin/env python3
"""
continue_atlas_from_pareto.py - Atlas continuation from F360 front members.
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

from headline_hunt.bets.block2_wang.encoders.search_schedule_space import (  # noqa: E402
    atlas_evaluate,
    atlas_score,
    parse_active_words,
)
from headline_hunt.bets.math_principles.encoders.continue_atlas_from_seed import (  # noqa: E402
    compact_candidate,
    from_hex_words,
    repo_path,
    run_restart,
)


DEFAULT_FRONT = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F360_chamber_seed_pareto_front.json"
)
DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F361_pareto_seeded_atlas_continuation.json"
)


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def select_representatives(front: dict[str, Any], labels: list[str]) -> list[tuple[str, dict[str, Any]]]:
    reps = front.get("representatives", {})
    out = []
    for label in labels:
        if label not in reps:
            raise ValueError(f"front has no representative {label!r}")
        out.append((label, reps[label]))
    return out


def seed_summary(label: str, row: dict[str, Any], score_kwargs: dict[str, float]) -> dict[str, Any]:
    M1 = from_hex_words(row["M1"])
    M2 = from_hex_words(row["M2_kernel"])
    rec = atlas_evaluate(M1, M2)
    score = atlas_score(rec, **score_kwargs)
    out = compact_candidate(M1, M2, rec, score)
    out["label"] = label
    out["front_metrics"] = row.get("metrics", {})
    return out


def best_run(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return min(rows, key=lambda row: row["best_score"]["score"])


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    improved = [
        row for row in payload["representative_runs"]
        if row["best"]["score"] < row["seed"]["score"]
    ]
    if any(row["best"]["rec"]["a57_xor_hw"] == 0 for row in payload["representative_runs"]):
        return (
            "pareto_continuation_found_a57_zero",
            "Promote the winning representative to a chamber atlas check.",
        )
    if improved:
        return (
            "pareto_continuation_improved_atlas_loss",
            "Use the improved representative as the next continuation seed and keep the front-member labels attached.",
        )
    return (
        "pareto_continuation_no_descent",
        "The F360 representatives are useful diagnostics, but this move set did not descend from them at this budget.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: PARETO_SEEDED_ATLAS_CONTINUATION",
        "---",
        "",
        "# F361: Pareto-seeded atlas continuation",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Front: `{payload['front']}`.",
        "",
        "| Representative | Seed score | Seed a57 | Seed D61 | Best score | Best a57 | Best D61 | Best chart |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["representative_runs"]:
        seed = row["seed"]
        best = row["best"]
        lines.append(
            f"| `{row['label']}` | {seed['score']} | {seed['rec']['a57_xor_hw']} | "
            f"{seed['rec']['D61_hw']} | {best['score']} | {best['rec']['a57_xor_hw']} | "
            f"{best['rec']['D61_hw']} | `{','.join(best['rec']['chart_top2'])}` |"
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
    ap.add_argument("--modes", default="common_xor,common_add,raw_m2")
    ap.add_argument("--max-flips", type=int, default=2)
    ap.add_argument("--restarts", type=int, default=3)
    ap.add_argument("--iterations", type=int, default=15000)
    ap.add_argument("--init-kicks", type=int, default=2)
    ap.add_argument("--seed", type=int, default=36100)
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
        seed = seed_summary(label, row, score_kwargs)
        M1 = from_hex_words(row["M1"])
        M2 = from_hex_words(row["M2_kernel"])
        restarts = [
            run_restart(
                M1,
                M2,
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
        representative_runs.append({
            "label": label,
            "seed": seed,
            "best": best,
            "restarts": restarts,
        })

    payload = {
        "report_id": "F361",
        "front": repo_path(args.front),
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
            }
            for row in representative_runs
        ],
        "wall_seconds": payload["wall_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
