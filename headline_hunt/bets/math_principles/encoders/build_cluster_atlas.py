#!/usr/bin/env python3
"""
build_cluster_atlas.py - Track 2 active-mask basin/cluster atlas.

This is a bounded cluster proxy over the manifest. Nodes are active-word masks;
edges connect masks one word-swap apart. It answers whether good masks are
isolated or connected through near-good bridge masks before we spend effort on
deeper trace/avalanche extraction.
"""

from __future__ import annotations

import argparse
import itertools
import json
from collections import Counter, defaultdict, deque
from pathlib import Path
from statistics import mean
from typing import Any


REPO = Path(__file__).resolve().parents[4]
DEFAULT_MANIFEST = REPO / "headline_hunt/bets/math_principles/data/20260429_principles_manifest.jsonl"
DEFAULT_OUT_JSON = REPO / "headline_hunt/bets/math_principles/results/20260429_F345_cluster_atlas.json"
DEFAULT_OUT_MD = REPO / "headline_hunt/bets/math_principles/results/20260429_F345_cluster_atlas.md"


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


def mask_words(mask: str) -> tuple[int, ...]:
    return tuple(int(part) for part in mask.split(",") if part != "")


def mask_key(words: tuple[int, ...] | list[int]) -> str:
    return ",".join(str(word) for word in sorted(words))


def word_distance(a: str, b: str) -> int:
    return len(set(mask_words(a)) ^ set(mask_words(b)))


def grouped_masks(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("score") is None or row.get("active_mask") is None:
            continue
        if row.get("kind") not in {"block2_active_subset", "block2_basin_catalog", "block2_local_search"}:
            continue
        grouped[row["active_mask"]].append(row)

    out = {}
    for mask, members in grouped.items():
        scores = [int(row["score"]) for row in members]
        kinds = Counter(row["kind"] for row in members)
        sources = sorted({row.get("source_id") for row in members if row.get("source_id")})
        out[mask] = {
            "active_mask": mask,
            "active_words": list(mask_words(mask)),
            "size": len(mask_words(mask)),
            "best_score": min(scores),
            "mean_score": round(mean(scores), 6),
            "support": len(members),
            "kinds": dict(sorted(kinds.items())),
            "sources": sources[:12],
        }
    return out


def build_edges(nodes: list[str], max_distance: int) -> dict[str, list[str]]:
    edges: dict[str, list[str]] = {node: [] for node in nodes}
    by_size: dict[int, list[str]] = defaultdict(list)
    for node in nodes:
        by_size[len(mask_words(node))].append(node)
    for same_size in by_size.values():
        for a, b in itertools.combinations(sorted(same_size), 2):
            if word_distance(a, b) <= max_distance:
                edges[a].append(b)
                edges[b].append(a)
    for node in edges:
        edges[node].sort()
    return edges


def components(nodes: list[str], edges: dict[str, list[str]]) -> list[list[str]]:
    seen = set()
    comps = []
    for node in sorted(nodes):
        if node in seen:
            continue
        q = deque([node])
        seen.add(node)
        comp = []
        while q:
            current = q.popleft()
            comp.append(current)
            for nxt in edges[current]:
                if nxt not in seen:
                    seen.add(nxt)
                    q.append(nxt)
        comps.append(sorted(comp))
    comps.sort(key=lambda comp: (-len(comp), comp[0]))
    return comps


def summarize_component(comp: list[str], masks: dict[str, dict[str, Any]]) -> dict[str, Any]:
    scores = [masks[mask]["best_score"] for mask in comp]
    best_score = min(scores)
    best_masks = [mask for mask in comp if masks[mask]["best_score"] == best_score]
    words = Counter()
    pairs = Counter()
    for mask in comp:
        active = masks[mask]["active_words"]
        words.update(active)
        pairs.update(itertools.combinations(active, 2))
    return {
        "size": len(comp),
        "best_score": best_score,
        "best_masks": best_masks[:8],
        "score_histogram": dict(sorted(Counter(scores).items())),
        "top_words": words.most_common(8),
        "top_pairs": [(",".join(str(x) for x in pair), count) for pair, count in pairs.most_common(8)],
        "masks": comp[:32],
    }


def threshold_atlas(
    masks: dict[str, dict[str, Any]],
    threshold: int,
    max_distance: int,
) -> dict[str, Any]:
    nodes = [mask for mask, row in masks.items() if row["best_score"] <= threshold]
    edges = build_edges(nodes, max_distance)
    comps = components(nodes, edges)
    return {
        "threshold": threshold,
        "node_count": len(nodes),
        "edge_count": sum(len(v) for v in edges.values()) // 2,
        "component_count": len(comps),
        "largest_component": len(comps[0]) if comps else 0,
        "components": [summarize_component(comp, masks) for comp in comps[:16]],
    }


def radius_stats(
    low_masks: list[str],
    all_masks: dict[str, dict[str, Any]],
    max_distance: int,
    score_thresholds: list[int],
) -> list[dict[str, Any]]:
    out = []
    all_keys = list(all_masks)
    for mask in sorted(low_masks, key=lambda key: (all_masks[key]["best_score"], key)):
        neighbors = [
            other for other in all_keys
            if other != mask
            and len(mask_words(other)) == len(mask_words(mask))
            and word_distance(mask, other) <= max_distance
        ]
        counts = {
            f"score_le_{threshold}": sum(1 for other in neighbors if all_masks[other]["best_score"] <= threshold)
            for threshold in score_thresholds
        }
        best_neighbor = min((all_masks[other]["best_score"] for other in neighbors), default=None)
        out.append({
            "active_mask": mask,
            "best_score": all_masks[mask]["best_score"],
            "neighbor_count": len(neighbors),
            "best_neighbor_score": best_neighbor,
            **counts,
        })
    return out


def verdict(low_atlas: dict[str, Any], bridge_atlas: dict[str, Any], radius: list[dict[str, Any]]) -> str:
    low_clustered = low_atlas["edge_count"] > 0 or low_atlas["largest_component"] >= 2
    bridge_clustered = bridge_atlas["largest_component"] >= max(3, low_atlas["largest_component"])
    has_near_neighbors = any(row.get("score_le_95", 0) >= 3 for row in radius)
    if low_clustered:
        return "low_scores_have_direct_clusters"
    if bridge_clustered and has_near_neighbors:
        return "low_scores_connect_through_near_score_bridges"
    return "low_scores_mostly_isolated"


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: CLUSTER_ATLAS",
        "---",
        "",
        f"# {payload['report_id']}: active-mask cluster atlas",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        f"Observed masks: {payload['observed_mask_count']}.",
        f"Low threshold: {payload['low_threshold']}; bridge threshold: {payload['bridge_threshold']}; edge distance: {payload['edge_distance']}.",
        "",
        "## Threshold Graphs",
        "",
        "| Threshold | Nodes | Edges | Components | Largest |",
        "|---:|---:|---:|---:|---:|",
    ]
    for atlas in payload["thresholds"]:
        lines.append(
            f"| {atlas['threshold']} | {atlas['node_count']} | {atlas['edge_count']} | "
            f"{atlas['component_count']} | {atlas['largest_component']} |"
        )
    lines.extend([
        "",
        "## Low-Score Radius Stats",
        "",
        "| Mask | Score | Neighbors | Best neighbor | <=90 | <=92 | <=95 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for row in payload["radius_stats"]:
        best_neighbor = "-" if row["best_neighbor_score"] is None else str(row["best_neighbor_score"])
        lines.append(
            f"| `{row['active_mask']}` | {row['best_score']} | {row['neighbor_count']} | "
            f"{best_neighbor} | {row['score_le_90']} | {row['score_le_92']} | {row['score_le_95']} |"
        )
    lines.extend([
        "",
        "## Bridge Components",
        "",
    ])
    bridge = payload["thresholds"][-1]
    for idx, comp in enumerate(bridge["components"][:8], 1):
        lines.append(
            f"- Component {idx}: size={comp['size']} best={comp['best_score']} "
            f"best_masks={comp['best_masks']} top_pairs={comp['top_pairs'][:4]}"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        "Treat the best masks as basin seeds with near-score bridge neighborhoods, not as a single connected critical component. The next operator should walk radius-one neighborhoods around the known controls and track whether <=95 bridges reproduce before expanding.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--report-id", default="F345")
    ap.add_argument("--low-threshold", type=int, default=90)
    ap.add_argument("--bridge-threshold", type=int, default=95)
    ap.add_argument("--edge-distance", type=int, default=2)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    args = ap.parse_args()

    rows = read_jsonl(args.manifest)
    masks = grouped_masks(rows)
    thresholds = [
        threshold_atlas(masks, args.low_threshold, args.edge_distance),
        threshold_atlas(masks, 92, args.edge_distance),
        threshold_atlas(masks, args.bridge_threshold, args.edge_distance),
    ]
    low_masks = [
        mask for mask, row in masks.items()
        if row["best_score"] <= args.low_threshold
    ]
    radius = radius_stats(low_masks, masks, args.edge_distance, [90, 92, 95])
    payload = {
        "manifest": repo_path(args.manifest),
        "report_id": args.report_id,
        "observed_mask_count": len(masks),
        "low_threshold": args.low_threshold,
        "bridge_threshold": args.bridge_threshold,
        "edge_distance": args.edge_distance,
        "thresholds": thresholds,
        "radius_stats": radius,
    }
    payload["verdict"] = verdict(thresholds[0], thresholds[-1], radius)

    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    write_md(args.out_md, payload)
    print(json.dumps({
        "verdict": payload["verdict"],
        "observed_masks": len(masks),
        "low": {
            "nodes": thresholds[0]["node_count"],
            "edges": thresholds[0]["edge_count"],
            "largest": thresholds[0]["largest_component"],
        },
        "bridge": {
            "nodes": thresholds[-1]["node_count"],
            "edges": thresholds[-1]["edge_count"],
            "largest": thresholds[-1]["largest_component"],
        },
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
