#!/usr/bin/env python3
"""
design_conflict_guided_bridge.py - Sound CDCL bridge plan from strict-kernel splits.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from headline_hunt.bets.math_principles.encoders.continue_atlas_from_seed import repo_path  # noqa: E402


DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F379_conflict_guided_bridge_design.json"
)
SOURCES = {
    "F377": REPO / "headline_hunt/bets/math_principles/results/20260429_F377_strict_kernel_basin_comparison.json",
    "F378": REPO / "headline_hunt/bets/math_principles/results/20260429_F378_f322_kernel_safe_depth2_beam.json",
    "IPASIR": REPO / "headline_hunt/bets/programmatic_sat_propagator/propagators/IPASIR_UP_API.md",
    "F324": REPO / "headline_hunt/bets/cascade_aux_encoding/results/20260429_F324_universal_core_is_search_artifact_not_encoder.md",
    "F325": REPO / "headline_hunt/bets/cascade_aux_encoding/results/20260429_F325_pair_propagation_confirms_search_invariant.md",
    "F326": REPO / "headline_hunt/bets/cascade_aux_encoding/results/20260429_F326_multicand_up_universal_481.md",
}


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def rec(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "score": row.get("score", row.get("default_score")),
        "a57": row["rec"]["a57_xor_hw"],
        "D61": row["rec"]["D61_hw"],
        "chart": ",".join(row["rec"]["chart_top2"]),
        "tail63": row["rec"]["tail63_state_diff_hw"],
    }


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    return (
        "conflict_guided_bridge_design_ready",
        "Use F378 as a diagnostic target for sound CDCL/propagator experiments; do not inject empirical hard-core clauses as facts.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: CONFLICT_GUIDED_BRIDGE_DESIGN",
        "---",
        "",
        "# F379: conflict-guided bridge design",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        payload["decision"],
        "",
        "The strict-kernel basin work gives a diagnostic target, not another reason to keep mutating dM.",
        "The design rule is soundness first: arithmetic consequences may be propagated as clauses, while empirical hard-core observations become decision priorities or assumption cubes until proven.",
        "",
        "## Diagnostic Targets",
        "",
        "| Target | Source | Score | a57 | D61 | Chart | Use |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for row in payload["diagnostic_targets"]:
        r = row["rec"]
        lines.append(
            f"| `{row['id']}` | `{row['source']}` | {r['score']} | {r['a57']} | "
            f"{r['D61']} | `{r['chart']}` | {row['use']} |"
        )
    lines.extend([
        "",
        "## Soundness Split",
        "",
        "| Class | Allowed API hooks | Rule |",
        "|---|---|---|",
    ])
    for row in payload["soundness_split"]:
        lines.append(
            f"| `{row['class']}` | `{', '.join(row['api_hooks'])}` | {row['rule']} |"
        )
    lines.extend([
        "",
        "## Experiments",
        "",
        "| Step | Goal | Output | Stop condition |",
        "|---|---|---|---|",
    ])
    for row in payload["experiments"]:
        lines.append(
            f"| `{row['step']}` | {row['goal']} | {row['output']} | {row['stop_condition']} |"
        )
    lines.extend([
        "",
        "## Implementation Notes",
        "",
    ])
    for item in payload["implementation_notes"]:
        lines.append(f"- {item}")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    f377 = read_json(SOURCES["F377"])
    f378 = read_json(SOURCES["F378"])
    by_label = {row["label"]: row for row in f377["front_rows"]}
    diagnostic_targets = [
        {
            "id": "scalar_floor",
            "source": "F372/F377",
            "rec": {
                "score": by_label["F372_best_score"]["score"],
                "a57": by_label["F372_best_score"]["a57"],
                "D61": by_label["F372_best_score"]["D61"],
                "chart": by_label["F372_best_score"]["chart"],
                "tail63": None,
            },
            "use": "baseline strict score floor to beat",
        },
        {
            "id": "guard_corner",
            "source": "F374/F377",
            "rec": {
                "score": by_label["F374_low_guard"]["score"],
                "a57": by_label["F374_low_guard"]["a57"],
                "D61": by_label["F374_low_guard"]["D61"],
                "chart": by_label["F374_low_guard"]["chart"],
                "tail63": None,
            },
            "use": "a57=4 branch; chart repair target",
        },
        {
            "id": "D61_floor_guard_explosion",
            "source": "F378",
            "rec": rec(f378["best_d61"]),
            "use": "diagnostic cube: D61 reaches chamber floor while guard explodes",
        },
        {
            "id": "D61_to_guard_bridge",
            "source": "F375/F377",
            "rec": {
                "score": by_label["F375_D61_to_guard"]["score"],
                "a57": by_label["F375_D61_to_guard"]["a57"],
                "D61": by_label["F375_D61_to_guard"]["D61"],
                "chart": by_label["F375_D61_to_guard"]["chart"],
                "tail63": None,
            },
            "use": "confirmed bridge direction; loses D61 while repairing guard",
        },
    ]
    payload = {
        "report_id": "F379",
        "sources": {key: repo_path(path) for key, path in SOURCES.items()},
        "diagnostic_targets": diagnostic_targets,
        "soundness_split": [
            {
                "class": "sound_arithmetic",
                "api_hooks": ["cb_propagate", "cb_add_reason_clause_lit", "cb_check_found_model"],
                "rule": "Only proven cascade arithmetic, schedule recurrence, and modular-add consequences may be injected as clauses.",
            },
            {
                "class": "empirical_core_prior",
                "api_hooks": ["cb_decide"],
                "rule": "F286/F324-F326 hard-core bits are decision priorities, not clauses, unless separately derived for the current CNF.",
            },
            {
                "class": "diagnostic_assumption_cube",
                "api_hooks": ["solver assumptions", "conflict/decision logging"],
                "rule": "F378 and F375 split points become cubes for measuring conflict paths and extracting learned-clause candidates.",
            },
            {
                "class": "forbidden_unsound_clause",
                "api_hooks": [],
                "rule": "Do not add clauses merely saying the chamber target must hold; that would solve a different problem.",
            },
        ],
        "experiments": [
            {
                "step": "E1_bridge_cubes",
                "goal": "Turn F378 D61=4/a57=19 and F375 a57=5/D61=13 into assumption cubes against the F322/F372 CNFs.",
                "output": "conflict counts, first-conflict levels, and learned clauses touching W57-W60/core bits",
                "stop_condition": "no distinct conflict signature versus baseline after 20 cubes",
            },
            {
                "step": "E2_cb_decide_core_priority",
                "goal": "Use 132 hard-core bits plus F378 split bits as cb_decide priorities without adding clauses.",
                "output": "conflict/decision/restart deltas against vanilla CaDiCaL on the same CNFs",
                "stop_condition": "<1.5x conflict reduction at 100k and 1M caps",
            },
            {
                "step": "E3_sound_rule4_bridge",
                "goal": "Implement only sound Rule 4/5 modular consequences at the D61/a57 bridge boundary.",
                "output": "propagations fired, reason-clause sizes, conflict reduction, and zero model-rejection false positives",
                "stop_condition": "reason clauses exceed useful size or conflicts do not drop by >=2x on bridge cubes",
            },
        ],
        "implementation_notes": [
            "Use `add_observed_var` narrowly: W57-W60, the 132 hard-core schedule bits, and register bits needed for D61/a57 bridge rules.",
            "F378's D61=4/a57=19 point is the first diagnostic where the chamber D61 floor is reached under strict kernel; it should be the first cube.",
            "The bridge experiments should log learned clauses and variable decision ranks, because the thesis is about CDCL trajectory, not UP.",
            "A successful propagator must beat common-mode search by reducing conflicts or producing a bridge clause; another local-search run is not enough evidence.",
        ],
    }
    payload["verdict"], payload["decision"] = verdict(payload)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    out_md = args.out_md or args.out_json.with_suffix(".md")
    write_md(out_md, payload)
    print(json.dumps({
        "verdict": payload["verdict"],
        "targets": [row["id"] for row in payload["diagnostic_targets"]],
        "experiments": [row["step"] for row in payload["experiments"]],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
