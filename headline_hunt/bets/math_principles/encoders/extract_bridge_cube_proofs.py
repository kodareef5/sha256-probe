#!/usr/bin/env python3
"""
extract_bridge_cube_proofs.py - Proof metadata for F381 UNSAT bridge cubes.
"""

from __future__ import annotations

import argparse
import json
import re
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
DEFAULT_F381 = REPO / "headline_hunt/bets/math_principles/results/20260429_F381_bridge_cube_smoke.json"
DEFAULT_OUT_JSON = REPO / "headline_hunt/bets/math_principles/results/20260429_F382_bridge_cube_proof_metadata.json"
DEFAULT_PROOF_DIR = REPO / "headline_hunt/bets/math_principles/data/20260429_F382_bridge_cube_proofs"


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def safe_id(cube_id: str) -> str:
    return cube_id.replace("::", "__").replace("/", "_")


def parse_drat_stats(stdout: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for line in stdout.splitlines():
        if "DRAT proof file" in line and "closed" in line:
            out["proof_closed"] = True
        m = re.search(r"DRAT\s+(\d+)\s+added clauses", line)
        if m:
            out["drat_added_clauses"] = int(m.group(1))
        m = re.search(r"DRAT\s+(\d+)\s+deleted clauses", line)
        if m:
            out["drat_deleted_clauses"] = int(m.group(1))
        m = re.search(r"DRAT\s+(\d+)\s+bytes", line)
        if m:
            out["drat_bytes_reported"] = int(m.group(1))
        m = re.search(r"fixed:\s+(\d+)", line)
        if m:
            out["fixed_vars"] = int(m.group(1))
        m = re.search(r"propagations:\s+(\d+)", line)
        if m:
            out["propagations"] = int(m.group(1))
    return out


def status(stdout: str, returncode: int) -> str:
    if "s UNSATISFIABLE" in stdout or returncode == 20:
        return "UNSATISFIABLE"
    if "s SATISFIABLE" in stdout or returncode == 10:
        return "SATISFIABLE"
    return "UNKNOWN"


def run_proof(
    cadical: str,
    cnf_lines: list[str],
    header_idx: int,
    n_vars: int,
    n_clauses: int,
    cube: dict[str, Any],
    workdir: Path,
    proof_dir: Path,
) -> dict[str, Any]:
    sid = safe_id(cube["id"])
    cube_path = workdir / f"{sid}.cnf"
    proof_path = proof_dir / f"{sid}.drat"
    write_cube_cnf(cnf_lines, header_idx, n_vars, n_clauses, cube["assumptions"], cube_path)
    t0 = time.time()
    proc = subprocess.run(
        [cadical, "-n", str(cube_path), str(proof_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    wall = time.time() - t0
    stats = parse_drat_stats(proc.stdout)
    return {
        "id": cube["id"],
        "assumption_count": len(cube["assumptions"]),
        "status": status(proc.stdout, proc.returncode),
        "returncode": proc.returncode,
        "wall_seconds": round(wall, 6),
        "proof": repo_path(proof_path),
        "proof_bytes": proof_path.stat().st_size if proof_path.exists() else 0,
        "stats": stats,
        "stdout_tail": proc.stdout.splitlines()[-30:],
    }


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    if all(row["status"] == "UNSATISFIABLE" for row in payload["proof_runs"]):
        return (
            "bridge_cube_proofs_extracted",
            "Use proof metadata to rank bridge cubes for conflict-clause inspection.",
        )
    return (
        "bridge_cube_proof_extraction_partial",
        "Some selected cubes did not reproduce UNSAT during proof extraction.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: BRIDGE_CUBE_PROOF_METADATA",
        "---",
        "",
        "# F382: bridge cube proof metadata",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        payload["decision"],
        "",
        "| Cube | Assumptions | Status | Wall | DRAT bytes | Added | Deleted | Fixed | Propagations |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in payload["proof_runs"]:
        stats = row["stats"]
        lines.append(
            f"| `{row['id']}` | {row['assumption_count']} | `{row['status']}` | "
            f"{row['wall_seconds']} | {row['proof_bytes']} | "
            f"{stats.get('drat_added_clauses', '')} | {stats.get('drat_deleted_clauses', '')} | "
            f"{stats.get('fixed_vars', '')} | {stats.get('propagations', '')} |"
        )
    lines.extend([
        "",
        "## Decision",
        "",
        "The fastest/smallest proof cubes are the best first targets for learned-clause inspection. "
        "The `w57_w60` full assignment cubes produce tiny proofs, suggesting the contradiction is mostly structural/UP-level rather than deep CDCL search.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--f381", type=Path, default=DEFAULT_F381)
    ap.add_argument("--cnf", type=Path, default=DEFAULT_CNF)
    ap.add_argument("--cubes", type=Path, default=DEFAULT_CUBES)
    ap.add_argument("--cadical", default=None)
    ap.add_argument("--workdir", type=Path, default=Path("/tmp/F382_bridge_cube_proofs"))
    ap.add_argument("--proof-dir", type=Path, default=DEFAULT_PROOF_DIR)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    cadical = args.cadical or shutil.which("cadical")
    if not cadical:
        raise SystemExit("cadical not found")
    f381 = read_json(args.f381)
    unsat_ids = {row["id"] for row in f381["runs"] if row["status"] == "UNSATISFIABLE"}
    cubes = [cube for cube in parse_cubes(args.cubes) if cube["id"] in unsat_ids]
    header, n_vars, n_clauses, lines = read_cnf(args.cnf)
    header_idx = lines.index(header)
    args.workdir.mkdir(parents=True, exist_ok=True)
    args.proof_dir.mkdir(parents=True, exist_ok=True)
    proof_runs = [
        run_proof(cadical, lines, header_idx, n_vars, n_clauses, cube, args.workdir, args.proof_dir)
        for cube in cubes
    ]
    payload = {
        "report_id": "F382",
        "f381": repo_path(args.f381),
        "cnf": repo_path(args.cnf),
        "cubes": repo_path(args.cubes),
        "cadical": cadical,
        "proof_dir": repo_path(args.proof_dir),
        "proof_runs": proof_runs,
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
        "proofs": [
            {
                "id": row["id"],
                "status": row["status"],
                "proof_bytes": row["proof_bytes"],
                "stats": row["stats"],
            }
            for row in proof_runs
        ],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
