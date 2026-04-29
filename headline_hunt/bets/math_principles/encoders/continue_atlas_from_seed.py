#!/usr/bin/env python3
"""
continue_atlas_from_seed.py - Stochastic atlas-loss continuation from a probe seed.
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


DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F355_seeded_atlas_commonmode_continuation.json"
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


def chart_match(value: Any) -> bool:
    return chart_tuple(value) in {("dh", "dCh"), ("dCh", "dh")}


def candidate_rank(candidate: dict[str, Any], selector: str) -> tuple[Any, ...]:
    rec = candidate["rec"]
    if selector == "best_score":
        return (
            candidate["score"],
            rec["a57_xor_hw"],
            0 if rec.get("chart_match") else 1,
            rec["D61_hw"],
        )
    if selector == "best_a57":
        return (
            rec["a57_xor_hw"],
            0 if rec.get("chart_match") else 1,
            rec["D61_hw"],
            candidate["score"],
        )
    if selector == "best_chart":
        return (
            0 if rec.get("chart_match") else 1,
            rec["a57_xor_hw"],
            rec["D61_hw"],
            candidate["score"],
        )
    raise ValueError(f"unknown selector {selector!r}")


def select_probe_candidate(probe: dict[str, Any], selector: str) -> dict[str, Any]:
    candidates = [
        candidate
        for mode in probe.get("modes", [])
        for candidate in mode.get("top", [])
    ]
    if not candidates:
        raise ValueError("probe JSON has no candidates in modes[].top")
    return min(candidates, key=lambda candidate: candidate_rank(candidate, selector))


def random_flip(
    rng: random.Random,
    active_words: list[int],
    modes: list[str],
) -> tuple[Any, ...]:
    mode = rng.choice(modes)
    word = rng.choice(active_words)
    bit = rng.randrange(32)
    if mode == "common_add":
        return (mode, word, bit, rng.choice([-1, 1]))
    return (mode, word, bit)


def apply_flips(
    M1: list[int],
    M2: list[int],
    flips: list[tuple[Any, ...]],
) -> tuple[list[int], list[int]]:
    out1 = list(M1)
    out2 = list(M2)
    for flip in flips:
        mode = flip[0]
        word = int(flip[1])
        bit = int(flip[2])
        if mode == "raw_m2":
            out2[word] = (out2[word] ^ (1 << bit)) & MASK
        elif mode == "raw_m1":
            out1[word] = (out1[word] ^ (1 << bit)) & MASK
        elif mode == "common_xor":
            out1[word] = (out1[word] ^ (1 << bit)) & MASK
            out2[word] = (out2[word] ^ (1 << bit)) & MASK
        elif mode == "common_add":
            sign = int(flip[3])
            delta = sign * (1 << bit)
            out1[word] = (out1[word] + delta) & MASK
            out2[word] = (out2[word] + delta) & MASK
        else:
            raise ValueError(f"unknown move mode {mode!r}")
    return out1, out2


def compact_flips(flips: list[tuple[Any, ...]]) -> list[dict[str, Any]]:
    out = []
    for flip in flips:
        row = {"mode": flip[0], "word": flip[1], "bit": flip[2]}
        if len(flip) > 3:
            row["sign"] = flip[3]
        out.append(row)
    return out


def compact_candidate(
    M1: list[int],
    M2: list[int],
    rec: dict[str, Any],
    score: float,
) -> dict[str, Any]:
    return {
        "score": round(score, 6),
        "rec": {
            "a57_xor_hw": rec["a57_xor_hw"],
            "D61_hw": rec["D61_hw"],
            "chart_top2": list(chart_tuple(rec.get("chart_top2"))),
            "chart_match": chart_match(rec.get("chart_top2")),
            "tail63_state_diff_hw": rec["tail63_state_diff_hw"],
        },
        "M1": [f"0x{word:08x}" for word in M1],
        "M2": [f"0x{word:08x}" for word in M2],
    }


def run_restart(
    seed_M1: list[int],
    seed_M2: list[int],
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
    for _ in range(init_kicks if restart else 0):
        flips = [random_flip(rng, active_words, modes)]
        cur_M1, cur_M2 = apply_flips(cur_M1, cur_M2, flips)

    cur_rec = atlas_evaluate(cur_M1, cur_M2)
    cur_score = atlas_score(cur_rec, **score_kwargs)
    best_M1 = list(cur_M1)
    best_M2 = list(cur_M2)
    best_rec = cur_rec
    best_score = cur_score
    best_a57 = compact_candidate(cur_M1, cur_M2, cur_rec, cur_score)
    best_chart = (
        compact_candidate(cur_M1, cur_M2, cur_rec, cur_score)
        if chart_match(cur_rec.get("chart_top2")) else None
    )
    accepts = 0
    improvements = []
    mode_hist: dict[str, int] = {}

    for it in range(iterations):
        n_flips = 1 + (rng.randrange(max_flips) if max_flips > 1 else 0)
        flips = [random_flip(rng, active_words, modes) for _ in range(n_flips)]
        cand_M1, cand_M2 = apply_flips(cur_M1, cur_M2, flips)
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
            for flip in flips:
                mode_hist[flip[0]] = mode_hist.get(flip[0], 0) + 1
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
            if chart_match(cand_rec.get("chart_top2")):
                if best_chart is None or (
                    cand_rec["a57_xor_hw"],
                    cand_rec["D61_hw"],
                    cand_score,
                ) < (
                    best_chart["rec"]["a57_xor_hw"],
                    best_chart["rec"]["D61_hw"],
                    best_chart["score"],
                ):
                    best_chart = compact_candidate(cand_M1, cand_M2, cand_rec, cand_score)

    return {
        "restart": restart,
        "best_score": compact_candidate(best_M1, best_M2, best_rec, best_score),
        "best_a57": best_a57,
        "best_chart": best_chart,
        "accepts": accepts,
        "accepted_mode_histogram": dict(sorted(mode_hist.items())),
        "improvement_tail": improvements[-12:],
    }


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    best = min(payload["restarts"], key=lambda row: row["best_score"]["score"])
    seed = payload["seed_candidate"]
    if best["best_score"]["rec"]["a57_xor_hw"] == 0:
        return (
            "seeded_continuation_found_a57_zero",
            "Promote the candidate to the chamber atlas and run a chain-score check.",
        )
    if best["best_score"]["score"] < seed["score"]:
        return (
            "seeded_continuation_improved_atlas_loss",
            "Common-mode continuation is now a real operator: keep it as a post-atlas polish step and run a longer seeded pass.",
        )
    return (
        "seeded_continuation_no_improvement",
        "The deterministic probe found the local improvement, but stochastic continuation did not extend it at this budget.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: SEEDED_ATLAS_CONTINUATION",
        "---",
        "",
        f"# {payload['report_id']}: seeded atlas common-mode continuation",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Seed score: {payload['seed_candidate']['score']} a57={payload['seed_candidate']['rec']['a57_xor_hw']} D61={payload['seed_candidate']['rec']['D61_hw']} chart=`{','.join(payload['seed_candidate']['rec']['chart_top2'])}`.",
        "",
        "| Restart | Best score | a57 | D61 | Chart | Accepts |",
        "|---:|---:|---:|---:|---|---:|",
    ]
    for row in payload["restarts"]:
        best = row["best_score"]
        lines.append(
            f"| {row['restart']} | {best['score']} | {best['rec']['a57_xor_hw']} | "
            f"{best['rec']['D61_hw']} | `{','.join(best['rec']['chart_top2'])}` | "
            f"{row['accepts']} |"
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
    ap.add_argument("seed_probe", type=Path)
    ap.add_argument("--selector", choices=["best_score", "best_a57", "best_chart"], default="best_score")
    ap.add_argument("--active-words", default=None)
    ap.add_argument("--modes", default="common_xor,common_add,raw_m2")
    ap.add_argument("--max-flips", type=int, default=2)
    ap.add_argument("--restarts", type=int, default=8)
    ap.add_argument("--iterations", type=int, default=50000)
    ap.add_argument("--init-kicks", type=int, default=3)
    ap.add_argument("--seed", type=int, default=35500)
    ap.add_argument("--report-id", default="F355")
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    if args.max_flips < 1 or args.max_flips > 3:
        raise SystemExit("--max-flips must be in [1,3]")
    probe = read_json(args.seed_probe)
    seed_candidate = select_probe_candidate(probe, args.selector)
    active_words = (
        parse_active_words(args.active_words)
        if args.active_words
        else [int(word) for word in probe.get("active_words", [])]
    )
    modes = [mode.strip() for mode in args.modes.split(",") if mode.strip()]
    score_kwargs = probe.get("score_kwargs") or {
        "atlas_alpha": 4.0,
        "atlas_beta": 1.0,
        "atlas_gamma": 8.0,
        "atlas_delta": 0.05,
    }
    seed_M1 = from_hex_words(seed_candidate["M1"])
    seed_M2 = from_hex_words(seed_candidate["M2"])
    rng = random.Random(args.seed)
    t0 = time.time()
    restarts = [
        run_restart(
            seed_M1,
            seed_M2,
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
    args_payload = vars(args).copy()
    args_payload["seed_probe"] = repo_path(args.seed_probe)
    args_payload["out_json"] = repo_path(args.out_json)
    args_payload["out_md"] = repo_path(args.out_md) if args.out_md else None
    payload = {
        "report_id": args.report_id,
        "seed_probe": repo_path(args.seed_probe),
        "selector": args.selector,
        "active_words": active_words,
        "modes": modes,
        "args": args_payload,
        "score_kwargs": score_kwargs,
        "seed_candidate": seed_candidate,
        "restarts": restarts,
        "wall_seconds": round(time.time() - t0, 6),
    }
    payload["verdict"], payload["decision"] = verdict(payload)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    out_md = args.out_md or args.out_json.with_suffix(".md")
    write_md(out_md, payload)
    best = min(restarts, key=lambda row: row["best_score"]["score"])
    print(json.dumps({
        "verdict": payload["verdict"],
        "seed": {
            "score": seed_candidate["score"],
            "rec": seed_candidate["rec"],
        },
        "best": best["best_score"],
        "wall_seconds": payload["wall_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
