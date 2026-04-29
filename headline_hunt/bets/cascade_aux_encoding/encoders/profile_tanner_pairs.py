#!/usr/bin/env python3
"""
profile_tanner_pairs.py - Semantic profile of high-multiplicity Tanner pairs.

This extends tanner_4cycle_count.py by joining high-multiplicity variable pairs
against cascade_aux varmap sidecars. It is meant for BP/LDPC design work: find
which SHA-level objects create dominant 4-cycle clusters.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def parse_cnf(path: Path) -> tuple[int, int, list[frozenset[int]]]:
    n_vars = 0
    n_clauses_decl = 0
    clauses = []
    with path.open() as f:
        for line in f:
            s = line.strip()
            if not s or s.startswith("c"):
                continue
            if s.startswith("p"):
                parts = s.split()
                n_vars = int(parts[2])
                n_clauses_decl = int(parts[3])
                continue
            lits = [int(t) for t in s.split()]
            if lits and lits[-1] == 0:
                lits = lits[:-1]
            if lits:
                clauses.append(frozenset(abs(lit) for lit in lits))
    return n_vars, n_clauses_decl, clauses


def count_var_pairs(clauses: list[frozenset[int]]) -> dict[tuple[int, int], int]:
    pair_count: dict[tuple[int, int], int] = defaultdict(int)
    for clause in clauses:
        vars_ = sorted(clause)
        for i, left in enumerate(vars_):
            for right in vars_[i + 1:]:
                pair_count[(left, right)] += 1
    return pair_count


def schedule_label(var: int, n_free: int) -> str | None:
    if var == 1:
        return "CONST_TRUE"
    if 2 <= var <= 1 + n_free * 32:
        offset = var - 2
        return f"schedule.w1[{57 + offset // 32}].b{offset % 32}"
    if 1 + n_free * 32 < var <= 1 + 2 * n_free * 32:
        offset = var - 2 - n_free * 32
        return f"schedule.w2[{57 + offset // 32}].b{offset % 32}"
    return None


def add_varmap_labels(labels: dict[int, set[str]], node: Any, prefix: str) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            add_varmap_labels(labels, value, f"{prefix}.{key}" if prefix else str(key))
    elif isinstance(node, list):
        for idx, value in enumerate(node):
            if isinstance(value, int):
                var = abs(value)
                if var > 1:
                    labels[var].add(f"{prefix}.b{idx}")
            else:
                add_varmap_labels(labels, value, f"{prefix}[{idx}]")


def load_labels(varmap: Path | None, n_free: int, n_vars: int) -> dict[int, list[str]]:
    labels: dict[int, set[str]] = defaultdict(set)
    for var in range(1, n_vars + 1):
        label = schedule_label(var, n_free)
        if label:
            labels[var].add(label)

    if varmap is not None:
        with varmap.open() as f:
            data = json.load(f)
        for section in ("aux_reg", "aux_W", "actual_p1", "actual_p2", "aux_modular_diff"):
            if section in data:
                add_varmap_labels(labels, data[section], section)

    return {var: sorted(values) for var, values in labels.items()}


def label_kind(label: str) -> str:
    if label.startswith("schedule."):
        return "schedule"
    if label.startswith("aux_reg."):
        return "aux_reg"
    if label.startswith("aux_W."):
        return "aux_W"
    if label.startswith("actual_p1."):
        return "actual_p1"
    if label.startswith("actual_p2."):
        return "actual_p2"
    if label.startswith("aux_modular_diff."):
        return "aux_modular_diff"
    if label == "CONST_TRUE":
        return "const"
    return "unmapped"


def var_summary(var: int, labels: dict[int, list[str]], max_labels: int) -> dict[str, Any]:
    found = labels.get(var, [])
    return {
        "var": var,
        "labels": found[:max_labels],
        "label_count": len(found),
        "kinds": sorted({label_kind(label) for label in found}) or ["unmapped"],
    }


def pair_record(
    pair: tuple[int, int],
    mult: int,
    labels: dict[int, list[str]],
    max_labels: int,
) -> dict[str, Any]:
    left, right = pair
    return {
        "pair": [left, right],
        "gap": right - left,
        "multiplicity": mult,
        "four_cycles": mult * (mult - 1) // 2,
        "left": var_summary(left, labels, max_labels),
        "right": var_summary(right, labels, max_labels),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cnf", type=Path)
    ap.add_argument("--varmap", type=Path)
    ap.add_argument("--n-free", type=int, default=4)
    ap.add_argument("--top", type=int, default=24)
    ap.add_argument("--min-mult", type=int, default=5)
    ap.add_argument("--gap", action="append", type=int, default=[])
    ap.add_argument("--max-labels", type=int, default=8)
    ap.add_argument("--out-json", type=Path)
    args = ap.parse_args()

    n_vars, n_clauses_decl, clauses = parse_cnf(args.cnf)
    pair_count = count_var_pairs(clauses)
    labels = load_labels(args.varmap, args.n_free, n_vars)

    multiplicity_hist = Counter(pair_count.values())
    gap_pair_hist: Counter[int] = Counter()
    gap_cycle_hist: Counter[int] = Counter()
    for (left, right), mult in pair_count.items():
        if mult < 2:
            continue
        gap = right - left
        gap_pair_hist[gap] += 1
        gap_cycle_hist[gap] += mult * (mult - 1) // 2

    high_pairs = [
        (pair, mult) for pair, mult in pair_count.items()
        if mult >= args.min_mult
    ]
    high_pairs.sort(key=lambda item: (item[1], item[0][1] - item[0][0]), reverse=True)

    top_pairs = [
        pair_record(pair, mult, labels, args.max_labels)
        for pair, mult in high_pairs[:args.top]
    ]

    top_by_gap = {}
    for gap in args.gap:
        rows = [
            (pair, mult) for pair, mult in pair_count.items()
            if pair[1] - pair[0] == gap and mult >= 2
        ]
        rows.sort(key=lambda item: item[1], reverse=True)
        top_by_gap[str(gap)] = [
            pair_record(pair, mult, labels, args.max_labels)
            for pair, mult in rows[:args.top]
        ]

    total_cycles = sum(mult * (mult - 1) // 2 for mult in pair_count.values() if mult >= 2)
    summary = {
        "cnf": str(args.cnf),
        "varmap": str(args.varmap) if args.varmap else None,
        "n_vars": n_vars,
        "n_clauses_declared": n_clauses_decl,
        "n_clauses_read": len(clauses),
        "distinct_var_pairs": len(pair_count),
        "four_cycles": total_cycles,
        "multiplicity_histogram": dict(sorted(multiplicity_hist.items())),
        "gap_pair_histogram": dict(sorted(gap_pair_hist.items())),
        "gap_cycle_histogram": dict(sorted(gap_cycle_hist.items())),
        "top_pairs": top_pairs,
        "top_by_gap": top_by_gap,
    }

    print(json.dumps({
        "n_vars": n_vars,
        "n_clauses_read": len(clauses),
        "four_cycles": total_cycles,
        "top_pairs": top_pairs[: min(8, len(top_pairs))],
    }, indent=2, sort_keys=True))
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        with args.out_json.open("w") as f:
            json.dump(summary, f, indent=2, sort_keys=True)
            f.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
