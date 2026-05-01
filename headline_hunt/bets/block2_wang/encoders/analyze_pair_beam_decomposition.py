#!/usr/bin/env python3
"""Analyze how a pair-beam record is covered by selected two-bit moves.

pair_beam_search.py records the selected pair pool and the final bit set for
best_seen/top_records/new_records, but it does not keep the beam parent chain.
This tool recovers useful structure by finding pair-pool entries contained in
the target bit set and exact pair covers when they exist.
"""

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def bit_index(raw: int | dict[str, Any]) -> int:
    if isinstance(raw, int):
        return raw
    return int(raw["bit_index"])


def bit_label(idx: int) -> str:
    return f"W{57 + idx // 32}:b{idx % 32}"


def normalize_bits(raw_bits: list[int | dict[str, Any]]) -> list[int]:
    return sorted({bit_index(raw) for raw in raw_bits})


def select_entry(payload: dict[str, Any], spec: str) -> tuple[str, dict[str, Any]]:
    if spec == "best_seen":
        return spec, payload["best_seen"]
    if ":" not in spec:
        raise ValueError("--entry must be best_seen, top:N, or new:N")
    section, raw_idx = spec.split(":", 1)
    idx = int(raw_idx)
    if idx < 1:
        raise ValueError("entry indexes are 1-based")
    if section == "top":
        return spec, payload["top_records"][idx - 1]
    if section == "new":
        return spec, payload["new_records"][idx - 1]
    raise ValueError("--entry must be best_seen, top:N, or new:N")


def pair_summary(rank: int, pair: dict[str, Any]) -> dict[str, Any]:
    bits = normalize_bits(pair["bit_indices"])
    return {
        "rank": rank,
        "bit_indices": bits,
        "labels": [bit_label(idx) for idx in bits],
        "hw_total": pair.get("hw_total"),
        "score": pair.get("score"),
        "delta_hw63": pair.get("delta_hw63"),
        "net_delta": pair.get("net_delta"),
        "total_repair": pair.get("total_repair"),
        "total_damage": pair.get("total_damage"),
    }


def find_exact_covers(
    target_bits: set[int],
    internal_pairs: list[dict[str, Any]],
    max_solutions: int,
) -> list[list[dict[str, Any]]]:
    by_bit: dict[int, list[dict[str, Any]]] = {bit: [] for bit in target_bits}
    for pair in internal_pairs:
        a, b = pair["bit_indices"]
        by_bit[a].append(pair)
        by_bit[b].append(pair)
    for pairs in by_bit.values():
        pairs.sort(key=lambda p: p["rank"])

    solutions: list[list[dict[str, Any]]] = []

    def rec(remaining: set[int], chosen: list[dict[str, Any]]) -> None:
        if len(solutions) >= max_solutions:
            return
        if not remaining:
            solutions.append(chosen[:])
            return
        pivot = min(remaining, key=lambda bit: len(by_bit.get(bit, ())))
        for pair in by_bit.get(pivot, []):
            bits = set(pair["bit_indices"])
            if not bits <= remaining:
                continue
            rec(remaining - bits, chosen + [pair])

    if len(target_bits) % 2 == 0:
        rec(set(target_bits), [])
    return solutions


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--artifact", required=True, help="pair_beam_search.py JSON artifact")
    ap.add_argument("--entry", default="best_seen", help="best_seen, top:N, or new:N")
    ap.add_argument("--max-decompositions", type=int, default=12)
    ap.add_argument("--frontier-limit", type=int, default=40)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    path = Path(args.artifact)
    payload = load_json(path)
    entry_name, entry = select_entry(payload, args.entry)
    target_bits = normalize_bits(entry.get("bits", []))
    target = set(target_bits)

    internal_pairs = []
    frontier_pairs = []
    external_pairs = 0
    for rank, pair in enumerate(payload.get("selected_pairs", []), start=1):
        bits = set(normalize_bits(pair["bit_indices"]))
        summary = pair_summary(rank, pair)
        overlap = bits & target
        if bits <= target:
            internal_pairs.append(summary)
        elif overlap:
            frontier_pairs.append(summary | {
                "target_overlap": sorted(overlap),
                "target_overlap_labels": [bit_label(idx) for idx in sorted(overlap)],
            })
        else:
            external_pairs += 1

    covered = sorted({bit for pair in internal_pairs for bit in pair["bit_indices"]})
    uncovered = sorted(target - set(covered))
    covers = find_exact_covers(target, internal_pairs, args.max_decompositions)
    decompositions = []
    for cover in covers:
        ranks = [pair["rank"] for pair in cover]
        decompositions.append({
            "pair_ranks": ranks,
            "rank_sum": sum(ranks),
            "max_rank": max(ranks) if ranks else None,
            "pairs": cover,
        })
    decompositions.sort(key=lambda d: (d["rank_sum"], d["max_rank"] or 0, d["pair_ranks"]))

    result = {
        "description": "pair-beam target decomposition against selected pair pool",
        "source_artifact": str(path),
        "entry": entry_name,
        "candidate": payload.get("candidate"),
        "init_W": payload.get("init_W"),
        "init_hw": payload.get("init_hw"),
        "target_W": entry.get("W"),
        "target_hw": entry.get("hw_total"),
        "target_score": entry.get("score"),
        "target_bits": [
            {"bit_index": idx, "label": bit_label(idx)}
            for idx in target_bits
        ],
        "selected_pair_count": len(payload.get("selected_pairs", [])),
        "internal_pair_count": len(internal_pairs),
        "frontier_pair_count": len(frontier_pairs),
        "external_pair_count": external_pairs,
        "coverage": {
            "covered_bits": [
                {"bit_index": idx, "label": bit_label(idx)}
                for idx in covered
            ],
            "uncovered_bits": [
                {"bit_index": idx, "label": bit_label(idx)}
                for idx in uncovered
            ],
        },
        "internal_pairs": internal_pairs,
        "decompositions": decompositions,
        "frontier_pairs": frontier_pairs[:args.frontier_limit],
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        f"wrote {out}: {len(internal_pairs)} internal pairs, "
        f"{len(decompositions)} exact covers"
    )


if __name__ == "__main__":
    main()
