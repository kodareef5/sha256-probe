#!/usr/bin/env python3
"""
minimize_bridge_cube_core.py - Greedy UNSAT-core minimization for bridge cubes.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from smoke_bridge_cubes import (  # noqa: E402
    DEFAULT_CNF,
    DEFAULT_CUBES,
    parse_cubes,
    read_cnf,
    repo_path,
    write_cube_cnf,
)

REPO = Path(__file__).resolve().parents[4]
DEFAULT_VARMAP = REPO / "headline_hunt/bets/math_principles/data/20260429_F380_aux_force_sr60_n32_bit31_m17149975_fillffffffff.varmap.json"
DEFAULT_OUT_JSON = REPO / "headline_hunt/bets/math_principles/results/20260429_F383_bridge_cube_unsat_core.json"


def load_reverse_varmap(path: Path) -> dict[int, list[dict[str, Any]]]:
    with path.open() as f:
        data = json.load(f)
    out: dict[int, list[dict[str, Any]]] = {}
    for r_str, lits in data["aux_W"].items():
        r = int(r_str)
        for bit, lit in enumerate(lits):
            if abs(lit) <= 1:
                continue
            out.setdefault(abs(lit), []).append({
                "kind": "W_xor",
                "round": r,
                "bit": bit,
                "polarity": 1 if lit > 0 else -1,
            })
    return out


def lit_coordinate(lit: int, reverse: dict[int, list[dict[str, Any]]]) -> dict[str, Any]:
    entries = reverse.get(abs(lit), [])
    return {
        "literal": lit,
        "assumed_value": 1 if lit > 0 else 0,
        "coordinates": entries,
    }


def run_status(
    cadical: str,
    cnf_lines: list[str],
    header_idx: int,
    n_vars: int,
    n_clauses: int,
    assumptions: list[int],
    path: Path,
    timeout: int,
) -> tuple[str, float]:
    write_cube_cnf(cnf_lines, header_idx, n_vars, n_clauses, assumptions, path)
    t0 = time.time()
    proc = subprocess.run(
        [cadical, "-q", "-n", "-t", str(timeout), str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    wall = time.time() - t0
    if proc.returncode == 20:
        return "UNSATISFIABLE", wall
    if proc.returncode == 10:
        return "SATISFIABLE", wall
    return "UNKNOWN", wall


def find_cube(path: Path, cube_id: str) -> list[int]:
    for cube in parse_cubes(path):
        if cube["id"] == cube_id:
            return list(cube["assumptions"])
    raise ValueError(f"cube {cube_id!r} not found in {path}")


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    if payload["core_status"] == "UNSATISFIABLE" and payload["core_size"] < payload["initial_size"]:
        return (
            "bridge_cube_core_minimized",
            "Use the minimized coordinate core as the first bridge-conflict target.",
        )
    return (
        "bridge_cube_core_not_minimized",
        "The cube stayed UNSAT only with the full assumption set or did not reproduce UNSAT.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: BRIDGE_CUBE_UNSAT_CORE",
        "---",
        "",
        "# F383: bridge cube UNSAT core",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        payload["decision"],
        f"Cube: `{payload['cube_id']}`.",
        f"Initial assumptions: {payload['initial_size']}; minimized core: {payload['core_size']}.",
        f"Tests: {payload['tests_run']}; total wall: {payload['total_wall_seconds']}s.",
        "",
        "## Core Literals",
        "",
        "| Literal | Assumed dW | Coordinates |",
        "|---:|---:|---|",
    ]
    for row in payload["core_coordinates"]:
        coords = ", ".join(
            f"{coord['kind']}[{coord['round']}][{coord['bit']}] pol={coord['polarity']}"
            for coord in row["coordinates"]
        )
        lines.append(f"| {row['literal']} | {row['assumed_value']} | `{coords}` |")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cube-id", default="F374_low_guard_corner::w57_w60")
    ap.add_argument("--cnf", type=Path, default=DEFAULT_CNF)
    ap.add_argument("--cubes", type=Path, default=DEFAULT_CUBES)
    ap.add_argument("--varmap", type=Path, default=DEFAULT_VARMAP)
    ap.add_argument("--cadical", default=None)
    ap.add_argument("--timeout", type=int, default=2)
    ap.add_argument("--workdir", type=Path, default=Path("/tmp/F383_bridge_core"))
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    cadical = args.cadical or shutil.which("cadical")
    if not cadical:
        raise SystemExit("cadical not found")
    assumptions = find_cube(args.cubes, args.cube_id)
    header, n_vars, n_clauses, lines = read_cnf(args.cnf)
    header_idx = lines.index(header)
    args.workdir.mkdir(parents=True, exist_ok=True)
    status, wall = run_status(
        cadical,
        lines,
        header_idx,
        n_vars,
        n_clauses,
        assumptions,
        args.workdir / "initial.cnf",
        args.timeout,
    )
    if status != "UNSATISFIABLE":
        raise SystemExit(f"initial cube is not UNSAT: {status}")
    total_wall = wall
    tests = 1
    core = list(assumptions)
    changed = True
    while changed:
        changed = False
        for lit in list(core):
            trial = [item for item in core if item != lit]
            st, wall = run_status(
                cadical,
                lines,
                header_idx,
                n_vars,
                n_clauses,
                trial,
                args.workdir / "trial.cnf",
                args.timeout,
            )
            total_wall += wall
            tests += 1
            if st == "UNSATISFIABLE":
                core = trial
                changed = True
    core_status, wall = run_status(
        cadical,
        lines,
        header_idx,
        n_vars,
        n_clauses,
        core,
        args.workdir / "core.cnf",
        args.timeout,
    )
    total_wall += wall
    tests += 1
    reverse = load_reverse_varmap(args.varmap)
    payload = {
        "report_id": "F383",
        "cube_id": args.cube_id,
        "cnf": repo_path(args.cnf),
        "cubes": repo_path(args.cubes),
        "varmap": repo_path(args.varmap),
        "initial_size": len(assumptions),
        "core_size": len(core),
        "core_status": core_status,
        "core_literals": core,
        "core_coordinates": [lit_coordinate(lit, reverse) for lit in core],
        "tests_run": tests,
        "total_wall_seconds": round(total_wall, 6),
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
        "initial_size": payload["initial_size"],
        "core_size": payload["core_size"],
        "core_literals": payload["core_literals"],
        "tests": payload["tests_run"],
        "wall": payload["total_wall_seconds"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
