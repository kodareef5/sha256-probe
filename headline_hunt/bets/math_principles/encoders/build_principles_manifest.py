#!/usr/bin/env python3
"""
build_principles_manifest.py - Normalize existing math-principles evidence.

The manifest is a JSONL table consumed by the REM/tail, influence, and
carry-invariant analyzers. It intentionally ingests a bounded set of concrete
artifacts rather than every result file in the repository.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[4]

BIT19_CANDIDATE = "bit19_m51ca0b34_fill55555555"
BLOCK2_BUNDLE = "headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json"


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def rel(path: Path) -> str:
    return str(path.relative_to(REPO))


def mask_key(active_words: list[int] | None) -> str | None:
    if active_words is None:
        return None
    return ",".join(str(word) for word in active_words)


def contains_1_3(active_words: list[int] | None) -> bool | None:
    if active_words is None:
        return None
    return 1 in active_words and 3 in active_words


def parse_f_id(path: Path) -> str | None:
    match = re.search(r"(F\d+)", path.name)
    return match.group(1) if match else None


def parse_chunk(path: Path) -> int | None:
    match = re.search(r"chunk0*([0-9]+)", path.name)
    return int(match.group(1)) if match else None


def record_base(kind: str, path: Path, source_id: str | None = None) -> dict[str, Any]:
    return {
        "kind": kind,
        "source_id": source_id or parse_f_id(path) or path.stem,
        "artifact_path": rel(path),
    }


def ingest_basin_catalog(path: Path) -> list[dict[str, Any]]:
    data = load_json(path)
    rows: list[dict[str, Any]] = []
    for basin in data.get("basins", []):
        active_words = [int(word) for word in basin.get("active_words", [])]
        rows.append({
            **record_base("block2_basin_catalog", path, basin.get("id")),
            "candidate": data.get("candidate", BIT19_CANDIDATE),
            "bundle": data.get("bundle", BLOCK2_BUNDLE),
            "active_words": active_words,
            "active_mask": mask_key(active_words),
            "contains_1_3": contains_1_3(active_words),
            "score": basin.get("best_score"),
            "chunk": basin.get("chunk"),
            "seed_notes": basin.get("seed_notes"),
            "tags": ["bit19", "narrow_basin"],
        })
    return rows


def ingest_active_subset_scan(path: Path) -> list[dict[str, Any]]:
    data = load_json(path)
    args = data.get("args", {})
    rows: list[dict[str, Any]] = []
    chunk = parse_chunk(path)
    for idx, entry in enumerate(data.get("subsets", [])):
        active_words = [int(word) for word in entry.get("active_words", [])]
        best = entry.get("best", {})
        rows.append({
            **record_base("block2_active_subset", path),
            "candidate": BIT19_CANDIDATE,
            "bundle": data.get("bundle", BLOCK2_BUNDLE),
            "active_words": active_words,
            "active_mask": mask_key(active_words),
            "contains_1_3": contains_1_3(active_words),
            "score": best.get("score"),
            "objective": best.get("objective"),
            "message_diff_hw": best.get("message_diff_hw"),
            "nonzero_message_words": best.get("nonzero_message_words"),
            "nonzero_schedule_words": best.get("nonzero_schedule_words"),
            "seed": entry.get("seed"),
            "restart": best.get("restart"),
            "chunk": chunk,
            "start_index": data.get("start_index") or args.get("start_index"),
            "subset_index": idx,
            "tags": ["bit19", "active_subset_scan", "seed7101"],
        })
    return rows


def local_search_role(path: Path, args: dict[str, Any]) -> str:
    if args.get("init_json"):
        return "init_continuation"
    if "seed" in path.name:
        return "fresh_seed"
    return "local_search"


def ingest_local_search(path: Path) -> list[dict[str, Any]]:
    data = load_json(path)
    args = data.get("args", {})
    active_words = [int(word) for word in data.get("active_words", [])]
    role = local_search_role(path, args)
    rows: list[dict[str, Any]] = []
    for result in data.get("results", []):
        rows.append({
            **record_base("block2_local_search", path),
            "candidate": BIT19_CANDIDATE,
            "bundle": data.get("bundle", BLOCK2_BUNDLE),
            "active_words": active_words,
            "active_mask": mask_key(active_words),
            "contains_1_3": contains_1_3(active_words),
            "score": result.get("score"),
            "objective": result.get("objective"),
            "message_diff_hw": result.get("message_diff_hw"),
            "nonzero_message_words": result.get("nonzero_message_words"),
            "nonzero_schedule_words": result.get("nonzero_schedule_words"),
            "seed": args.get("seed"),
            "restart": result.get("restart"),
            "search_role": role,
            "init_json": args.get("init_json"),
            "tags": ["bit19", role],
        })
    return rows


def mode_from_stability_path(path: Path) -> str:
    if "sr60" in path.name:
        return "sr60"
    if "sr61" in path.name:
        return "sr61"
    return "unknown"


def hard_core_class(row: dict[str, Any], n_inputs: int) -> str:
    if row.get("core_count") == n_inputs:
        return "stable_core"
    if row.get("shell_count") == n_inputs:
        return "stable_shell"
    return "variable"


def ingest_hard_core_stability(path: Path) -> list[dict[str, Any]]:
    data = load_json(path)
    mode = mode_from_stability_path(path)
    n_inputs = int(data.get("n_inputs", 0))
    rows: list[dict[str, Any]] = []
    for item in data.get("rows", []):
        key = item.get("key")
        rows.append({
            **record_base("hard_core_stability_bit", path),
            "mode": mode,
            "schedule_key": key,
            "word_round": item.get("word_round"),
            "bit": int(key.rsplit(".b", 1)[1]) if isinstance(key, str) and ".b" in key else None,
            "core_count": item.get("core_count"),
            "shell_count": item.get("shell_count"),
            "core_fraction": item.get("core_fraction"),
            "shell_fraction": item.get("shell_fraction"),
            "hard_core_class": hard_core_class(item, n_inputs),
            "n_inputs": n_inputs,
            "tags": [mode, "hard_core_stability"],
        })
    return rows


def ingest_tanner_motifs(path: Path) -> list[dict[str, Any]]:
    data = load_json(path)
    rows: list[dict[str, Any]] = []
    for rank, family in enumerate(data.get("families", []), start=1):
        rows.append({
            **record_base("tanner_motif_family", path),
            "rank": rank,
            "family_relation": family.get("family_relation"),
            "family_key": family.get("family_key"),
            "profile_count": family.get("profile_count"),
            "record_count": family.get("record_count"),
            "gaps": family.get("gaps"),
            "total_four_cycles": family.get("total_four_cycles_in_records"),
            "max_multiplicity": family.get("max_multiplicity"),
            "tags": ["tanner", "bp_feature"],
        })
    return rows


def default_paths(include_math_results: bool = False) -> dict[str, list[Path]]:
    block2 = REPO / "headline_hunt/bets/block2_wang/results"
    cascade = REPO / "headline_hunt/bets/cascade_aux_encoding/results"
    math_results = REPO / "headline_hunt/bets/math_principles/results"
    search = block2 / "search_artifacts"
    paths = {
        "basin_catalog": [block2 / "20260428_F339_bit19_narrow_basin_catalog.json"],
        "active_subset": sorted(search.glob("*bit19_fullpool_size5_chunk*_64x3x4k.json")),
        "local_search": sorted([
            *search.glob("*bit19_*continue_8x50k.json"),
            *search.glob("*bit19_*seed*_8x50k.json"),
        ]),
        "hard_core_stability": [
            cascade / "20260428_F332_sr60_6cand_hard_core_stability.json",
            cascade / "20260428_F336_sr61_4cand_hard_core_stability.json",
        ],
        "tanner_motif": [
            cascade / "20260428_F331_sr60_tanner_motif_compare_maxlabels16.json",
        ],
    }
    if include_math_results:
        paths["active_subset"].extend([
            math_results / "20260429_F344_submodular_mask_calibration_scan.json",
            math_results / "20260429_F347_radius1_basin_walk_scan.json",
        ])
        paths["local_search"].extend([
            math_results / "20260429_F348_radius1_new88_continuation_8x50k.json",
            math_results / "20260429_F349_radius1_new88_seeded_8x50k.json",
            math_results / "20260429_F350_radius1_new88_polish.json",
        ])
        paths["active_subset"] = sorted(set(paths["active_subset"]))
        paths["local_search"] = sorted(set(paths["local_search"]))
    return paths


def build_manifest(include_math_results: bool = False) -> list[dict[str, Any]]:
    paths = default_paths(include_math_results=include_math_results)
    records: list[dict[str, Any]] = []
    for path in paths["basin_catalog"]:
        if path.exists():
            records.extend(ingest_basin_catalog(path))
    for path in paths["active_subset"]:
        records.extend(ingest_active_subset_scan(path))
    for path in paths["local_search"]:
        records.extend(ingest_local_search(path))
    for path in paths["hard_core_stability"]:
        if path.exists():
            records.extend(ingest_hard_core_stability(path))
    for path in paths["tanner_motif"]:
        if path.exists():
            records.extend(ingest_tanner_motifs(path))
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for record in records:
            f.write(json.dumps(record, sort_keys=True))
            f.write("\n")


def write_summary(
    path: Path,
    records: list[dict[str, Any]],
    include_math_results: bool = False,
) -> dict[str, Any]:
    by_kind = Counter(record["kind"] for record in records)
    score_records = [
        record for record in records
        if record.get("score") is not None
    ]
    best_scores: dict[str, Any] = {}
    for kind in sorted({record["kind"] for record in score_records}):
        rows = [record for record in score_records if record["kind"] == kind]
        best_scores[kind] = min(record["score"] for record in rows)
    summary = {
        "record_count": len(records),
        "by_kind": dict(sorted(by_kind.items())),
        "best_scores": best_scores,
        "manifest_scope": {
            "block2_candidate": BIT19_CANDIDATE,
            "active_subset_records": by_kind.get("block2_active_subset", 0),
            "local_search_records": by_kind.get("block2_local_search", 0),
            "hard_core_modes": sorted({
                record.get("mode") for record in records
                if record["kind"] == "hard_core_stability_bit"
            }),
        },
        "include_math_results": include_math_results,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")
    return summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--include-math-results", action="store_true",
                    help="Include math_principles calibration scans and continuations.")
    ap.add_argument("--out-jsonl", type=Path, default=REPO / "headline_hunt/bets/math_principles/data/20260429_principles_manifest.jsonl")
    ap.add_argument("--summary-json", type=Path, default=REPO / "headline_hunt/bets/math_principles/results/20260429_manifest_summary.json")
    args = ap.parse_args()

    records = build_manifest(include_math_results=args.include_math_results)
    write_jsonl(args.out_jsonl, records)
    summary = write_summary(
        args.summary_json,
        records,
        include_math_results=args.include_math_results,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
