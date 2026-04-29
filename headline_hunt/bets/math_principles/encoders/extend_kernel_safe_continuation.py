#!/usr/bin/env python3
"""
extend_kernel_safe_continuation.py - Extend strict-kernel atlas descendants.
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
)
from headline_hunt.bets.math_principles.encoders.continue_atlas_kernel_safe import (  # noqa: E402
    diff_summary,
    is_kernel_pair,
    run_restart,
)


DEFAULT_SOURCE = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F369_kernel_safe_pareto_continuation.json"
)
DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F370_kernel_safe_descendant_continuation.json"
)


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def selected_rows(source: dict[str, Any], labels: list[str]) -> list[dict[str, Any]]:
    rows = source.get("representative_runs", [])
    by_label = {row["label"]: row for row in rows}
    out = []
    for label in labels:
        if label not in by_label:
            raise ValueError(f"source has no representative run {label!r}")
        out.append(by_label[label])
    return out


def best_run(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return min(rows, key=lambda row: row["best_score"]["score"])


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    improved = [row for row in payload["descendant_runs"] if row["best"]["score"] < row["seed"]["score"]]
    if any(row["best"]["rec"]["a57_xor_hw"] == 0 for row in payload["descendant_runs"]):
        return (
            "kernel_descendant_found_a57_zero",
            "Promote the strict-kernel candidate to chamber atlas verification.",
        )
    if improved:
        return (
            "kernel_descendant_improved",
            "Continue the improved strict-kernel descendant with the same guard.",
        )
    return (
        "kernel_descendant_no_improvement",
        "The strict-kernel descendant is locally stiff at this continuation budget.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: KERNEL_SAFE_DESCENDANT_CONTINUATION",
        "---",
        "",
        "# F370: kernel-safe descendant continuation",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Source: `{payload['source']}`.",
        "",
        "| Label | Seed score | Seed a57 | Seed D61 | Best score | Best a57 | Best D61 | Invalid moves |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["descendant_runs"]:
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
    ap.add_argument("source", nargs="?", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--labels", default="best_D61")
    ap.add_argument("--active-words", default="0-15")
    ap.add_argument("--modes", default="common_xor,common_add")
    ap.add_argument("--max-flips", type=int, default=2)
    ap.add_argument("--restarts", type=int, default=4)
    ap.add_argument("--iterations", type=int, default=30000)
    ap.add_argument("--init-kicks", type=int, default=1)
    ap.add_argument("--seed", type=int, default=37000)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    source = read_json(args.source)
    kernel_bit = int(source.get("kernel_bit", 31))
    labels = [part.strip() for part in args.labels.split(",") if part.strip()]
    active_words = parse_active_words(args.active_words)
    modes = [part.strip() for part in args.modes.split(",") if part.strip()]
    if any(mode not in {"common_xor", "common_add"} for mode in modes):
        raise SystemExit("kernel-safe extender only accepts common_xor/common_add modes")
    score_kwargs = source.get("score_kwargs") or {
        "atlas_alpha": 4.0,
        "atlas_beta": 1.0,
        "atlas_gamma": 8.0,
        "atlas_delta": 0.05,
    }
    rng = random.Random(args.seed)
    t0 = time.time()
    descendant_runs = []
    for row in selected_rows(source, labels):
        seed_candidate = row["best"]
        M1 = from_hex_words(seed_candidate["M1"])
        M2 = from_hex_words(seed_candidate["M2"])
        if not is_kernel_pair(M1, M2, kernel_bit):
            raise ValueError(f"source seed {row['label']} drifted: {diff_summary(M1, M2)}")
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
            raise RuntimeError(f"internal: best for {row['label']} drifted")
        descendant_runs.append({
            "label": row["label"],
            "seed": seed,
            "best": best,
            "restarts": restarts,
            "invalid_moves": sum(run["invalid_moves"] for run in restarts),
        })

    payload = {
        "report_id": "F370",
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
        "score_kwargs": score_kwargs,
        "descendant_runs": descendant_runs,
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
        "descendants": [
            {
                "label": row["label"],
                "seed_score": row["seed"]["score"],
                "best_score": row["best"]["score"],
                "best_rec": row["best"]["rec"],
                "invalid_moves": row["invalid_moves"],
            }
            for row in descendant_runs
        ],
        "wall_seconds": payload["wall_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
