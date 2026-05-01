#!/usr/bin/env python3
"""
build_single_candidate_priority_spec.py - Emit F397-style priority specs for one CNF.

This is the small follow-on needed for out-of-band candidates such as
bit2_ma896ee41, which are not part of the F332 six-candidate stability panel
but can still be mapped onto the same F286/F332 priority key recipes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from build_decision_priority_specs import (
    REPO,
    DEFAULT_STABILITY,
    build_priority_set,
    f286_keys,
    f332_stable_keys,
    hard_core_index,
    load_json,
    parse_candidate_from_cnf,
    rel,
)


DEFAULT_OUT_JSON = (
    REPO / "headline_hunt/bets/programmatic_sat_propagator/results/preflight_2026-04-29/F409_bit2_decision_priority_specs.json"
)


def build_spec(args: argparse.Namespace) -> dict[str, Any]:
    stability = load_json(args.stability)
    cnf = rel(args.cnf)
    candidate = args.candidate or parse_candidate_from_cnf(cnf)
    key_sets = {
        "f286_132_conservative": f286_keys(),
        "f332_139_stable6": f332_stable_keys(stability),
    }
    index = hard_core_index(args.hard_core)
    priority_sets = {
        name: build_priority_set(keys, index)
        for name, keys in key_sets.items()
    }
    candidate_spec = {
        "candidate": candidate,
        "name": args.name or candidate.split("_", 1)[0],
        "cnf": cnf,
        "hard_core_artifact": rel(args.hard_core),
        "priority_sets": priority_sets,
    }
    summary = {
        "report_id": args.report_id,
        "stability_source": rel(args.stability),
        "candidate_count": 1,
        "priority_sets": {
            name: {"requested_count": len(keys)}
            for name, keys in key_sets.items()
        },
        "all_candidates_complete": {
            name: not candidate_spec["priority_sets"][name]["missing"]
            for name in key_sets
        },
        "candidate_var_counts": [
            {
                "candidate": candidate,
                **{
                    name: candidate_spec["priority_sets"][name]["var_count"]
                    for name in key_sets
                },
            }
        ],
    }
    return {
        "summary": summary,
        "candidate_specs": [candidate_spec],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")


def write_md(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    spec = payload["candidate_specs"][0]
    lines = [
        "---",
        "date: 2026-04-30",
        "bet: programmatic_sat_propagator",
        "status: SINGLE_CANDIDATE_DECISION_PRIORITY_SPECS",
        "---",
        "",
        f"# {summary['report_id']}: single-candidate decision-priority specs",
        "",
        "## Summary",
        "",
        f"Candidate: `{spec['candidate']}`.",
        f"CNF: `{spec['cnf']}`.",
        f"Hard-core artifact: `{spec['hard_core_artifact']}`.",
        f"Stability source: `{summary['stability_source']}`.",
        f"Completeness: `{summary['all_candidates_complete']}`.",
        "",
        "## Priority Sets",
        "",
        "| Set | Requested vars | Present vars | Missing vars |",
        "|---|---:|---:|---:|",
    ]
    for name, row in spec["priority_sets"].items():
        lines.append(
            f"| `{name}` | {row['requested_count']} | {row['var_count']} | {len(row['missing'])} |"
        )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stability", type=Path, default=DEFAULT_STABILITY)
    ap.add_argument("--cnf", type=Path, required=True)
    ap.add_argument("--hard-core", type=Path, required=True)
    ap.add_argument("--candidate", default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--report-id", default="F409")
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    payload = build_spec(args)
    write_json(args.out_json, payload)
    write_md(args.out_md or args.out_json.with_suffix(".md"), payload)
    print(json.dumps(payload["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
