#!/usr/bin/env python3
"""
probe_atlas_neighborhood.py - Local move probes around atlas-loss candidates.
"""

from __future__ import annotations

import argparse
import itertools
import json
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from headline_hunt.bets.block2_wang.encoders.search_schedule_space import (  # noqa: E402
    MASK,
    atlas_evaluate,
    atlas_score,
    parse_active_words,
)


DEFAULT_OUT = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F353_atlas_neighborhood_probe.json"
)


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def from_hex_words(words: list[str]) -> list[int]:
    return [int(word, 16) for word in words]


def chart_tuple(value: Any) -> tuple[str, str]:
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return str(value[0]), str(value[1])
    return "?", "?"


def is_chart_match(value: Any) -> bool:
    return chart_tuple(value) in {("dh", "dCh"), ("dCh", "dh")}


def select_restart(run: dict[str, Any], selector: str) -> dict[str, Any]:
    restarts = list(run.get("restarts", []))
    if not restarts:
        raise ValueError("run JSON has no restarts")
    if selector == "best_score":
        return min(restarts, key=lambda row: row["best_score"])
    if selector == "best_a57":
        return min(
            restarts,
            key=lambda row: (
                row["best_rec"]["a57_xor_hw"],
                0 if is_chart_match(row["best_rec"].get("chart_top2")) else 1,
                row["best_rec"]["D61_hw"],
                row["best_score"],
            ),
        )
    if selector == "best_chart":
        chart_rows = [
            row for row in restarts
            if is_chart_match(row["best_rec"].get("chart_top2"))
        ]
        if not chart_rows:
            raise ValueError("no restart best is chart-compatible")
        return min(
            chart_rows,
            key=lambda row: (
                row["best_rec"]["a57_xor_hw"],
                row["best_rec"]["D61_hw"],
                row["best_score"],
            ),
        )
    raise ValueError(f"unknown selector {selector!r}")


def move_positions(active_words: list[int], mode: str) -> list[tuple[Any, ...]]:
    if mode == "raw_m2":
        return [("raw_m2", word, bit) for word in active_words for bit in range(32)]
    if mode == "raw_m1":
        return [("raw_m1", word, bit) for word in active_words for bit in range(32)]
    if mode == "common_xor":
        return [("common_xor", word, bit) for word in active_words for bit in range(32)]
    if mode == "common_add":
        return [
            ("common_add", word, bit, sign)
            for word in active_words
            for bit in range(32)
            for sign in (1, -1)
        ]
    raise ValueError(f"unknown mode {mode!r}")


def apply_move(
    M1: list[int],
    M2: list[int],
    flips: Iterable[tuple[Any, ...]],
) -> tuple[list[int], list[int]]:
    out1 = list(M1)
    out2 = list(M2)
    for item in flips:
        mode = item[0]
        word = int(item[1])
        bit = int(item[2])
        if mode == "raw_m2":
            out2[word] = (out2[word] ^ (1 << bit)) & MASK
        elif mode == "raw_m1":
            out1[word] = (out1[word] ^ (1 << bit)) & MASK
        elif mode == "common_xor":
            out1[word] = (out1[word] ^ (1 << bit)) & MASK
            out2[word] = (out2[word] ^ (1 << bit)) & MASK
        elif mode == "common_add":
            sign = int(item[3])
            delta = sign * (1 << bit)
            out1[word] = (out1[word] + delta) & MASK
            out2[word] = (out2[word] + delta) & MASK
        else:
            raise ValueError(f"unknown move mode {mode!r}")
    return out1, out2


def move_label(flips: Iterable[tuple[Any, ...]]) -> list[dict[str, Any]]:
    out = []
    for item in flips:
        row = {"mode": item[0], "word": item[1], "bit": item[2]}
        if len(item) > 3:
            row["sign"] = item[3]
        out.append(row)
    return out


def rank_key(candidate: dict[str, Any]) -> tuple[Any, ...]:
    rec = candidate["rec"]
    return (
        candidate["score"],
        rec["a57_xor_hw"],
        0 if is_chart_match(rec.get("chart_top2")) else 1,
        rec["D61_hw"],
        rec["tail63_state_diff_hw"],
    )


def keep_top(top: list[dict[str, Any]], candidate: dict[str, Any], n: int) -> None:
    top.append(candidate)
    top.sort(key=rank_key)
    if len(top) > n:
        top.pop()


def compact_candidate(
    M1: list[int],
    M2: list[int],
    rec: dict[str, Any],
    score: float,
    flips: list[tuple[Any, ...]],
    base_score: float,
    base_rec: dict[str, Any],
) -> dict[str, Any]:
    return {
        "score": round(score, 6),
        "delta_score": round(score - base_score, 6),
        "rec": {
            "a57_xor_hw": rec["a57_xor_hw"],
            "D61_hw": rec["D61_hw"],
            "chart_top2": list(chart_tuple(rec.get("chart_top2"))),
            "chart_match": is_chart_match(rec.get("chart_top2")),
            "tail63_state_diff_hw": rec["tail63_state_diff_hw"],
        },
        "delta_rec": {
            "a57_xor_hw": rec["a57_xor_hw"] - base_rec["a57_xor_hw"],
            "D61_hw": rec["D61_hw"] - base_rec["D61_hw"],
            "tail63_state_diff_hw": rec["tail63_state_diff_hw"] - base_rec["tail63_state_diff_hw"],
            "chart_changed": chart_tuple(rec.get("chart_top2")) != chart_tuple(base_rec.get("chart_top2")),
        },
        "flips": move_label(flips),
        "M1": [f"0x{word:08x}" for word in M1],
        "M2": [f"0x{word:08x}" for word in M2],
    }


def probe_mode(
    base_M1: list[int],
    base_M2: list[int],
    active_words: list[int],
    mode: str,
    radius: int,
    score_kwargs: dict[str, float],
    top_n: int,
) -> dict[str, Any]:
    base_rec = atlas_evaluate(base_M1, base_M2)
    base_score = atlas_score(base_rec, **score_kwargs)
    positions = move_positions(active_words, mode)
    top: list[dict[str, Any]] = []
    improved = 0
    chart_improved = 0
    a57_improved = 0
    scanned = 0
    for r in range(1, radius + 1):
        for flips in itertools.combinations(positions, r):
            cand_M1, cand_M2 = apply_move(base_M1, base_M2, flips)
            rec = atlas_evaluate(cand_M1, cand_M2)
            score = atlas_score(rec, **score_kwargs)
            scanned += 1
            if score < base_score:
                improved += 1
            if is_chart_match(rec.get("chart_top2")) and not is_chart_match(base_rec.get("chart_top2")):
                chart_improved += 1
            if rec["a57_xor_hw"] < base_rec["a57_xor_hw"]:
                a57_improved += 1
            keep_top(
                top,
                compact_candidate(cand_M1, cand_M2, rec, score, list(flips), base_score, base_rec),
                top_n,
            )
    chart_hist = Counter(",".join(candidate["rec"]["chart_top2"]) for candidate in top)
    return {
        "mode": mode,
        "radius": radius,
        "positions": len(positions),
        "scanned": scanned,
        "improved_score_count": improved,
        "a57_improved_count": a57_improved,
        "chart_improved_count": chart_improved,
        "top_chart_histogram": dict(sorted(chart_hist.items())),
        "top": top,
    }


def write_md(path: Path, payload: dict[str, Any]) -> None:
    base = payload["base"]
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: ATLAS_NEIGHBORHOOD_PROBE",
        "---",
        "",
        f"# {payload['report_id']}: atlas-neighborhood probe",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Source: `{payload['source_path']}` selector `{payload['selector']}`.",
        f"Base score: {base['score']} a57={base['rec']['a57_xor_hw']} D61={base['rec']['D61_hw']} chart=`{','.join(base['rec']['chart_top2'])}`.",
        "",
        "| Mode | Radius | Scanned | Score-improved | a57-improved | Chart-improved | Best score | Best a57 | Best chart |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["modes"]:
        best = row["top"][0]
        lines.append(
            f"| `{row['mode']}` | {row['radius']} | {row['scanned']} | "
            f"{row['improved_score_count']} | {row['a57_improved_count']} | "
            f"{row['chart_improved_count']} | {best['score']} | "
            f"{best['rec']['a57_xor_hw']} | `{','.join(best['rec']['chart_top2'])}` |"
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


def make_verdict(payload: dict[str, Any]) -> tuple[str, str]:
    all_top = [candidate for mode in payload["modes"] for candidate in mode["top"]]
    base = payload["base"]
    if any(candidate["rec"]["a57_xor_hw"] == 0 for candidate in all_top):
        return (
            "local_probe_found_a57_zero",
            "Promote the best local move immediately and rerun stochastic atlas search from it.",
        )
    if any(
        candidate["rec"]["chart_match"]
        and candidate["rec"]["a57_xor_hw"] < base["rec"]["a57_xor_hw"]
        for candidate in all_top
    ):
        return (
            "local_probe_reduced_a57_inside_chart",
            "Use this move family as a deterministic polish step after atlas-loss search.",
        )
    if any(candidate["score"] < base["score"] for candidate in all_top):
        return (
            "local_probe_score_improves_only",
            "Local message moves can polish the scalar atlas loss, but the missing ingredient is still a chart-aware proposal.",
        )
    return (
        "local_probe_no_descent",
        "This basin is locally stiff under the tested message moves; next try schedule-coordinate or two-side structured moves.",
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", type=Path, help="Atlas-loss search JSON.")
    ap.add_argument("--selector", choices=["best_score", "best_a57", "best_chart"], default="best_a57")
    ap.add_argument("--active-words", default=None,
                    help="Comma/range list; default uses source active_words.")
    ap.add_argument("--modes", default="raw_m2,common_xor,common_add")
    ap.add_argument("--radius", type=int, default=1)
    ap.add_argument("--top", type=int, default=12)
    ap.add_argument("--alpha", type=float, default=None)
    ap.add_argument("--beta", type=float, default=None)
    ap.add_argument("--gamma", type=float, default=None)
    ap.add_argument("--delta", type=float, default=None)
    ap.add_argument("--report-id", default="F353")
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    if args.radius < 1 or args.radius > 2:
        raise SystemExit("--radius must be 1 or 2")
    run = read_json(args.source)
    selected = select_restart(run, args.selector)
    base_M1 = from_hex_words(selected["M1"])
    base_M2 = from_hex_words(selected["best_M2"])
    active_words = (
        parse_active_words(args.active_words)
        if args.active_words
        else [int(word) for word in run.get("active_words", [])]
    )
    run_args = run.get("args", {})
    score_kwargs = {
        "atlas_alpha": args.alpha if args.alpha is not None else float(run_args.get("alpha", 4.0)),
        "atlas_beta": args.beta if args.beta is not None else float(run_args.get("beta", 1.0)),
        "atlas_gamma": args.gamma if args.gamma is not None else float(run_args.get("gamma", 8.0)),
        "atlas_delta": args.delta if args.delta is not None else float(run_args.get("delta", 0.05)),
    }
    base_rec = atlas_evaluate(base_M1, base_M2)
    base_score = atlas_score(base_rec, **score_kwargs)
    t0 = time.time()
    payload = {
        "report_id": args.report_id,
        "source_path": repo_path(args.source),
        "selector": args.selector,
        "selected_restart": selected.get("restart"),
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
    }
    payload["wall_seconds"] = round(time.time() - t0, 6)
    payload["verdict"], payload["decision"] = make_verdict(payload)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    out_md = args.out_md or args.out_json.with_suffix(".md")
    write_md(out_md, payload)
    print(json.dumps({
        "verdict": payload["verdict"],
        "selected_restart": payload["selected_restart"],
        "base": payload["base"],
        "modes": [
            {
                "mode": row["mode"],
                "scanned": row["scanned"],
                "best": row["top"][0],
            }
            for row in payload["modes"]
        ],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
