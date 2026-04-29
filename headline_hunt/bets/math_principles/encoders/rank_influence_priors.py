#!/usr/bin/env python3
"""
rank_influence_priors.py - Empirical active-word/pair priors from manifest.
"""

from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[4]
DEFAULT_MANIFEST = REPO / "headline_hunt/bets/math_principles/data/20260429_principles_manifest.jsonl"


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


def active_words(row: dict[str, Any]) -> list[int]:
    return [int(word) for word in row.get("active_words", [])]


def count_features(rows: list[dict[str, Any]]) -> tuple[Counter[int], Counter[tuple[int, int]]]:
    word_counts: Counter[int] = Counter()
    pair_counts: Counter[tuple[int, int]] = Counter()
    for row in rows:
        words = sorted(set(active_words(row)))
        word_counts.update(words)
        pair_counts.update(itertools.combinations(words, 2))
    return word_counts, pair_counts


def rank_counts(
    positive_counts: Counter[Any],
    background_counts: Counter[Any],
    n_positive: int,
    n_background: int,
    universe: list[Any],
) -> list[dict[str, Any]]:
    ranked = []
    for key in universe:
        pos = positive_counts[key]
        bg = background_counts[key]
        pos_freq = (pos + 0.5) / (n_positive + 1.0) if n_positive else 0.0
        bg_freq = (bg + 0.5) / (n_background + 1.0) if n_background else 0.0
        ranked.append({
            "feature": list(key) if isinstance(key, tuple) else key,
            "positive_count": pos,
            "background_count": bg,
            "positive_frequency": round(pos_freq, 6),
            "background_frequency": round(bg_freq, 6),
            "lift": round(pos_freq / bg_freq, 6) if bg_freq else None,
        })
    ranked.sort(key=lambda row: (row["lift"] or 0.0, row["positive_count"]), reverse=True)
    return ranked


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: INFLUENCE_PRIORS",
        "---",
        "",
        "# F341: empirical influence priors",
        "",
        "## Summary",
        "",
        f"Positive threshold: score <= {payload['positive_score_threshold']}.",
        f"Background records: {payload['background_count']}; positive records: {payload['positive_count']}.",
        "",
        "## Top active words",
        "",
        "| Rank | Word | Positive | Background | Lift |",
        "|---:|---:|---:|---:|---:|",
    ]
    for idx, row in enumerate(payload["word_priors"][:12], 1):
        lines.append(
            f"| {idx} | {row['feature']} | {row['positive_count']} | "
            f"{row['background_count']} | {row['lift']} |"
        )
    lines.extend([
        "",
        "## Top active-word pairs",
        "",
        "| Rank | Pair | Positive | Background | Lift |",
        "|---:|---|---:|---:|---:|",
    ])
    for idx, row in enumerate(payload["pair_priors"][:16], 1):
        pair = ",".join(str(x) for x in row["feature"])
        lines.append(
            f"| {idx} | `{pair}` | {row['positive_count']} | "
            f"{row['background_count']} | {row['lift']} |"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        f"`{{1,3}}` stats: {payload['pair_1_3']}.",
        "Use `{1,3}` as a candidate sampler axis, but preserve F248 as the explicit outlier control.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("manifest", type=Path, nargs="?", default=DEFAULT_MANIFEST)
    ap.add_argument("--positive-score", type=int, default=90)
    ap.add_argument("--out-json", type=Path, default=REPO / "headline_hunt/bets/math_principles/results/20260429_F341_influence_priors.json")
    ap.add_argument("--out-md", type=Path, default=REPO / "headline_hunt/bets/math_principles/results/20260429_F341_influence_priors.md")
    args = ap.parse_args()

    rows = read_jsonl(args.manifest)
    background = [
        row for row in rows
        if row.get("kind") == "block2_active_subset" and row.get("score") is not None
    ]
    positives = [
        row for row in rows
        if row.get("kind") in {"block2_active_subset", "block2_basin_catalog"}
        and row.get("score") is not None
        and row["score"] <= args.positive_score
    ]
    bg_word, bg_pair = count_features(background)
    pos_word, pos_pair = count_features(positives)
    words = list(range(16))
    pairs = list(itertools.combinations(range(16), 2))
    word_priors = rank_counts(pos_word, bg_word, len(positives), len(background), words)
    pair_priors = rank_counts(pos_pair, bg_pair, len(positives), len(background), pairs)
    pair_1_3 = next(row for row in pair_priors if row["feature"] == [1, 3])
    payload = {
        "manifest": repo_path(args.manifest),
        "positive_score_threshold": args.positive_score,
        "background_count": len(background),
        "positive_count": len(positives),
        "word_priors": word_priors,
        "pair_priors": pair_priors,
        "pair_1_3": pair_1_3,
        "positive_masks": [
            {
                "source_id": row.get("source_id"),
                "active_mask": row.get("active_mask"),
                "score": row.get("score"),
                "contains_1_3": row.get("contains_1_3"),
            }
            for row in positives
        ],
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    write_md(args.out_md, payload)
    print(json.dumps({
        "positive_count": len(positives),
        "top_word": word_priors[0],
        "top_pair": pair_priors[0],
        "pair_1_3": pair_1_3,
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
