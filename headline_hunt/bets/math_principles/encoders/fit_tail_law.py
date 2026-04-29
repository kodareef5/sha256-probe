#!/usr/bin/env python3
"""
fit_tail_law.py - REM-style and heavy-tail diagnostics for manifest scores.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from statistics import mean, pstdev
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


def quantile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    vals = sorted(values)
    pos = (len(vals) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return vals[lo]
    frac = pos - lo
    return vals[lo] * (1 - frac) + vals[hi] * frac


def normal_cdf(x: float, mu: float, sigma: float) -> float:
    if sigma <= 0:
        return 1.0 if x >= mu else 0.0
    return 0.5 * (1.0 + math.erf((x - mu) / (sigma * math.sqrt(2))))


def score_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [float(row["score"]) for row in rows if row.get("score") is not None]
    if not scores:
        return {"n": 0}
    mu = mean(scores)
    sigma = pstdev(scores) if len(scores) > 1 else 0.0
    n = len(scores)
    expected_min = mu - sigma * math.sqrt(2.0 * math.log(n)) if n > 1 else scores[0]
    thresholds = [90, 92, 95]
    threshold_rows = {}
    for threshold in thresholds:
        observed = sum(1 for score in scores if score <= threshold)
        expected = n * normal_cdf(threshold, mu, sigma)
        threshold_rows[str(threshold)] = {
            "observed": observed,
            "gaussian_expected": round(expected, 6),
            "observed_over_expected": round(observed / expected, 6) if expected > 0 else None,
        }
    return {
        "n": n,
        "min": min(scores),
        "max": max(scores),
        "mean": round(mu, 6),
        "stdev": round(sigma, 6),
        "q01": quantile(scores, 0.01),
        "q05": quantile(scores, 0.05),
        "q10": quantile(scores, 0.10),
        "median": quantile(scores, 0.50),
        "expected_min_rem_gaussian": round(expected_min, 6),
        "min_minus_expected": round(min(scores) - expected_min, 6),
        "thresholds": threshold_rows,
    }


def contains_pattern(rows: list[dict[str, Any]], threshold: int) -> dict[str, Any]:
    low = [
        row for row in rows
        if row.get("score") is not None and row["score"] <= threshold
    ]
    if not low:
        return {"threshold": threshold, "low_count": 0}
    contains = sum(1 for row in low if row.get("contains_1_3"))
    masks = Counter(row.get("active_mask") for row in low)
    return {
        "threshold": threshold,
        "low_count": len(low),
        "contains_1_3_count": contains,
        "contains_1_3_fraction": round(contains / len(low), 6),
        "distinct_masks": len(masks),
        "top_masks": masks.most_common(8),
    }


def verdict(active_stats: dict[str, Any], pattern: dict[str, Any]) -> str:
    low90 = active_stats.get("thresholds", {}).get("90", {})
    ratio = low90.get("observed_over_expected")
    if ratio is not None and ratio >= 2.0:
        return "clustered_or_heavy_tail_evidence"
    if pattern.get("contains_1_3_fraction", 0) >= 0.6 and pattern.get("low_count", 0) >= 3:
        return "structured_seed_basin_evidence"
    return "rem_like_or_inconclusive"


def write_md(path: Path, payload: dict[str, Any]) -> None:
    active = payload["active_subset_scores"]
    local = payload["local_search_scores"]
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: TAIL_LAW_TRIAGE",
        "---",
        "",
        f"# {payload['report_id']}: REM / tail-law triage",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        "",
        "This is a score-tail diagnostic over the current principles manifest, not a proof of the final search distribution.",
        "",
        "## Active-subset scan scores",
        "",
        f"- n={active.get('n')} min={active.get('min')} mean={active.get('mean')} stdev={active.get('stdev')}",
        f"- Gaussian REM expected min: {active.get('expected_min_rem_gaussian')} (observed-minus-expected {active.get('min_minus_expected')})",
        f"- <=90 observed/expected: {active.get('thresholds', {}).get('90')}",
        "",
        "## Local-search scores",
        "",
        f"- n={local.get('n')} min={local.get('min')} mean={local.get('mean')} stdev={local.get('stdev')}",
        f"- <=90 observed/expected: {local.get('thresholds', {}).get('90')}",
        "",
        "## Structure check",
        "",
        f"- Low-score pattern: {payload['low_score_pattern']}",
        "",
        "## Decision",
        "",
        "Do not resume blind chunk scanning as the primary activity. Use the low-score masks as structured basins for influence/submodular and multi-seed tests.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("manifest", type=Path, nargs="?", default=DEFAULT_MANIFEST)
    ap.add_argument("--report-id", default="F340")
    ap.add_argument("--out-json", type=Path, default=REPO / "headline_hunt/bets/math_principles/results/20260429_F340_tail_law.json")
    ap.add_argument("--out-md", type=Path, default=REPO / "headline_hunt/bets/math_principles/results/20260429_F340_tail_law.md")
    args = ap.parse_args()

    rows = read_jsonl(args.manifest)
    active_rows = [row for row in rows if row.get("kind") == "block2_active_subset"]
    local_rows = [row for row in rows if row.get("kind") == "block2_local_search"]
    basin_rows = [row for row in rows if row.get("kind") == "block2_basin_catalog"]
    payload = {
        "manifest": repo_path(args.manifest),
        "report_id": args.report_id,
        "active_subset_scores": score_stats(active_rows),
        "local_search_scores": score_stats(local_rows),
        "basin_catalog_scores": score_stats(basin_rows),
        "low_score_pattern": contains_pattern(active_rows + basin_rows, threshold=90),
    }
    payload["verdict"] = verdict(payload["active_subset_scores"], payload["low_score_pattern"])

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    write_md(args.out_md, payload)
    print(json.dumps({
        "verdict": payload["verdict"],
        "active_n": payload["active_subset_scores"].get("n"),
        "active_min": payload["active_subset_scores"].get("min"),
        "local_min": payload["local_search_scores"].get("min"),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
