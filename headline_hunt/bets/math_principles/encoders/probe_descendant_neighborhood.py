#!/usr/bin/env python3
"""
probe_descendant_neighborhood.py - Deterministic local probes for descendants.
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
    compact_candidate,
    probe_mode,
)


DEFAULT_SOURCE = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F362_pareto_descendant_continuation.json"
)
DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F365_descendant_neighborhood_r1.json"
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


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    all_top = [candidate for mode in payload["modes"] for candidate in mode["top"]]
    base = payload["base"]
    if any(candidate["rec"]["a57_xor_hw"] == 0 for candidate in all_top):
        return (
            "descendant_probe_found_a57_zero",
            "Promote the local move and rerun continuation from it.",
        )
    if any(candidate["score"] < base["score"] for candidate in all_top):
        return (
            "descendant_probe_found_descent",
            "Use the best deterministic move as the next continuation seed.",
        )
    if any(candidate["rec"]["D61_hw"] < base["rec"]["D61_hw"] for candidate in all_top):
        return (
            "descendant_probe_found_D61_only_descent",
            "D61 can move locally, but not under the current scalar atlas objective.",
        )
    return (
        "descendant_probe_no_local_descent",
        "No tested single-coordinate move improves the basin; use multi-coordinate or schedule-space moves next.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    base = payload["base"]
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: DESCENDANT_NEIGHBORHOOD_PROBE",
        "---",
        "",
        f"# {payload['report_id']}: descendant neighborhood probe",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Source: `{payload['source']}` label `{payload['label']}`.",
        f"Base score: {base['score']} a57={base['rec']['a57_xor_hw']} D61={base['rec']['D61_hw']} chart=`{','.join(base['rec']['chart_top2'])}`.",
        f"D61-only lower moves in retained top sets: {payload['d61_lower_count']}.",
        "",
        "| Mode | Radius | Scanned | Score-improved | a57-improved | Best score | Best a57 | Best D61 | Best chart |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["modes"]:
        best = row["top"][0]
        lines.append(
            f"| `{row['mode']}` | {row['radius']} | {row['scanned']} | "
            f"{row['improved_score_count']} | {row['a57_improved_count']} | "
            f"{best['score']} | {best['rec']['a57_xor_hw']} | "
            f"{best['rec']['D61_hw']} | `{','.join(best['rec']['chart_top2'])}` |"
        )
    lines.extend([
        "",
        "## D61-Only Lower Moves",
        "",
    ])
    if payload["best_d61_lower"]:
        row = payload["best_d61_lower"]
        lines.extend([
            f"Best D61-only lower move: score {row['score']} with a57={row['rec']['a57_xor_hw']}, D61={row['rec']['D61_hw']}, chart=`{','.join(row['rec']['chart_top2'])}`.",
            f"Move: `{row['flips']}`.",
            "",
        ])
    else:
        lines.extend(["None retained in top sets.", ""])
    lines.extend([
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
    ap.add_argument("--modes", default="raw_m1,raw_m2,common_xor,common_add")
    ap.add_argument("--radius", type=int, default=1)
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--alpha", type=float, default=4.0)
    ap.add_argument("--beta", type=float, default=1.0)
    ap.add_argument("--gamma", type=float, default=8.0)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--report-id", default="F365")
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    if args.radius < 1 or args.radius > 2:
        raise SystemExit("--radius must be 1 or 2")
    source = read_json(args.source)
    row = selected_row(source, args.label)
    seed = row["best"]
    base_M1 = from_hex_words(seed["M1"])
    base_M2 = from_hex_words(seed["M2"])
    active_words = parse_active_words(args.active_words)
    score_kwargs = {
        "atlas_alpha": args.alpha,
        "atlas_beta": args.beta,
        "atlas_gamma": args.gamma,
        "atlas_delta": args.delta,
    }
    base_rec = atlas_evaluate(base_M1, base_M2)
    base_score = atlas_score(base_rec, **score_kwargs)
    t0 = time.time()
    payload = {
        "report_id": args.report_id,
        "source": repo_path(args.source),
        "label": args.label,
        "active_words": active_words,
        "score_kwargs": score_kwargs,
        "base": compact_candidate(base_M1, base_M2, base_rec, base_score, [], base_score, base_rec),
        "modes": [
            probe_mode(
                base_M1,
                base_M2,
                active_words,
                mode.strip(),
                args.radius,
                score_kwargs,
                args.top,
            )
            for mode in args.modes.split(",")
            if mode.strip()
        ],
        "wall_seconds": None,
    }
    payload["wall_seconds"] = round(time.time() - t0, 6)
    all_top = [candidate for mode in payload["modes"] for candidate in mode["top"]]
    d61_lower = [
        candidate for candidate in all_top
        if candidate["rec"]["D61_hw"] < payload["base"]["rec"]["D61_hw"]
    ]
    d61_lower.sort(key=lambda row: (
        row["rec"]["D61_hw"],
        row["score"],
        row["rec"]["a57_xor_hw"],
    ))
    payload["d61_lower_count"] = len(d61_lower)
    payload["best_d61_lower"] = d61_lower[0] if d61_lower else None
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
        "modes": [
            {
                "mode": row["mode"],
                "scanned": row["scanned"],
                "best": row["top"][0]["rec"],
                "best_score": row["top"][0]["score"],
                "improved_score_count": row["improved_score_count"],
            }
            for row in payload["modes"]
        ],
        "wall_seconds": payload["wall_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
