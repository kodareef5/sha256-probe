#!/usr/bin/env python3
"""
compare_hard_core_jsons.py - Compare identify_hard_core.py JSON outputs.

The comparison is semantic for schedule variables: W1/W2 round/bit keys are
used instead of raw SAT variable numbers, so matching encoders can be compared
even when aux variable numbering differs.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def schedule_key(entry: dict[str, Any]) -> str:
    return f"{entry['word']}[{entry['round']}].b{entry['bit']}"


def schedule_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [entry for entry in entries if "word" in entry]


def count_by_word_round(entries: list[dict[str, Any]]) -> dict[str, int]:
    counts = Counter(
        f"{entry['word']}[{entry['round']}]"
        for entry in schedule_entries(entries)
    )
    return dict(sorted(counts.items()))


def load(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def set_summary(left: set[str], right: set[str]) -> dict[str, Any]:
    inter = left & right
    union = left | right
    return {
        "left_count": len(left),
        "right_count": len(right),
        "intersection_count": len(inter),
        "union_count": len(union),
        "jaccard": round(len(inter) / len(union), 6) if union else 1.0,
        "left_only": sorted(left - right),
        "right_only": sorted(right - left),
    }


def compact_input_summary(data: dict[str, Any]) -> dict[str, Any]:
    core_entries = schedule_entries(data.get("schedule_core", []))
    shell_entries = schedule_entries(data.get("schedule_shell", []))
    return {
        "cnf": data.get("cnf"),
        "n_free": data.get("n_free"),
        "n_vars": data.get("n_vars"),
        "n_clauses": data.get("n_clauses"),
        "shell_size": data.get("shell_size"),
        "core_size": data.get("core_size"),
        "schedule_core_count": len(core_entries),
        "schedule_shell_count": len(shell_entries),
        "aux_core_count": data.get("aux_core_count"),
        "const_true_core_count": data.get("const_true_core_count"),
        "schedule_core_by_word_round": count_by_word_round(data.get("schedule_core", [])),
        "schedule_shell_by_word_round": count_by_word_round(data.get("schedule_shell", [])),
    }


def compare(left: dict[str, Any], right: dict[str, Any], left_name: str, right_name: str) -> dict[str, Any]:
    left_core = {schedule_key(entry) for entry in schedule_entries(left.get("schedule_core", []))}
    right_core = {schedule_key(entry) for entry in schedule_entries(right.get("schedule_core", []))}
    left_shell = {schedule_key(entry) for entry in schedule_entries(left.get("schedule_shell", []))}
    right_shell = {schedule_key(entry) for entry in schedule_entries(right.get("schedule_shell", []))}

    return {
        "left_name": left_name,
        "right_name": right_name,
        "left": compact_input_summary(left),
        "right": compact_input_summary(right),
        "schedule_core": set_summary(left_core, right_core),
        "schedule_shell": set_summary(left_shell, right_shell),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("left", type=Path)
    ap.add_argument("right", type=Path)
    ap.add_argument("--left-name", default="left")
    ap.add_argument("--right-name", default="right")
    ap.add_argument("--out-json", type=Path)
    args = ap.parse_args()

    summary = compare(
        load(args.left),
        load(args.right),
        args.left_name,
        args.right_name,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        with args.out_json.open("w") as f:
            json.dump(summary, f, indent=2, sort_keys=True)
            f.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
