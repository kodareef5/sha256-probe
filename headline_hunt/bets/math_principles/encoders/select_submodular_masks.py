#!/usr/bin/env python3
"""
select_submodular_masks.py - Deterministic active-word selectors.

This is the first Track 6 implementation. It does not run the absorber search.
It turns the manifest and F341 influence priors into ranked active-word masks
that can be fed to block2_wang/encoders/active_subset_scan.py.
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[4]
DEFAULT_MANIFEST = REPO / "headline_hunt/bets/math_principles/data/20260429_principles_manifest.jsonl"
DEFAULT_PRIORS = REPO / "headline_hunt/bets/math_principles/results/20260429_F341_influence_priors.json"
DEFAULT_OUT_JSON = REPO / "headline_hunt/bets/math_principles/results/20260429_F343_submodular_selectors.json"
DEFAULT_OUT_MD = REPO / "headline_hunt/bets/math_principles/results/20260429_F343_submodular_selectors.md"
DEFAULT_MASK_LIST = REPO / "headline_hunt/bets/math_principles/data/20260429_F343_submodular_masks.txt"


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


def mask_key(words: list[int] | tuple[int, ...]) -> str:
    return ",".join(str(word) for word in sorted(words))


def mask_words(mask: str) -> tuple[int, ...]:
    return tuple(int(part) for part in mask.split(",") if part != "")


def load_prior_weights(priors: dict[str, Any]) -> tuple[dict[int, float], dict[tuple[int, int], float]]:
    word_weights = {
        int(row["feature"]): max(0.0, float(row["lift"]) - 1.0)
        for row in priors.get("word_priors", [])
    }
    pair_weights = {}
    for row in priors.get("pair_priors", []):
        feature = tuple(int(x) for x in row["feature"])
        if len(feature) == 2:
            pair_weights[tuple(sorted(feature))] = max(0.0, float(row["lift"]) - 1.0)
    return word_weights, pair_weights


def observed_scores(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    observed: dict[str, dict[str, Any]] = {}
    for row in rows:
        mask = row.get("active_mask")
        score = row.get("score")
        if mask is None or score is None:
            continue
        current = observed.get(mask)
        candidate = {
            "best_score": score,
            "source_id": row.get("source_id"),
            "kind": row.get("kind"),
            "artifact_path": row.get("artifact_path"),
        }
        if current is None or score < current["best_score"]:
            observed[mask] = candidate
    return observed


def positive_evidence(rows: list[dict[str, Any]], threshold: int) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("kind") not in {"block2_active_subset", "block2_basin_catalog"}:
            continue
        if row.get("score") is None or row["score"] > threshold:
            continue
        grouped[row["active_mask"]].append(row)

    evidence = []
    for mask, members in grouped.items():
        best = min(int(row["score"]) for row in members)
        support = len(members)
        weight = (threshold - best + 1) * (1.0 + math.log1p(support - 1))
        sources = sorted({row.get("source_id") for row in members if row.get("source_id")})
        evidence.append({
            "active_mask": mask,
            "active_words": list(mask_words(mask)),
            "best_score": best,
            "support": support,
            "weight": round(weight, 6),
            "sources": sources,
        })
    evidence.sort(key=lambda row: (-row["weight"], row["best_score"], row["active_mask"]))
    return evidence


def coverage_value(
    selected: set[int],
    evidence: list[dict[str, Any]],
    cap: int,
) -> float:
    total = 0.0
    for item in evidence:
        overlap = len(selected.intersection(item["active_words"]))
        total += float(item["weight"]) * min(overlap, cap) / cap
    return total


def word_prior_value(selected: set[int], word_weights: dict[int, float]) -> float:
    return sum(word_weights.get(word, 0.0) for word in selected)


def objective(
    selected: set[int],
    evidence: list[dict[str, Any]],
    word_weights: dict[int, float],
    cap: int,
    word_scale: float,
) -> float:
    return coverage_value(selected, evidence, cap) + word_scale * word_prior_value(selected, word_weights)


def pair_diagnostic(selected: set[int], pair_weights: dict[tuple[int, int], float]) -> float:
    total = 0.0
    for a, b in itertools.combinations(sorted(selected), 2):
        total += pair_weights.get((a, b), 0.0)
    return total


def nearest_evidence(selected: set[int], evidence: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not evidence:
        return None
    ranked = []
    for item in evidence:
        words = set(item["active_words"])
        overlap = len(selected & words)
        distance = len(selected | words) - overlap
        ranked.append((distance, -overlap, item["best_score"], item["active_mask"], item))
    _, _, _, _, best = sorted(ranked)[0]
    return {
        "active_mask": best["active_mask"],
        "best_score": best["best_score"],
        "support": best["support"],
        "distance": sorted(ranked)[0][0],
    }


def annotate(
    words: tuple[int, ...],
    evidence: list[dict[str, Any]],
    word_weights: dict[int, float],
    pair_weights: dict[tuple[int, int], float],
    observed: dict[str, dict[str, Any]],
    cap: int,
    word_scale: float,
    label: str | None = None,
) -> dict[str, Any]:
    selected = set(words)
    mask = mask_key(words)
    nearest = nearest_evidence(selected, evidence)
    exact = observed.get(mask)
    return {
        "label": label,
        "active_words": list(words),
        "active_mask": mask,
        "objective": round(objective(selected, evidence, word_weights, cap, word_scale), 6),
        "coverage_value": round(coverage_value(selected, evidence, cap), 6),
        "word_prior_value": round(word_prior_value(selected, word_weights), 6),
        "pair_prior_diagnostic": round(pair_diagnostic(selected, pair_weights), 6),
        "contains_1_3": 1 in selected and 3 in selected,
        "exact_observed": exact,
        "nearest_positive": nearest,
    }


def greedy_select(
    pool: list[int],
    size: int,
    seed: tuple[int, ...],
    evidence: list[dict[str, Any]],
    word_weights: dict[int, float],
    cap: int,
    word_scale: float,
) -> tuple[int, ...]:
    selected = set(seed)
    if len(selected) > size:
        raise ValueError(f"seed {seed} is larger than target size {size}")
    while len(selected) < size:
        candidates = [word for word in pool if word not in selected]
        if not candidates:
            break
        current = objective(selected, evidence, word_weights, cap, word_scale)
        ranked = []
        for word in candidates:
            trial = set(selected)
            trial.add(word)
            gain = objective(trial, evidence, word_weights, cap, word_scale) - current
            ranked.append((gain, word_weights.get(word, 0.0), -word, word))
        ranked.sort(reverse=True)
        selected.add(ranked[0][3])
    return tuple(sorted(selected))


def rank_all_subsets(
    pool: list[int],
    size: int,
    evidence: list[dict[str, Any]],
    word_weights: dict[int, float],
    pair_weights: dict[tuple[int, int], float],
    observed: dict[str, dict[str, Any]],
    cap: int,
    word_scale: float,
) -> list[dict[str, Any]]:
    ranked = [
        annotate(combo, evidence, word_weights, pair_weights, observed, cap, word_scale)
        for combo in itertools.combinations(pool, size)
    ]
    ranked.sort(key=lambda row: (
        -row["objective"],
        (row["exact_observed"] or {}).get("best_score", 999),
        -row["pair_prior_diagnostic"],
        row["active_mask"],
    ))
    for idx, row in enumerate(ranked, 1):
        row["objective_rank"] = idx
    return ranked


def with_label(row: dict[str, Any], label: str) -> dict[str, Any]:
    out = dict(row)
    out["label"] = label
    return out


def calibration_summary(
    ranked_all: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    positive_score: int,
    top_window: int,
) -> dict[str, Any]:
    by_mask = {row["active_mask"]: row for row in ranked_all}
    positive_ranks = []
    for item in evidence:
        row = by_mask.get(item["active_mask"])
        if row is None:
            continue
        positive_ranks.append({
            "active_mask": item["active_mask"],
            "best_score": item["best_score"],
            "support": item["support"],
            "objective": row["objective"],
            "objective_rank": row["objective_rank"],
        })
    positive_ranks.sort(key=lambda row: (row["objective_rank"], row["best_score"]))

    top_observed = next((row for row in ranked_all if row["exact_observed"] is not None), None)
    top_unseen = next((row for row in ranked_all if row["exact_observed"] is None), None)
    top_known_good = positive_ranks[0] if positive_ranks else None
    top_observed_score = None
    if top_observed is not None:
        top_observed_score = top_observed["exact_observed"]["best_score"]

    if top_known_good and top_known_good["objective_rank"] <= top_window:
        verdict = "passes_known_good_recall"
    elif top_unseen and top_unseen["objective_rank"] <= top_window and (top_observed_score or 999) > positive_score:
        verdict = "needs_unseen_scan_but_fails_observed_calibration"
    else:
        verdict = "fails_direct_selector_calibration"

    return {
        "top_window": top_window,
        "verdict": verdict,
        "top_observed": top_observed,
        "top_unseen": top_unseen,
        "top_known_good": top_known_good,
        "positive_ranks": positive_ranks,
    }


def select_mask_rows(
    greedy_rows: list[dict[str, Any]],
    ranked_all: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    by_mask = {row["active_mask"]: row for row in ranked_all}
    rows: list[dict[str, Any]] = []
    seen = set()

    def add(row: dict[str, Any] | None, label: str) -> None:
        if row is None or row["active_mask"] in seen or len(rows) >= limit:
            return
        seen.add(row["active_mask"])
        rows.append(with_label(row, label))

    for item in sorted(evidence, key=lambda row: (row["best_score"], -row["support"], row["active_mask"])):
        add(by_mask.get(item["active_mask"]), "known_good_control")

    unseen_added = 0
    for row in ranked_all:
        if row["exact_observed"] is None:
            add(row, f"top_unseen_rank_{row['objective_rank']}")
            unseen_added += 1
            if unseen_added >= max(4, limit // 3):
                break

    for row in greedy_rows:
        add(row, row.get("label") or "greedy_selector")

    for row in ranked_all:
        add(row, f"top_objective_rank_{row['objective_rank']}")

    return rows


def seed_specs(priors: dict[str, Any], top_pairs: int, top_words: int) -> list[tuple[str, tuple[int, ...]]]:
    seeds: list[tuple[str, tuple[int, ...]]] = [("free_greedy", tuple())]
    for row in priors.get("pair_priors", [])[:top_pairs]:
        pair = tuple(sorted(int(x) for x in row["feature"]))
        seeds.append((f"force_pair_{mask_key(pair)}", pair))
    for row in priors.get("word_priors", [])[:top_words]:
        word = int(row["feature"])
        seeds.append((f"force_word_{word}", (word,)))
    return seeds


def write_mask_list(path: Path, masks: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# F343 submodular selector masks.",
        "# Feed with active_subset_scan.py --subset-list this_file",
    ]
    for row in masks:
        exact = row["exact_observed"]
        exact_label = "unseen" if exact is None else f"known_score={exact['best_score']}"
        label = row.get("label") or "ranked"
        lines.append(f"{row['active_mask']}  # {label} objective={row['objective']} {exact_label}")
    path.write_text("\n".join(lines) + "\n")


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: SUBMODULAR_SELECTORS",
        "---",
        "",
        "# F343: submodular active-word selectors",
        "",
        "## Summary",
        "",
        f"Pool: `{payload['pool']}`; size: {payload['size']}; positive threshold: {payload['positive_score_threshold']}.",
        f"Positive masks: {payload['positive_mask_count']}; observed masks: {payload['observed_mask_count']}.",
        f"Mask list: `{payload['mask_list']}`.",
        f"Calibration verdict: `{payload['calibration']['verdict']}`.",
        "",
        "## Calibration",
        "",
    ]
    top_observed = payload["calibration"]["top_observed"]
    top_unseen = payload["calibration"]["top_unseen"]
    top_known_good = payload["calibration"]["top_known_good"]
    if top_observed:
        exact = top_observed["exact_observed"]
        lines.append(
            f"- Top objective mask `{top_observed['active_mask']}` was already observed at score {exact['best_score']}."
        )
    if top_unseen:
        lines.append(
            f"- First unseen mask is rank {top_unseen['objective_rank']}: `{top_unseen['active_mask']}`."
        )
    if top_known_good:
        lines.append(
            f"- First known-good mask is rank {top_known_good['objective_rank']}: `{top_known_good['active_mask']}` score {top_known_good['best_score']}."
        )
    lines.extend([
        "",
        "Known-good objective ranks:",
        "",
        "| Rank | Mask | Best score | Support | Objective |",
        "|---:|---|---:|---:|---:|",
    ])
    for row in payload["calibration"]["positive_ranks"][:12]:
        lines.append(
            f"| {row['objective_rank']} | `{row['active_mask']}` | {row['best_score']} | "
            f"{row['support']} | {row['objective']} |"
        )
    lines.extend([
        "",
        "## Greedy selectors",
        "",
        "| Rank | Label | Mask | Objective | Pair diag | Exact observed | Nearest positive |",
        "|---:|---|---|---:|---:|---|---|",
    ])
    for idx, row in enumerate(payload["greedy_selectors"], 1):
        exact = row["exact_observed"]
        exact_label = "-" if exact is None else f"{exact['best_score']} ({exact['source_id']})"
        nearest = row["nearest_positive"]
        nearest_label = "-" if nearest is None else f"{nearest['active_mask']} d={nearest['distance']} score={nearest['best_score']}"
        lines.append(
            f"| {idx} | `{row['label']}` | `{row['active_mask']}` | {row['objective']} | "
            f"{row['pair_prior_diagnostic']} | {exact_label} | {nearest_label} |"
        )
    lines.extend([
        "",
        "## Top exhaustive masks",
        "",
        "| Rank | Mask | Objective | Pair diag | Exact observed | Nearest positive |",
        "|---:|---|---:|---:|---|---|",
    ])
    for idx, row in enumerate(payload["top_exhaustive"][:20], 1):
        exact = row["exact_observed"]
        exact_label = "-" if exact is None else f"{exact['best_score']} ({exact['source_id']})"
        nearest = row["nearest_positive"]
        nearest_label = "-" if nearest is None else f"{nearest['active_mask']} d={nearest['distance']} score={nearest['best_score']}"
        lines.append(
            f"| {idx} | `{row['active_mask']}` | {row['objective']} | "
            f"{row['pair_prior_diagnostic']} | {exact_label} | {nearest_label} |"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        "Do not trust the raw submodular objective as a direct selector yet. Use the emitted subset list as a calibration scan: known-good controls first, then the highest-ranking unseen masks, then the raw greedy/objective picks.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--priors", type=Path, default=DEFAULT_PRIORS)
    ap.add_argument("--pool", default="0-15")
    ap.add_argument("--size", type=int, default=5)
    ap.add_argument("--positive-score", type=int, default=90)
    ap.add_argument("--coverage-cap", type=int, default=3)
    ap.add_argument("--word-prior-scale", type=float, default=1.0)
    ap.add_argument("--top-pairs", type=int, default=8)
    ap.add_argument("--top-words", type=int, default=6)
    ap.add_argument("--top-exhaustive", type=int, default=40)
    ap.add_argument("--mask-list-limit", type=int, default=24)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    ap.add_argument("--mask-list", type=Path, default=DEFAULT_MASK_LIST)
    args = ap.parse_args()

    pool = parse_words(args.pool)
    if args.size < 1 or args.size > len(pool):
        raise SystemExit("--size must be in [1,len(pool)]")
    if args.coverage_cap < 1:
        raise SystemExit("--coverage-cap must be positive")

    rows = read_jsonl(args.manifest)
    priors = read_json(args.priors)
    word_weights, pair_weights = load_prior_weights(priors)
    observed = observed_scores(rows)
    evidence = positive_evidence(rows, args.positive_score)

    greedy_rows = []
    seen = set()
    for label, seed in seed_specs(priors, args.top_pairs, args.top_words):
        selected = greedy_select(pool, args.size, seed, evidence, word_weights, args.coverage_cap, args.word_prior_scale)
        if selected in seen:
            continue
        seen.add(selected)
        greedy_rows.append(
            annotate(selected, evidence, word_weights, pair_weights, observed, args.coverage_cap, args.word_prior_scale, label)
        )
    greedy_rows.sort(key=lambda row: (-row["objective"], row["active_mask"]))

    ranked_all = rank_all_subsets(
        pool,
        args.size,
        evidence,
        word_weights,
        pair_weights,
        observed,
        args.coverage_cap,
        args.word_prior_scale,
    )
    top_exhaustive = ranked_all[:args.top_exhaustive]
    calibration = calibration_summary(ranked_all, evidence, args.positive_score, args.top_exhaustive)
    mask_rows = select_mask_rows(greedy_rows, ranked_all, evidence, args.mask_list_limit)

    payload = {
        "manifest": repo_path(args.manifest),
        "priors": repo_path(args.priors),
        "pool": ",".join(str(word) for word in pool),
        "size": args.size,
        "positive_score_threshold": args.positive_score,
        "coverage_cap": args.coverage_cap,
        "word_prior_scale": args.word_prior_scale,
        "positive_mask_count": len(evidence),
        "observed_mask_count": len(observed),
        "calibration": calibration,
        "greedy_selectors": greedy_rows,
        "top_exhaustive": top_exhaustive,
        "mask_list": repo_path(args.mask_list),
        "mask_list_rows": mask_rows,
    }

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    write_mask_list(args.mask_list, mask_rows)
    write_md(args.out_md, payload)

    print(json.dumps({
        "positive_masks": len(evidence),
        "observed_masks": len(observed),
        "calibration_verdict": calibration["verdict"],
        "top_greedy": greedy_rows[0] if greedy_rows else None,
        "top_exhaustive": top_exhaustive[0] if top_exhaustive else None,
        "top_unseen": calibration["top_unseen"],
        "mask_list": repo_path(args.mask_list),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
