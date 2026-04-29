#!/usr/bin/env python3
"""
smoke_bridge_cubes.py - Low-budget CaDiCaL smoke tests for F380 cubes.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[4]
DEFAULT_CNF = (
    REPO
    / "headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit31_m17149975_fillffffffff.cnf"
)
DEFAULT_CUBES = (
    REPO
    / "headline_hunt/bets/math_principles/data/20260429_F380_bridge_cubes.dimacs.txt"
)
DEFAULT_OUT_JSON = (
    REPO
    / "headline_hunt/bets/math_principles/results/20260429_F381_bridge_cube_smoke.json"
)


def repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def parse_cubes(path: Path) -> list[dict[str, Any]]:
    cubes = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            cubes.append({
                "id": parts[0],
                "assumptions": [int(part) for part in parts[1:]],
            })
    return cubes


def read_cnf(path: Path) -> tuple[str, int, int, list[str]]:
    lines = path.read_text().splitlines()
    header_idx = None
    n_vars = n_clauses = None
    for idx, line in enumerate(lines):
        if line.startswith("p cnf "):
            parts = line.split()
            n_vars = int(parts[2])
            n_clauses = int(parts[3])
            header_idx = idx
            break
    if header_idx is None or n_vars is None or n_clauses is None:
        raise ValueError(f"{path}: no DIMACS header")
    return lines[header_idx], n_vars, n_clauses, lines


def write_cube_cnf(
    lines: list[str],
    header_idx: int,
    n_vars: int,
    n_clauses: int,
    assumptions: list[int],
    out_path: Path,
) -> None:
    out = list(lines)
    out[header_idx] = f"p cnf {n_vars} {n_clauses + len(assumptions)}"
    out.extend(f"{lit} 0" for lit in assumptions)
    out_path.write_text("\n".join(out) + "\n")


def parse_status(stdout: str, returncode: int) -> str:
    for line in stdout.splitlines():
        if line.startswith("s "):
            return line[2:].strip()
    if returncode == 10:
        return "SATISFIABLE"
    if returncode == 20:
        return "UNSATISFIABLE"
    return "UNKNOWN"


def parse_metric(stdout: str, name: str) -> int | None:
    for line in stdout.splitlines():
        if name in line:
            parts = line.replace(":", " ").split()
            for part in parts:
                if part.isdigit():
                    return int(part)
    return None


def run_cube(
    cadical: str,
    cnf_lines: list[str],
    header_idx: int,
    n_vars: int,
    n_clauses: int,
    cube: dict[str, Any],
    workdir: Path,
    conflicts: int,
    timeout: int,
) -> dict[str, Any]:
    cube_path = workdir / f"{cube['id'].replace('::', '__')}.cnf"
    write_cube_cnf(cnf_lines, header_idx, n_vars, n_clauses, cube["assumptions"], cube_path)
    cmd = [cadical, "-n", "-c", str(conflicts), "-t", str(timeout), str(cube_path)]
    t0 = time.time()
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    wall = time.time() - t0
    return {
        "id": cube["id"],
        "assumption_count": len(cube["assumptions"]),
        "status": parse_status(proc.stdout, proc.returncode),
        "returncode": proc.returncode,
        "wall_seconds": round(wall, 6),
        "conflicts_metric": parse_metric(proc.stdout, "conflicts"),
        "decisions_metric": parse_metric(proc.stdout, "decisions"),
        "stdout_tail": proc.stdout.splitlines()[-20:],
    }


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    statuses = {row["status"] for row in payload["runs"]}
    if "UNSATISFIABLE" in statuses:
        return (
            "bridge_cube_smoke_found_unsat_cube",
            "Promote UNSAT bridge cubes to proof/log extraction.",
        )
    if "SATISFIABLE" in statuses:
        return (
            "bridge_cube_smoke_found_sat_cube",
            "Inspect SAT bridge cube witnesses for structural relevance.",
        )
    return (
        "bridge_cube_smoke_all_unknown",
        "No cube resolves at the smoke cap; compare conflict/decision signatures before deeper runs.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: BRIDGE_CUBE_SMOKE",
        "---",
        "",
        "# F381: bridge cube smoke tests",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        payload["decision"],
        f"CNF: `{payload['cnf']}`.",
        f"Conflict cap: {payload['conflicts']}; timeout: {payload['timeout_seconds']}s.",
        "",
        "| Cube | Assumptions | Status | rc | Wall |",
        "|---|---:|---|---:|---:|",
    ]
    for row in payload["runs"]:
        lines.append(
            f"| `{row['id']}` | {row['assumption_count']} | `{row['status']}` | "
            f"{row['returncode']} | {row['wall_seconds']} |"
        )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cnf", type=Path, default=DEFAULT_CNF)
    ap.add_argument("--cubes", type=Path, default=DEFAULT_CUBES)
    ap.add_argument("--cadical", default=None)
    ap.add_argument("--conflicts", type=int, default=5000)
    ap.add_argument("--timeout", type=int, default=5)
    ap.add_argument("--workdir", type=Path, default=Path("/tmp/F381_bridge_cubes"))
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    cadical = args.cadical or shutil.which("cadical")
    if not cadical:
        raise SystemExit("cadical not found")
    cubes = parse_cubes(args.cubes)
    header, n_vars, n_clauses, lines = read_cnf(args.cnf)
    header_idx = lines.index(header)
    args.workdir.mkdir(parents=True, exist_ok=True)
    runs = [
        run_cube(
            cadical,
            lines,
            header_idx,
            n_vars,
            n_clauses,
            cube,
            args.workdir,
            args.conflicts,
            args.timeout,
        )
        for cube in cubes
    ]
    payload = {
        "report_id": "F381",
        "cnf": repo_path(args.cnf),
        "cubes": repo_path(args.cubes),
        "cadical": cadical,
        "conflicts": args.conflicts,
        "timeout_seconds": args.timeout,
        "runs": runs,
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
        "statuses": {status: sum(1 for row in runs if row["status"] == status) for status in sorted({row["status"] for row in runs})},
        "runs": [{"id": row["id"], "status": row["status"], "wall": row["wall_seconds"]} for row in runs],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
