#!/usr/bin/env python3
"""
run_decision_priority_matrix.py - Compile/run the F398 cb_decide matrix.

Default mode is a dry run that writes the exact command matrix and missing
input inventory.  Use --run on a machine with CaDiCaL C++ headers/libcadical.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[4]
DEFAULT_SPEC = (
    REPO / "headline_hunt/bets/programmatic_sat_propagator/results/preflight_2026-04-29/F397_decision_priority_specs.json"
)
DEFAULT_SOURCE = REPO / "headline_hunt/bets/programmatic_sat_propagator/propagators/cascade_propagator.cc"
DEFAULT_OUT_JSON = (
    REPO / "headline_hunt/bets/programmatic_sat_propagator/results/preflight_2026-04-29/F399_decision_priority_matrix_plan.json"
)
LOCAL_CADICAL_SRC = REPO / ".deps/cadical/src"
LOCAL_CADICAL_LIB = REPO / ".deps/cadical/build/libcadical.a"
LOCAL_NLOHMANN_INCLUDE = REPO / ".deps/nlohmann/include"


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


def find_varmap(cnf: Path) -> Path | None:
    candidates = [
        Path(str(cnf) + ".varmap.json"),
        cnf.with_suffix(cnf.suffix + ".varmap.json"),
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def compile_command(source: Path, binary: Path) -> list[str]:
    include_dirs = []
    if (LOCAL_CADICAL_SRC / "cadical.hpp").exists():
        include_dirs.append(LOCAL_CADICAL_SRC)
    if (LOCAL_NLOHMANN_INCLUDE / "nlohmann/json.hpp").exists():
        include_dirs.append(LOCAL_NLOHMANN_INCLUDE)
    include_dirs.extend([
        Path("/opt/homebrew/include"),
        Path("/usr/local/include"),
    ])

    cmd = [
        "g++",
        "-std=c++17",
        "-O2",
        *[f"-I{path}" for path in include_dirs],
        str(source),
    ]
    if LOCAL_CADICAL_LIB.exists():
        cmd.append(str(LOCAL_CADICAL_LIB))
    else:
        cmd.extend([
            "-L/opt/homebrew/lib",
            "-L/usr/local/lib",
            "-lcadical",
        ])
    cmd.extend([
        "-o",
        str(binary),
    ])
    return cmd


def run_command(cmd: list[str], timeout: int | None = None) -> dict[str, Any]:
    t0 = time.time()
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "wall_seconds": round(time.time() - t0, 3),
        "stdout_tail": proc.stdout.splitlines()[-40:],
        "stderr_tail": proc.stderr.splitlines()[-80:],
        "metrics": parse_metrics(proc.stdout + "\n" + proc.stderr),
    }


def parse_metrics(text: str) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    patterns = {
        "result": r"Result:\s+([0-9]+)",
        "cb_decide_suggestions": r"cb_decide suggestions:\s+([0-9]+)",
        "cb_propagate_fires": r"cb_propagate fires:\s+([0-9]+)",
        "decisions": r"decisions:\s+([0-9]+)",
        "backtracks": r"backtracks:\s+([0-9]+)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if match:
            value = match.group(1)
            metrics[key] = int(value) if value.isdigit() else value
    return metrics


def matrix_commands(
    binary: Path,
    spec_path: Path,
    candidate: str,
    cnf: Path,
    varmap: Path,
    conflicts: int,
    priority_max_suggestions: int | None,
    priority_stride: int | None,
) -> list[dict[str, Any]]:
    base = [str(binary), str(cnf), str(varmap), f"--conflicts={conflicts}"]
    priority_extra = []
    priority_suffix = ""
    if priority_max_suggestions is not None:
        priority_extra.append(f"--priority-max-suggestions={priority_max_suggestions}")
        priority_suffix += f"_max{priority_max_suggestions}"
    if priority_stride is not None:
        priority_extra.append(f"--priority-stride={priority_stride}")
        priority_suffix += f"_stride{priority_stride}"
    return [
        {"arm": "baseline_no_propagator", "cmd": [*base, "--no-propagator"]},
        {"arm": "existing_propagator", "cmd": base},
        {
            "arm": f"priority_f286_132{priority_suffix}",
            "cmd": [
                *base,
                f"--priority-spec={spec_path}",
                "--priority-set=f286_132_conservative",
                f"--priority-candidate={candidate}",
                *priority_extra,
            ],
        },
        {
            "arm": f"priority_f332_139{priority_suffix}",
            "cmd": [
                *base,
                f"--priority-spec={spec_path}",
                "--priority-set=f332_139_stable6",
                f"--priority-candidate={candidate}",
                *priority_extra,
            ],
        },
    ]


def build_plan(args: argparse.Namespace) -> dict[str, Any]:
    spec = load_json(args.priority_spec)
    requested = set(args.candidates.split(",")) if args.candidates else None
    binary = args.binary or Path("/tmp/F399_cascade_propagator")
    compile_cmd = compile_command(args.source, binary)
    runnable = []
    missing = []
    for item in spec["candidate_specs"]:
        candidate = item["candidate"]
        if requested and candidate not in requested and item.get("name") not in requested:
            continue
        cnf = REPO / item["cnf"]
        varmap = find_varmap(cnf)
        row = {
            "candidate": candidate,
            "cnf": rel(cnf),
            "varmap": rel(varmap) if varmap else None,
        }
        if not cnf.exists() or varmap is None:
            missing.append({
                **row,
                "missing_cnf": not cnf.exists(),
                "missing_varmap": varmap is None,
            })
            continue
        row["commands"] = matrix_commands(
            binary,
            args.priority_spec,
            candidate,
            cnf,
            varmap,
            args.conflicts,
            args.priority_max_suggestions,
            args.priority_stride,
        )
        runnable.append(row)
    return {
        "report_id": args.report_id,
        "mode": "run" if args.run else "dry_run",
        "priority_spec": rel(args.priority_spec),
        "source": rel(args.source),
        "binary": str(binary),
        "conflicts": args.conflicts,
        "priority_max_suggestions": args.priority_max_suggestions,
        "priority_stride": args.priority_stride,
        "compile_command": compile_cmd,
        "runnable_candidates": runnable,
        "missing_inputs": missing,
    }


def execute_plan(plan: dict[str, Any], timeout: int) -> dict[str, Any]:
    compile_result = run_command(plan["compile_command"], timeout=timeout)
    plan["compile_result"] = compile_result
    if compile_result["returncode"] != 0:
        plan["verdict"] = "compile_failed"
        return plan
    runs = []
    for candidate in plan["runnable_candidates"]:
        for arm in candidate["commands"]:
            result = run_command(arm["cmd"], timeout=timeout)
            runs.append({
                "candidate": candidate["candidate"],
                "arm": arm["arm"],
                **result,
            })
    plan["runs"] = runs
    plan["verdict"] = "matrix_completed"
    return plan


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")


def write_md(path: Path, payload: dict[str, Any]) -> None:
    report_id = payload.get("report_id", "F399")
    status = "DECISION_PRIORITY_MATRIX_RUN" if payload["mode"] == "run" else "DECISION_PRIORITY_MATRIX_PLAN"
    lines = [
        "---",
        "date: 2026-04-30",
        "bet: programmatic_sat_propagator",
        f"status: {status}",
        "---",
        "",
        f"# {report_id}: decision-priority matrix",
        "",
        "## Summary",
        "",
        f"Mode: `{payload['mode']}`.",
        f"Verdict: `{payload.get('verdict', 'not_run')}`.",
        f"Priority spec: `{payload['priority_spec']}`.",
        f"Conflict cap: {payload['conflicts']}.",
        f"Priority max suggestions: `{payload.get('priority_max_suggestions')}`.",
        f"Priority stride: `{payload.get('priority_stride')}`.",
        f"Runnable candidates here: {len(payload['runnable_candidates'])}.",
        f"Missing-input candidates here: {len(payload['missing_inputs'])}.",
        "",
        "## Compile Command",
        "",
        "```bash",
        " ".join(payload["compile_command"]),
        "```",
        "",
        "## Runnable Candidates",
        "",
        "| Candidate | VarMap | Arms |",
        "|---|---|---:|",
    ]
    for row in payload["runnable_candidates"]:
        lines.append(f"| `{row['candidate']}` | `{row['varmap']}` | {len(row['commands'])} |")
    lines.extend([
        "",
        "## Missing Inputs",
        "",
        "| Candidate | Missing CNF | Missing VarMap |",
        "|---|:---:|:---:|",
    ])
    for row in payload["missing_inputs"]:
        lines.append(
            f"| `{row['candidate']}` | {row['missing_cnf']} | {row['missing_varmap']} |"
        )
    if "compile_result" in payload:
        compile_result = payload["compile_result"]
        lines.extend([
            "",
            "## Compile Result",
            "",
            f"Return code: `{compile_result['returncode']}`.",
            f"Wall seconds: `{compile_result['wall_seconds']}`.",
        ])
    if payload.get("runs"):
        lines.extend([
            "",
            "## Run Results",
            "",
            "| Candidate | Arm | Result | Return Code | Wall s | Decisions | Backtracks | cb_decide | cb_propagate |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ])
        for row in payload["runs"]:
            metrics = row.get("metrics", {})
            lines.append(
                f"| `{row['candidate']}` | `{row['arm']}` | "
                f"{metrics.get('result', '')} | {row['returncode']} | {row['wall_seconds']} | "
                f"{metrics.get('decisions', '')} | {metrics.get('backtracks', '')} | "
                f"{metrics.get('cb_decide_suggestions', '')} | {metrics.get('cb_propagate_fires', '')} |"
            )
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--priority-spec", type=Path, default=DEFAULT_SPEC)
    ap.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    ap.add_argument("--binary", type=Path, default=None)
    ap.add_argument("--conflicts", type=int, default=50000)
    ap.add_argument("--candidates", default=None,
                    help="comma-separated candidate keys or F332 short names")
    ap.add_argument("--run", action="store_true",
                    help="compile and run instead of writing a dry-run plan")
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--priority-max-suggestions", type=int, default=None)
    ap.add_argument("--priority-stride", type=int, default=None)
    ap.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    ap.add_argument("--out-md", type=Path, default=None)
    ap.add_argument("--report-id", default="F399")
    args = ap.parse_args()

    plan = build_plan(args)
    payload = execute_plan(plan, args.timeout) if args.run else plan
    write_json(args.out_json, payload)
    write_md(args.out_md or args.out_json.with_suffix(".md"), payload)
    print(json.dumps({
        "mode": payload["mode"],
        "runnable_candidates": len(payload["runnable_candidates"]),
        "missing_inputs": len(payload["missing_inputs"]),
        "out_json": rel(args.out_json),
    }, indent=2, sort_keys=True))
    return 0 if payload.get("verdict") != "compile_failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
