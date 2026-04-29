#!/usr/bin/env python3
"""
plan_radius1_basin_walk.py - Emit radius-one basin-walk masks from F345.

For each score <= 90 active-word mask, generate all one-word swaps over the
0..15 message-word pool. Known <=95 neighbors are bridge controls; unobserved
neighbors are the next bounded basin-walk queue.
"""

from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[4]
DEFAULT_MANIFEST = REPO / "headline_hunt/bets/math_principles/data/20260429_principles_manifest.jsonl"
DEFAULT_PRIORS = REPO / "headline_hunt/bets/math_principles/results/20260429_F341_influence_priors.json"
DEFAULT_OUT_JSON = REPO / "headline_hunt/bets/math_principles/results/20260429_F346_radius1_basin_walk_plan.json"
DEFAULT_OUT_MD = REPO / "headline_hunt/bets/math_principles/results/20260429_F346_radius1_basin_walk_plan.md"
DEFAULT_MASK_LIST = REPO / "headline_hunt/bets/math_principles/data/20260429_F346_radius1_basin_walk_masks.txt"


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def parse_words(spec: str) -> list[int]:
    if spec == "all":
        return list(range(16))
    words = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = [int(x) for x in part.split("-", 1)]
            words.extend(range(lo, hi + 1))
        else:
            words.append(int(part))
    out = sorted(set(words))
    if not out or any(word < 0 or word > 15 for word in out):
        raise ValueError("word specs must name message words in [0,15]")
    return out


def mask_words(mask: str) -> tuple[int, ...]:
    return tuple(int(part) for part in mask.split(",") if part != "")


def mask_key(words: tuple[int, ...] | list[int] | set[int]) -> str:
    return ",".join(str(word) for word in sorted(words))


def load_pair_weights(priors: dict[str, Any]) -> dict[tuple[int, int], float]:
    out = {}
    for row in priors.get("pair_priors", []):
        pair = tuple(sorted(int(x) for x in row["feature"]))
        if len(pair) == 2:
            out[pair] = max(0.0, float(row["lift"]) - 1.0)
    return out


def pair_score(words: tuple[int, ...], weights: dict[tuple[int, int], float]) -> float:
    return sum(weights.get(pair, 0.0) for pair in itertools.combinations(words, 2))


def observed_masks(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("score") is None or row.get("active_mask") is None:
            continue
        if row.get("kind") not in {"block2_active_subset", "block2_basin_catalog", "block2_local_search"}:
            continue
        grouped[row["active_mask"]].append(row)

    out = {}
    for mask, members in grouped.items():
        best = min(members, key=lambda row: int(row["score"]))
        out[mask] = {
            "active_mask": mask,
            "active_words": list(mask_words(mask)),
            "best_score": int(best["score"]),
            "support": len(members),
            "source_id": best.get("source_id"),
            "kind": best.get("kind"),
            "artifact_path": best.get("artifact_path"),
        }
    return out


def radius1(seed: tuple[int, ...], pool: list[int]) -> list[tuple[int, ...]]:
    seed_set = set(seed)
    out = []
    for remove in seed:
        for add in pool:
            if add in seed_set:
                continue
            trial = set(seed_set)
            trial.remove(remove)
            trial.add(add)
            out.append(tuple(sorted(trial)))
    return sorted(set(out))


def build_candidates(
    observed: dict[str, dict[str, Any]],
    pair_weights: dict[tuple[int, int], float],
    pool: list[int],
    low_threshold: int,
    bridge_threshold: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    seeds = [
        row for row in observed.values()
        if row["best_score"] <= low_threshold and len(row["active_words"]) == 5
    ]
    seeds.sort(key=lambda row: (row["best_score"], row["active_mask"]))
    parents: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for seed in seeds:
        for neighbor in radius1(tuple(seed["active_words"]), pool):
            parents[mask_key(neighbor)].append(seed)

    candidates = []
    for mask, seed_rows in parents.items():
        if any(seed["active_mask"] == mask for seed in seed_rows):
            continue
        words = mask_words(mask)
        exact = observed.get(mask)
        parent_scores = [seed["best_score"] for seed in seed_rows]
        label = "unseen_radius1"
        if exact is not None and exact["best_score"] <= bridge_threshold:
            label = "known_bridge_control"
        elif exact is not None:
            label = "known_nonbridge_neighbor"
        priority = (
            (bridge_threshold - min(parent_scores) + 1)
            + 2 * len(seed_rows)
            + 0.25 * pair_score(words, pair_weights)
        )
        if exact is not None and exact["best_score"] <= bridge_threshold:
            priority += bridge_threshold - exact["best_score"] + 1
        candidates.append({
            "active_mask": mask,
            "active_words": list(words),
            "label": label,
            "parent_count": len(seed_rows),
            "parents": [
                {
                    "active_mask": seed["active_mask"],
                    "best_score": seed["best_score"],
                    "source_id": seed.get("source_id"),
                }
                for seed in sorted(seed_rows, key=lambda row: (row["best_score"], row["active_mask"]))
            ],
            "best_parent_score": min(parent_scores),
            "exact_observed": exact,
            "pair_prior_diagnostic": round(pair_score(words, pair_weights), 6),
            "priority": round(priority, 6),
        })
    candidates.sort(key=lambda row: (
        row["label"] != "known_bridge_control",
        row["label"] != "unseen_radius1",
        -row["priority"],
        (row["exact_observed"] or {}).get("best_score", 999),
        row["active_mask"],
    ))
    return seeds, candidates


def select_queue(
    candidates: list[dict[str, Any]],
    bridge_controls: int,
    unseen_count: int,
) -> list[dict[str, Any]]:
    queue = []
    seen = set()

    def add(row: dict[str, Any]) -> None:
        if row["active_mask"] in seen:
            return
        seen.add(row["active_mask"])
        queue.append(row)

    for row in [c for c in candidates if c["label"] == "known_bridge_control"][:bridge_controls]:
        add(row)
    for row in [c for c in candidates if c["label"] == "unseen_radius1"][:unseen_count]:
        add(row)
    return queue


def write_mask_list(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# F346 radius-one basin-walk masks.",
        "# Known bridge controls first, then unseen radius-one neighbors.",
    ]
    for row in rows:
        exact = row["exact_observed"]
        exact_label = "unseen" if exact is None else f"known_score={exact['best_score']}"
        lines.append(
            f"{row['active_mask']}  # {row['label']} parent_best={row['best_parent_score']} "
            f"priority={row['priority']} {exact_label}"
        )
    path.write_text("\n".join(lines) + "\n")


def write_md(path: Path, payload: dict[str, Any]) -> None:
    counts = payload["candidate_counts"]
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: RADIUS1_BASIN_WALK_PLAN",
        "---",
        "",
        "# F346: radius-one basin-walk plan",
        "",
        "## Summary",
        "",
        f"Seeds: {len(payload['low_seeds'])}; candidates: {sum(counts.values())}.",
        f"Candidate counts: {counts}.",
        f"Mask list: `{payload['mask_list']}`.",
        "",
        "## Queue",
        "",
        "| Rank | Mask | Label | Parent best | Parents | Known | Pair diag | Priority |",
        "|---:|---|---|---:|---:|---|---:|---:|",
    ]
    for idx, row in enumerate(payload["queue"], 1):
        exact = row["exact_observed"]
        known = "-" if exact is None else str(exact["best_score"])
        lines.append(
            f"| {idx} | `{row['active_mask']}` | `{row['label']}` | {row['best_parent_score']} | "
            f"{row['parent_count']} | {known} | {row['pair_prior_diagnostic']} | {row['priority']} |"
        )
    lines.extend([
        "",
        "## Top Unseen",
        "",
        "| Rank | Mask | Parent best | Parents | Pair diag | Priority |",
        "|---:|---|---:|---:|---:|---:|",
    ])
    for idx, row in enumerate(payload["top_unseen"][:16], 1):
        lines.append(
            f"| {idx} | `{row['active_mask']}` | {row['best_parent_score']} | "
            f"{row['parent_count']} | {row['pair_prior_diagnostic']} | {row['priority']} |"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        "This is the next bounded basin-walk queue. If controls reproduce <=95 and unseen neighbors improve, continue walking; if controls miss again, spend budget on reproducing parent basins before expansion.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--priors", type=Path, default=DEFAULT_PRIORS)
    ap.add_argument("--pool", default="0-15")
    ap.add_argument("--low-threshold", type=int, default=90)
    ap.add_argument("--bridge-threshold", type=int, default=95)
    ap.add_argument("--bridge-controls", type=int, default=12)
    ap.add_argument("--unseen-count", type=int, default=20)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    ap.add_argument("--mask-list", type=Path, default=DEFAULT_MASK_LIST)
    args = ap.parse_args()

    rows = read_jsonl(args.manifest)
    priors = read_json(args.priors)
    pool = parse_words(args.pool)
    observed = observed_masks(rows)
    pair_weights = load_pair_weights(priors)
    seeds, candidates = build_candidates(
        observed,
        pair_weights,
        pool,
        args.low_threshold,
        args.bridge_threshold,
    )
    queue = select_queue(candidates, args.bridge_controls, args.unseen_count)
    counts = Counter(row["label"] for row in candidates)
    top_unseen = [row for row in candidates if row["label"] == "unseen_radius1"]

    payload = {
        "manifest": repo_path(args.manifest),
        "priors": repo_path(args.priors),
        "pool": ",".join(str(word) for word in pool),
        "low_threshold": args.low_threshold,
        "bridge_threshold": args.bridge_threshold,
        "low_seeds": seeds,
        "candidate_counts": dict(sorted(counts.items())),
        "queue": queue,
        "top_unseen": top_unseen[:64],
        "mask_list": repo_path(args.mask_list),
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    write_mask_list(args.mask_list, queue)
    write_md(args.out_md, payload)
    print(json.dumps({
        "candidate_counts": payload["candidate_counts"],
        "mask_list": payload["mask_list"],
        "queue_count": len(queue),
        "seed_count": len(seeds),
        "top_unseen": top_unseen[0] if top_unseen else None,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
