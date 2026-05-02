#!/usr/bin/env python3
"""Extract absorber M2/profile seeds for two-block follow-up operators."""

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def parse_int_set(raw: str) -> set[int] | None:
    if not raw:
        return None
    return {int(part) for part in raw.split(",") if part.strip()}


def parse_words(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def choose_observations(
    observations: list[dict[str, Any]],
    ranks: set[int] | None,
    rounds: set[int] | None,
    per_rank_round: bool,
    limit: int,
) -> list[dict[str, Any]]:
    filtered = []
    for obs in observations:
        if ranks is not None and int(obs["rank"]) not in ranks:
            continue
        if rounds is not None and int(obs["rounds"]) not in rounds:
            continue
        filtered.append(obs)

    filtered.sort(key=lambda obs: (
        -int(obs["rounds"]),
        int(obs["best_hw"]),
        -int(obs["cleared_total"]),
        int(obs["new_total"]),
        int(obs["rank"]),
    ))

    selected = []
    seen = set()
    for obs in filtered:
        key = (obs["rank"], obs["rounds"]) if per_rank_round else obs["rank"]
        if key in seen:
            continue
        seen.add(key)
        selected.append(obs)
        if limit and len(selected) >= limit:
            break
    return selected


def seed_from_observation(obs: dict[str, Any]) -> dict[str, Any]:
    return {
        "rank": obs["rank"],
        "candidate": obs["candidate"],
        "rounds": obs["rounds"],
        "block1_hw": obs["block1_hw"],
        "bridge_score": obs["bridge_score"],
        "block1_W": obs["W"],
        "absorber_start_hw": obs["start_hw"],
        "absorber_best_hw": obs["best_hw"],
        "absorber_improvement": obs["improvement"],
        "absorber_m2": parse_words(obs["best_m2"]),
        "absorber_state_diff": obs["best_state_diff"],
        "input_lane_hw": obs["input_lane_hw"],
        "absorber_lane_hw": obs["best_lane_hw"],
        "lane_delta": obs["lane_delta"],
        "cleared_lane_hw": obs["cleared_lane_hw"],
        "new_lane_hw": obs["new_lane_hw"],
        "overlap_lane_hw": obs["overlap_lane_hw"],
        "cleared_total": obs["cleared_total"],
        "new_total": obs["new_total"],
        "overlap_total": obs["overlap_total"],
        "cg_best_hw": obs["cg_best_hw"],
        "cg_new_hw": obs["cg_new_hw"],
        "cg_cleared_hw": obs["cg_cleared_hw"],
        "source_csv": obs["csv"],
    }


def write_md(path: Path, seeds: list[dict[str, Any]]) -> None:
    lines = [
        "# Absorber M2 Seeds",
        "",
        "| Rank | Rounds | Block-1 HW | Absorber HW | Cleared | New | c/g HW | W57..W60 | M2[0..15] |",
        "|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for seed in seeds:
        words = ",".join(seed["block1_W"])
        m2 = ",".join(seed["absorber_m2"])
        lines.append(
            f"| {seed['rank']} | {seed['rounds']} | {seed['block1_hw']} | "
            f"{seed['absorber_best_hw']} | {seed['cleared_total']} | "
            f"{seed['new_total']} | {seed['cg_best_hw']} | `{words}` | `{m2}` |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--ranks", default="")
    ap.add_argument("--rounds", default="")
    ap.add_argument("--per-rank-round", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out-jsonl", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    profile = load_json(Path(args.profile))
    ranks = parse_int_set(args.ranks)
    rounds = parse_int_set(args.rounds)
    selected = choose_observations(profile["observations"], ranks, rounds, args.per_rank_round, args.limit)
    seeds = [seed_from_observation(obs) for obs in selected]

    out_jsonl = Path(args.out_jsonl)
    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with out_jsonl.open("w", encoding="utf-8") as fh:
        for seed in seeds:
            fh.write(json.dumps(seed, sort_keys=True) + "\n")
    write_md(Path(args.out_md), seeds)
    print(f"wrote {out_jsonl}: {len(seeds)} seeds")


if __name__ == "__main__":
    main()
