#!/usr/bin/env python3
"""
summarize_hard_core_stability.py - Aggregate hard-core schedule stability.

Given multiple identify_hard_core.py JSON files, report which semantic schedule
bits are always core, always shell, or candidate-dependent.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


def load(path: Path) -> dict[str, Any]:
    with path.open() as f:
        return json.load(f)


def schedule_key(entry: dict[str, Any]) -> str | None:
    if "word" not in entry:
        return None
    return f"{entry['word']}[{entry['round']}].b{entry['bit']}"


def word_round(key: str) -> str:
    return key.split(".b", 1)[0]


def schedule_sets(data: dict[str, Any]) -> tuple[set[str], set[str]]:
    core = {
        key for entry in data.get("schedule_core", [])
        for key in [schedule_key(entry)]
        if key is not None
    }
    shell = {
        key for entry in data.get("schedule_shell", [])
        for key in [schedule_key(entry)]
        if key is not None
    }
    return core, shell


def summarize(paths: list[Path], names: list[str]) -> dict[str, Any]:
    if names and len(names) != len(paths):
        raise ValueError("--name count must match input JSON count")
    if not names:
        names = [path.stem for path in paths]

    per_input = []
    all_keys: set[str] = set()
    core_counts: Counter[str] = Counter()
    shell_counts: Counter[str] = Counter()

    for path, name in zip(paths, names):
        data = load(path)
        core, shell = schedule_sets(data)
        all_keys |= core | shell
        core_counts.update(core)
        shell_counts.update(shell)
        per_input.append({
            "name": name,
            "path": str(path),
            "cnf": data.get("cnf"),
            "n_free": data.get("n_free"),
            "schedule_core_count": len(core),
            "schedule_shell_count": len(shell),
        })

    n = len(paths)
    rows = []
    for key in sorted(all_keys):
        rows.append({
            "key": key,
            "word_round": word_round(key),
            "core_count": core_counts[key],
            "shell_count": shell_counts[key],
            "core_fraction": round(core_counts[key] / n, 6),
            "shell_fraction": round(shell_counts[key] / n, 6),
        })

    stable_core = [row["key"] for row in rows if row["core_count"] == n]
    stable_shell = [row["key"] for row in rows if row["shell_count"] == n]
    variable = [
        row["key"] for row in rows
        if row["core_count"] not in (0, n)
    ]

    by_word_round: dict[str, dict[str, Any]] = {}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["word_round"]].append(row)
    for group, group_rows in sorted(grouped.items()):
        by_word_round[group] = {
            "bits": len(group_rows),
            "stable_core": sum(1 for row in group_rows if row["core_count"] == n),
            "stable_shell": sum(1 for row in group_rows if row["shell_count"] == n),
            "variable": sum(1 for row in group_rows if row["core_count"] not in (0, n)),
            "mean_core_fraction": round(
                sum(float(row["core_fraction"]) for row in group_rows) / len(group_rows),
                6,
            ),
        }

    return {
        "inputs": per_input,
        "n_inputs": n,
        "schedule_keys": len(rows),
        "stable_core_count": len(stable_core),
        "stable_shell_count": len(stable_shell),
        "variable_count": len(variable),
        "by_word_round": by_word_round,
        "stable_core": stable_core,
        "stable_shell": stable_shell,
        "variable": variable,
        "rows": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("json", nargs="+", type=Path)
    ap.add_argument("--name", action="append", default=[])
    ap.add_argument("--out-json", type=Path)
    args = ap.parse_args()

    summary = summarize(args.json, args.name)
    print(json.dumps({
        "n_inputs": summary["n_inputs"],
        "schedule_keys": summary["schedule_keys"],
        "stable_core_count": summary["stable_core_count"],
        "stable_shell_count": summary["stable_shell_count"],
        "variable_count": summary["variable_count"],
        "by_word_round": summary["by_word_round"],
    }, indent=2, sort_keys=True))
    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        with args.out_json.open("w") as f:
            json.dump(summary, f, indent=2, sort_keys=True)
            f.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
