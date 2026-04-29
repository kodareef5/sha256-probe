#!/usr/bin/env python3
"""
analyze_w57_core_pair.py - Cross-check the F383 two-bit W57 core.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from smoke_bridge_cubes import DEFAULT_CNF, read_cnf, repo_path, write_cube_cnf  # noqa: E402


REPO = Path(__file__).resolve().parents[4]
DEFAULT_F380 = REPO / "headline_hunt/bets/math_principles/results/20260429_F380_bridge_cubes.json"
DEFAULT_VARMAP = REPO / "headline_hunt/bets/math_principles/data/20260429_F380_aux_force_sr60_n32_bit31_m17149975_fillffffffff.varmap.json"
DEFAULT_OUT_JSON = REPO / "headline_hunt/bets/math_principles/results/20260429_F384_w57_core_pair_analysis.json"


def read_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def w_lit(varmap: dict[str, Any], round_: int, bit: int) -> int:
    return int(varmap["aux_W"][str(round_)][bit])


def run_assumptions(
    cadical: str,
    lines: list[str],
    header_idx: int,
    n_vars: int,
    n_clauses: int,
    assumptions: list[int],
    path: Path,
    timeout: int,
) -> dict[str, Any]:
    write_cube_cnf(lines, header_idx, n_vars, n_clauses, assumptions, path)
    t0 = time.time()
    proc = subprocess.run(
        [cadical, "-q", "-n", "-t", str(timeout), str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    wall = time.time() - t0
    if proc.returncode == 20:
        status = "UNSATISFIABLE"
    elif proc.returncode == 10:
        status = "SATISFIABLE"
    else:
        status = "UNKNOWN"
    return {
        "assumptions": assumptions,
        "status": status,
        "returncode": proc.returncode,
        "wall_seconds": round(wall, 6),
    }


def target_pair_values(f380: dict[str, Any], round_: int, bits: tuple[int, int]) -> list[dict[str, Any]]:
    out = []
    for cube in f380["cubes"]:
        if cube["subset"] != "w57_w60":
            continue
        values = cube["coordinate_bits"][str(round_)]
        out.append({
            "target": cube["target"],
            "candidate": cube["candidate"],
            "values": {str(bit): values[bit] for bit in bits},
        })
    return out


def verdict(payload: dict[str, Any]) -> tuple[str, str]:
    unsat = [row for row in payload["polarity_tests"] if row["status"] == "UNSATISFIABLE"]
    if len(unsat) == 1:
        return (
            "w57_pair_has_single_forbidden_polarity",
            "Treat the forbidden W57 pair as a sound two-bit bridge constraint candidate.",
        )
    if unsat:
        return (
            "w57_pair_has_multiple_forbidden_polarities",
            "The W57 pair is heavily constrained; inspect before using as a bridge-specific signal.",
        )
    return (
        "w57_pair_not_forbidden_at_smoke_cap",
        "The F383 core did not reproduce under direct polarity testing.",
    )


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: W57_CORE_PAIR_ANALYSIS",
        "---",
        "",
        "# F384: W57 core-pair analysis",
        "",
        "## Summary",
        "",
        f"Verdict: `{payload['verdict']}`.",
        payload["decision"],
        f"Pair: dW{payload['round']}[{payload['bits'][0]}], dW{payload['round']}[{payload['bits'][1]}].",
        "",
        "## Polarity Tests",
        "",
        "| dW57[22] | dW57[23] | Literals | Status | Wall |",
        "|---:|---:|---|---|---:|",
    ]
    for row in payload["polarity_tests"]:
        lines.append(
            f"| {row['values']['22']} | {row['values']['23']} | `{row['assumptions']}` | "
            f"`{row['status']}` | {row['wall_seconds']} |"
        )
    lines.extend([
        "",
        "## Target Values",
        "",
        "| Target | dW57[22] | dW57[23] | Candidate |",
        "|---|---:|---:|---|",
    ])
    for row in payload["target_values"]:
        cand = row["candidate"]
        lines.append(
            f"| `{row['target']}` | {row['values']['22']} | {row['values']['23']} | "
            f"a57={cand['a57']} D61={cand['D61']} chart=`{cand['chart']}` |"
        )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cnf", type=Path, default=DEFAULT_CNF)
    ap.add_argument("--f380", type=Path, default=DEFAULT_F380)
    ap.add_argument("--varmap", type=Path, default=DEFAULT_VARMAP)
    ap.add_argument("--round", type=int, default=57)
    ap.add_argument("--bits", default="22,23")
    ap.add_argument("--cadical", default=None)
    ap.add_argument("--timeout", type=int, default=2)
    ap.add_argument("--workdir", type=Path, default=Path("/tmp/F384_w57_pair"))
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    args = ap.parse_args()

    bits = tuple(int(part) for part in args.bits.split(","))
    if len(bits) != 2:
        raise SystemExit("--bits must name exactly two bits")
    cadical = args.cadical or shutil.which("cadical")
    if not cadical:
        raise SystemExit("cadical not found")
    varmap = read_json(args.varmap)
    f380 = read_json(args.f380)
    header, n_vars, n_clauses, lines = read_cnf(args.cnf)
    header_idx = lines.index(header)
    args.workdir.mkdir(parents=True, exist_ok=True)
    lit0 = w_lit(varmap, args.round, bits[0])
    lit1 = w_lit(varmap, args.round, bits[1])
    tests = []
    for v0 in (0, 1):
        for v1 in (0, 1):
            assumptions = [lit0 if v0 else -lit0, lit1 if v1 else -lit1]
            row = run_assumptions(
                cadical,
                lines,
                header_idx,
                n_vars,
                n_clauses,
                assumptions,
                args.workdir / f"w{args.round}_{bits[0]}{v0}_{bits[1]}{v1}.cnf",
                args.timeout,
            )
            row["values"] = {str(bits[0]): v0, str(bits[1]): v1}
            tests.append(row)
    payload = {
        "report_id": "F384",
        "cnf": repo_path(args.cnf),
        "f380": repo_path(args.f380),
        "varmap": repo_path(args.varmap),
        "round": args.round,
        "bits": list(bits),
        "literals": {str(bits[0]): lit0, str(bits[1]): lit1},
        "polarity_tests": tests,
        "target_values": target_pair_values(f380, args.round, bits),
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
        "tests": [{"values": row["values"], "status": row["status"]} for row in tests],
        "target_values": payload["target_values"],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
