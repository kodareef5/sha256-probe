#!/usr/bin/env python3
"""
generate_bridge_cubes.py - Coordinate/optional-literal cubes for F379 E1.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from headline_hunt.bets.block2_wang.encoders.search_schedule_space import expand_schedule  # noqa: E402
from headline_hunt.bets.math_principles.encoders.continue_atlas_from_seed import (  # noqa: E402
    from_hex_words,
    repo_path,
)
from headline_hunt.bets.programmatic_sat_propagator.propagators.varmap_loader import VarMap  # noqa: E402


DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F380_bridge_cubes.json"
)
DEFAULT_OUT_TXT = (
    REPO
    / "headline_hunt/bets/math_principles/data/20260429_F380_bridge_cubes.dimacs.txt"
)
SOURCES = {
    "F374": REPO / "headline_hunt/bets/math_principles/results/20260429_F374_kernel_safe_pareto_bridge.json",
    "F375": REPO / "headline_hunt/bets/math_principles/results/20260429_F375_kernel_safe_bridge_anchor_continuation.json",
    "F378": REPO / "headline_hunt/bets/math_principles/results/20260429_F378_f322_kernel_safe_depth2_beam.json",
}


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def chart(row: dict[str, Any]) -> str:
    return ",".join(row["rec"]["chart_top2"])


def candidate_summary(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "score": row.get("default_score", row.get("score")),
        "profile_score": row.get("profile_score"),
        "a57": row["rec"]["a57_xor_hw"],
        "D61": row["rec"]["D61_hw"],
        "chart": chart(row),
        "tail63": row["rec"]["tail63_state_diff_hw"],
    }


def select_targets() -> list[dict[str, Any]]:
    f374 = read_json(SOURCES["F374"])
    f375 = read_json(SOURCES["F375"])
    f378 = read_json(SOURCES["F378"])
    f375_bridge = None
    for row in f375["anchor_runs"]:
        if row["label"] == "best_d61":
            f375_bridge = row["best_profile"]
            break
    if f375_bridge is None:
        raise ValueError("F375 has no best_d61 bridge")
    return [
        {
            "id": "F378_D61_floor_guard_explosion",
            "source": "F378",
            "candidate": f378["best_d61"],
            "why": "D61 reaches chamber floor 4 while guard explodes to a57=19.",
        },
        {
            "id": "F375_D61_to_guard_bridge",
            "source": "F375",
            "candidate": f375_bridge,
            "why": "D61-side bridge repairs guard to a57=5 while D61 rises to 13.",
        },
        {
            "id": "F374_low_guard_corner",
            "source": "F374",
            "candidate": f374["anchors"]["best_guard"],
            "why": "Nontrivial a57=4 corner, off chamber chart.",
        },
    ]


def schedule_xor_bits(candidate: dict[str, Any], rounds: list[int]) -> dict[str, list[int]]:
    M1 = from_hex_words(candidate["M1"])
    M2 = from_hex_words(candidate["M2"])
    W1 = expand_schedule(M1)
    W2 = expand_schedule(M2)
    out = {}
    for r in rounds:
        diff = (W1[r] ^ W2[r]) & 0xFFFFFFFF
        out[str(r)] = [(diff >> bit) & 1 for bit in range(32)]
    return out


def subset_bits(bits_by_round: dict[str, list[int]], subset: str) -> dict[str, list[int]]:
    if subset == "w57_w60":
        wanted = {"57", "58", "59", "60"}
    elif subset == "w61":
        wanted = {"61"}
    elif subset == "w57_w63":
        wanted = {str(r) for r in range(57, 64)}
    elif subset == "ones_w57_w63":
        return {
            r: [bit for bit, value in enumerate(bits) if value]
            for r, bits in bits_by_round.items()
            if any(bits)
        }
    else:
        raise ValueError(f"unknown subset {subset!r}")
    return {r: bits for r, bits in bits_by_round.items() if r in wanted}


def to_assumptions(
    vm: VarMap | None,
    bits_by_round: dict[str, list[int]],
    ones_only: bool,
) -> dict[str, Any]:
    if vm is None:
        return {"available": False, "assumptions": [], "constant_conflicts": [], "constant_satisfied": 0}
    assumptions = []
    conflicts = []
    constant_satisfied = 0
    for r_str, bits in bits_by_round.items():
        r = int(r_str)
        if ones_only:
            iterable = [(bit, 1) for bit in bits]
        else:
            iterable = list(enumerate(bits))
        for bit, value in iterable:
            lit = vm.w_lit(r, bit)
            if abs(lit) == 1:
                if (lit == 1) == bool(value):
                    constant_satisfied += 1
                else:
                    conflicts.append({"round": r, "bit": bit, "value": value, "literal": lit})
                continue
            assumptions.append(lit if value else -lit)
    return {
        "available": True,
        "assumptions": assumptions,
        "constant_conflicts": conflicts,
        "constant_satisfied": constant_satisfied,
    }


def cube_row(
    target: dict[str, Any],
    subset: str,
    vm: VarMap | None,
    rounds: list[int],
) -> dict[str, Any]:
    bits = schedule_xor_bits(target["candidate"], rounds)
    sub = subset_bits(bits, subset)
    ones_only = subset.startswith("ones_")
    bit_count = sum(len(bits) for bits in sub.values())
    one_count = sum(sum(bits) if not ones_only else len(bits) for bits in sub.values())
    lit = to_assumptions(vm, sub, ones_only)
    return {
        "target": target["id"],
        "source": target["source"],
        "why": target["why"],
        "candidate": candidate_summary(target["candidate"]),
        "subset": subset,
        "coordinate_bits": sub,
        "bit_count": bit_count,
        "one_count": one_count,
        "literal_cube": {
            "available": lit["available"],
            "assumption_count": len(lit["assumptions"]),
            "assumptions": lit["assumptions"],
            "constant_conflicts": lit["constant_conflicts"],
            "constant_satisfied": lit["constant_satisfied"],
        },
    }


def write_txt(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# F380 bridge cubes",
        f"# varmap: {payload['varmap'] or 'coordinate-only'}",
        "# Each non-comment line: cube_id followed by DIMACS assumption literals.",
    ]
    for cube in payload["cubes"]:
        if not cube["literal_cube"]["available"]:
            continue
        assumptions = cube["literal_cube"]["assumptions"]
        cube_id = f"{cube['target']}::{cube['subset']}"
        lines.append(" ".join([cube_id] + [str(lit) for lit in assumptions]))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: BRIDGE_CUBE_GENERATOR",
        "---",
        "",
        "# F380: bridge cube generator",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        payload["decision"],
        f"Varmap: `{payload['varmap'] or 'coordinate-only'}`.",
        "",
        "| Target | Subset | Bits | Ones | Assumptions | Const conflicts | Candidate |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for cube in payload["cubes"]:
        cand = cube["candidate"]
        lines.append(
            f"| `{cube['target']}` | `{cube['subset']}` | {cube['bit_count']} | "
            f"{cube['one_count']} | {cube['literal_cube']['assumption_count']} | "
            f"{len(cube['literal_cube']['constant_conflicts'])} | "
            f"a57={cand['a57']} D61={cand['D61']} chart=`{cand['chart']}` |"
        )
    lines.extend([
        "",
        "## Usage",
        "",
        "Use coordinate cubes directly for propagator diagnostics. If a matching varmap is supplied, "
        "the `.dimacs.txt` sidecar gives assumption literals for CaDiCaL-style runs. "
        "Do not use cubes from a mismatched kernel-bit CNF as proof artifacts; they are diagnostics.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--varmap", type=Path, default=None)
    ap.add_argument("--subsets", default="ones_w57_w63,w61,w57_w60")
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-txt", type=Path, default=DEFAULT_OUT_TXT)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    vm = VarMap.load(args.varmap) if args.varmap else None
    rounds = list(range(57, 64))
    subsets = [part.strip() for part in args.subsets.split(",") if part.strip()]
    cubes = [
        cube_row(target, subset, vm, rounds)
        for target in select_targets()
        for subset in subsets
    ]
    literal_available = sum(1 for cube in cubes if cube["literal_cube"]["available"])
    payload = {
        "report_id": "F380",
        "sources": {key: repo_path(path) for key, path in SOURCES.items()},
        "varmap": repo_path(args.varmap) if args.varmap else None,
        "subsets": subsets,
        "cubes": cubes,
        "literal_cube_count": literal_available,
    }
    payload["verdict"] = "bridge_cubes_generated"
    payload["decision"] = (
        "Run E1 with these coordinate cubes; add a matching varmap to materialize DIMACS assumptions."
        if vm is None else
        "Run E1 with the generated DIMACS assumption sidecar and compare conflict signatures."
    )
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    write_txt(args.out_txt, payload)
    out_md = args.out_md or args.out_json.with_suffix(".md")
    write_md(out_md, payload)
    print(json.dumps({
        "verdict": payload["verdict"],
        "cubes": len(cubes),
        "literal_cube_count": literal_available,
        "out_txt": repo_path(args.out_txt),
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
