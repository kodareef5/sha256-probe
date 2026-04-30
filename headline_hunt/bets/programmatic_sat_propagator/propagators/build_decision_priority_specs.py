#!/usr/bin/env python3
"""
build_decision_priority_specs.py - Emit cb_decide priority var lists.

F395 exhausted the cheap clause-count axis.  This script turns the F286/F332
hard-core findings into concrete SAT-variable priority orders that a CaDiCaL
IPASIR-UP `cb_decide` hook can consume.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[4]
DEFAULT_STABILITY = (
    REPO / "headline_hunt/bets/cascade_aux_encoding/results/20260428_F332_sr60_6cand_hard_core_stability.json"
)
DEFAULT_OUT_JSON = (
    REPO / "headline_hunt/bets/programmatic_sat_propagator/results/preflight_2026-04-29/F397_decision_priority_specs.json"
)


def rel(path: Path | str) -> str:
    path = Path(path)
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def parse_candidate_from_cnf(cnf: str) -> str:
    base = Path(cnf).name
    match = re.search(r"bit(?P<bit>\d+)_m(?P<m0>[0-9a-f]+)_fill(?P<fill>[0-9a-f]+)", base)
    if not match:
        match = re.search(r"msb_m(?P<m0>[0-9a-f]+)_fill(?P<fill>[0-9a-f]+)", base)
        if not match:
            return base.replace(".cnf", "")
        return f"bit31_m{match.group('m0')}_fill{match.group('fill')}"
    return f"bit{match.group('bit')}_m{match.group('m0')}_fill{match.group('fill')}"


def key_for(item: dict[str, Any]) -> str | None:
    category = item.get("category")
    bit = item.get("bit")
    if not category or bit is None:
        return None
    word = category[:2].lower()
    round_match = re.search(r"_(\d+)$", category)
    if not round_match:
        return None
    return f"{word}[{round_match.group(1)}].b{int(bit)}"


def f286_keys() -> list[str]:
    keys = [
        "w1[57].b0",
        "w2[57].b0",
        "w2[58].b14",
        "w2[58].b26",
    ]
    for word in ("w1", "w2"):
        for round_ in (59, 60):
            for bit in range(32):
                keys.append(f"{word}[{round_}].b{bit}")
    return keys


def f332_stable_keys(stability: dict[str, Any]) -> list[str]:
    n_inputs = int(stability["n_inputs"])
    rows = [
        row for row in stability["rows"]
        if int(row.get("core_count", -1)) == n_inputs
    ]
    order_rank = {key: idx for idx, key in enumerate(f286_keys())}
    return sorted(
        (row["key"] for row in rows),
        key=lambda key: (0, order_rank[key]) if key in order_rank else (1, key),
    )


def hard_core_index(path: Path) -> dict[str, dict[str, Any]]:
    data = load_json(path)
    index: dict[str, dict[str, Any]] = {}
    for item in data.get("schedule_core", []):
        key = key_for(item)
        if key:
            index[key] = item
    return index


def build_priority_set(keys: list[str], index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    vars_: list[int] = []
    entries: list[dict[str, Any]] = []
    missing: list[str] = []
    for rank, key in enumerate(keys):
        item = index.get(key)
        if not item:
            missing.append(key)
            continue
        var = int(item["var"])
        vars_.append(var)
        entries.append({
            "rank": rank,
            "key": key,
            "var": var,
            "category": item.get("category"),
            "round": item.get("round"),
            "bit": item.get("bit"),
        })
    return {
        "requested_count": len(keys),
        "var_count": len(vars_),
        "vars": vars_,
        "entries": entries,
        "missing": missing,
        "by_category": dict(sorted(Counter(row["category"] for row in entries).items())),
    }


def build_specs(stability_path: Path) -> dict[str, Any]:
    stability = load_json(stability_path)
    key_sets = {
        "f286_132_conservative": f286_keys(),
        "f332_139_stable6": f332_stable_keys(stability),
    }
    candidate_specs = []
    for item in stability.get("inputs", []):
        hard_core_path = REPO / item["path"]
        index = hard_core_index(hard_core_path)
        priority_sets = {
            name: build_priority_set(keys, index)
            for name, keys in key_sets.items()
        }
        candidate_specs.append({
            "candidate": parse_candidate_from_cnf(item["cnf"]),
            "name": item.get("name"),
            "cnf": item.get("cnf"),
            "hard_core_artifact": item.get("path"),
            "schedule_core_count": item.get("schedule_core_count"),
            "schedule_shell_count": item.get("schedule_shell_count"),
            "priority_sets": priority_sets,
        })
    summary = {
        "report_id": "F397",
        "stability_source": rel(stability_path),
        "candidate_count": len(candidate_specs),
        "priority_sets": {
            name: {"requested_count": len(keys)}
            for name, keys in key_sets.items()
        },
        "all_candidates_complete": {
            name: all(not spec["priority_sets"][name]["missing"] for spec in candidate_specs)
            for name in key_sets
        },
        "candidate_var_counts": [
            {
                "candidate": spec["candidate"],
                **{
                    name: spec["priority_sets"][name]["var_count"]
                    for name in key_sets
                },
            }
            for spec in candidate_specs
        ],
    }
    return {
        "summary": summary,
        "candidate_specs": candidate_specs,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")


def write_md(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    lines = [
        "---",
        "date: 2026-04-30",
        "bet: programmatic_sat_propagator",
        "status: DECISION_PRIORITY_SPECS",
        "---",
        "",
        "# F397: decision-priority specs",
        "",
        "## Summary",
        "",
        f"Source: `{summary['stability_source']}`.",
        f"Candidates: {summary['candidate_count']}.",
        f"Completeness: `{summary['all_candidates_complete']}`.",
        "",
        "## Priority Sets",
        "",
        "| Set | Requested vars |",
        "|---|---:|",
    ]
    for name, row in summary["priority_sets"].items():
        lines.append(f"| `{name}` | {row['requested_count']} |")
    lines.extend([
        "",
        "## Candidate Var Counts",
        "",
        "| Candidate | F286 132 | F332 139 |",
        "|---|---:|---:|",
    ])
    for row in summary["candidate_var_counts"]:
        lines.append(
            f"| `{row['candidate']}` | {row['f286_132_conservative']} | "
            f"{row['f332_139_stable6']} |"
        )
    lines.extend([
        "",
        "## Use",
        "",
        "- Feed `priority_sets.f286_132_conservative.vars` to a `cb_decide` hook first.",
        "- Use `f332_139_stable6` as the broader comparison arm; it includes n=6-stable extras beyond F286.",
        "- Run baseline / existing propagator / F286-priority / F332-priority under the same conflict or time cap.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stability", type=Path, default=DEFAULT_STABILITY)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    payload = build_specs(args.stability)
    write_json(args.out_json, payload)
    write_md(args.out_md or args.out_json.with_suffix(".md"), payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
