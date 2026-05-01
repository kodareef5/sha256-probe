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
HOTSPOT_PRIORITY_SET = "actual_p1_a57_hotspots"
HOTSPOT_SPEC = (
    REPO / "headline_hunt/bets/programmatic_sat_propagator/results/preflight_2026-04-29/F421_actual_a57_hotspot_priority_specs.json"
)
HOTSPOT_CONFIG = {
    "bit2_ma896ee41_fillffffffff": {
        "name": "bit2",
        "bit": 2,
        "m0": "0xa896ee41",
        "fill": "0xffffffff",
        "cnf": "headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit2_ma896ee41_fillffffffff.cnf",
        "hotspot_bits": [3, 7, 8],
        "f343_clauses": [[12401], [12423, 12424]],
    },
    "bit24_mdc27e18c_fillffffffff": {
        "name": "bit24",
        "bit": 24,
        "m0": "0xdc27e18c",
        "fill": "0xffffffff",
        "cnf": "headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit24_mdc27e18c_fillffffffff.cnf",
        "hotspot_bits": [14, 16, 21, 22, 23, 24, 25],
        "f343_clauses": [[12364], [12386, -12387]],
    },
    "bit28_md1acca79_fillffffffff": {
        "name": "bit28",
        "bit": 28,
        "m0": "0xd1acca79",
        "fill": "0xffffffff",
        "cnf": "headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit28_md1acca79_fillffffffff.cnf",
        "hotspot_bits": [2, 5, 6],
        "f343_clauses": [[-12352], [12374, 12375]],
    },
}
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


def run_command_logged(
    cmd: list[str],
    stdout_log: Path,
    stderr_log: Path,
    timeout: int | None = None,
) -> dict[str, Any]:
    t0 = time.time()
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
    )
    wall = round(time.time() - t0, 6)
    stdout_log.parent.mkdir(parents=True, exist_ok=True)
    stdout_log.write_text(proc.stdout)
    stderr_log.write_text(proc.stderr)
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "wall_seconds": wall,
        "stdout_log": str(stdout_log),
        "stderr_log": str(stderr_log),
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


def audit_cnf(path: Path) -> dict[str, Any]:
    proc = subprocess.run(
        ["python3", str(REPO / "headline_hunt/infra/audit_cnf.py"), str(path)],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    verdict = None
    for line in proc.stdout.splitlines():
        match = re.search(r"VERDICT:\s+([A-Z_]+)", line)
        if match:
            verdict = match.group(1)
            break
    result = {
        "returncode": proc.returncode,
        "verdict": verdict,
        "stdout_tail": proc.stdout.splitlines()[-20:],
        "stderr_tail": proc.stderr.splitlines()[-20:],
    }
    if proc.returncode != 0 or verdict != "CONFIRMED":
        raise RuntimeError(f"audit failed for {path}: {result}")
    return result


def inject_cnf(base: Path, out: Path, clauses: list[list[int]]) -> None:
    lines = base.read_text().splitlines()
    for idx, line in enumerate(lines):
        if not line.startswith("p cnf "):
            continue
        parts = line.split()
        if len(parts) != 4:
            raise ValueError(f"bad DIMACS header in {base}: {line}")
        lines[idx] = f"p cnf {int(parts[2])} {int(parts[3]) + len(clauses)}"
        break
    else:
        raise ValueError(f"missing DIMACS header in {base}")

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        for line in lines:
            f.write(line)
            f.write("\n")
        f.write("c F421 injected F343 clauses\n")
        for clause in clauses:
            f.write(" ".join(str(lit) for lit in clause))
            f.write(" 0\n")


def ensure_hotspot_input(candidate: str, workdir: Path) -> tuple[Path, Path, dict[str, Any] | None]:
    spec = HOTSPOT_CONFIG[candidate]
    cnf = REPO / spec["cnf"]
    varmap = find_varmap(cnf)
    if cnf.exists() and varmap is not None:
        return cnf, varmap, None

    out_cnf = workdir / Path(spec["cnf"]).name
    workdir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "python3",
        str(REPO / "headline_hunt/bets/cascade_aux_encoding/encoders/cascade_aux_encoder.py"),
        "--sr", "60",
        "--m0", spec["m0"],
        "--fill", spec["fill"],
        "--kernel-bit", str(spec["bit"]),
        "--mode", "force",
        "--out", str(out_cnf),
        "--varmap", "+",
        "--quiet",
    ]
    proc = subprocess.run(
        cmd,
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"failed to regenerate {candidate}: {proc.stderr}")
    out_varmap = find_varmap(out_cnf)
    if not out_cnf.exists() or out_varmap is None:
        raise RuntimeError(f"regeneration did not create CNF+varmap for {candidate}")
    return out_cnf, out_varmap, {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout.splitlines()[-20:],
        "stderr_tail": proc.stderr.splitlines()[-20:],
    }


def check_f343_vars(varmap: Path, clauses: list[list[int]]) -> None:
    data = load_json(varmap)
    d_w57 = data["aux_W"]["57"]
    expected = {abs(clauses[0][0]), abs(clauses[1][0]), abs(clauses[1][1])}
    actual = {abs(int(d_w57[0])), abs(int(d_w57[22])), abs(int(d_w57[23]))}
    if expected != actual:
        raise RuntimeError(f"F343 vars do not match {varmap}: expected {expected}, actual {actual}")


def build_hotspot_priority_spec(candidates: list[str], workdir: Path, out_path: Path) -> dict[str, Any]:
    rows = []
    for candidate in candidates:
        cfg = HOTSPOT_CONFIG[candidate]
        cnf, varmap, generated = ensure_hotspot_input(candidate, workdir)
        data = load_json(varmap)
        a57 = data["actual_p1"]["a_57"]
        entries = []
        vars_seen = []
        for rank, bit in enumerate(cfg["hotspot_bits"]):
            lit = int(a57[bit])
            var = abs(lit)
            if var <= 1:
                raise RuntimeError(f"{candidate} actual_p1_a_57_b{bit} is constant in {varmap}")
            entries.append({
                "rank": rank,
                "category": "actual_p1_a_57",
                "key": f"actual_p1_a_57_b{bit}",
                "round": 57,
                "bit": bit,
                "literal": lit,
                "var": var,
            })
            vars_seen.append(var)
        rows.append({
            "candidate": candidate,
            "name": cfg["name"],
            "cnf": rel(cnf),
            "varmap": rel(varmap),
            "generated_input": generated,
            "priority_sets": {
                HOTSPOT_PRIORITY_SET: {
                    "vars": vars_seen,
                    "entries": entries,
                    "missing": [],
                    "requested_count": len(cfg["hotspot_bits"]),
                    "var_count": len(vars_seen),
                    "by_category": {"actual_p1_a_57": len(vars_seen)},
                }
            },
        })
    payload = {
        "report_id": "F421",
        "parents": ["F397", "F399", "F407", "F416", "F420"],
        "priority_set": HOTSPOT_PRIORITY_SET,
        "candidate_specs": rows,
    }
    write_json(out_path, payload)
    return payload


def append_registry_run(
    candidate: str,
    cnf: Path,
    seed: int,
    arm: str,
    wall: float,
    stderr_log: Path,
    status: str,
) -> dict[str, Any]:
    proc = subprocess.run(
        [
            "python3",
            str(REPO / "headline_hunt/infra/append_run.py"),
            "--bet", "programmatic_sat_propagator",
            "--candidate", f"cand_n32_{candidate}",
            "--cnf", str(cnf),
            "--solver", "cadical-ipasir-up",
            "--solver-version", "3.0.0",
            "--seed", str(seed),
            "--status", status,
            "--wall", f"{wall:.6f}",
            "--encoder", f"cascade_aux_v1_modeA_sr60_force_F421_{arm}",
            "--log", str(stderr_log),
            "--notes", f"F421 actual_p1_a57 hotspot priority matrix {arm} for {candidate}",
        ],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"append_run failed for {candidate}/{arm}/seed{seed}: {proc.stderr}\n{proc.stdout}")
    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def solver_status(metrics: dict[str, Any], returncode: int) -> str:
    result = metrics.get("result")
    if result == 10:
        return "SAT"
    if result == 20:
        return "UNSAT"
    if result == 0 or returncode == 2:
        return "TIMEOUT"
    return "ERROR"


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


def hotspot_matrix_commands(
    binary: Path,
    spec_path: Path,
    candidate: str,
    cnf: Path,
    varmap: Path,
    f343_cnf: Path,
    conflicts: int,
    seed: int,
    priority_max_suggestions: int,
) -> list[dict[str, Any]]:
    base = [str(binary), str(cnf), str(varmap), f"--conflicts={conflicts}", f"--seed={seed}"]
    f343_base = [str(binary), str(f343_cnf), str(varmap), f"--conflicts={conflicts}", f"--seed={seed}"]
    return [
        {"arm": "baseline", "cnf": str(cnf), "cmd": base},
        {"arm": "f343", "cnf": str(f343_cnf), "cmd": f343_base},
        {
            "arm": f"hotspot_priority_max{priority_max_suggestions}",
            "cnf": str(cnf),
            "cmd": [
                *base,
                f"--priority-spec={spec_path}",
                f"--priority-set={HOTSPOT_PRIORITY_SET}",
                f"--priority-candidate={candidate}",
                f"--priority-max-suggestions={priority_max_suggestions}",
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


def parse_seeds(raw: str) -> list[int]:
    seeds = [int(part) for part in raw.split(",") if part.strip()]
    if not seeds:
        raise ValueError("--seeds must contain at least one integer")
    return seeds


def build_hotspot_plan(args: argparse.Namespace) -> dict[str, Any]:
    requested = args.candidates.split(",") if args.candidates else list(HOTSPOT_CONFIG)
    unknown = [cand for cand in requested if cand not in HOTSPOT_CONFIG]
    if unknown:
        raise ValueError(f"unknown hotspot candidates: {unknown}")
    seeds = parse_seeds(args.seeds)
    binary = args.binary or Path("/tmp/F421_cascade_propagator")
    priority_max = 132 if args.priority_max_suggestions is None else args.priority_max_suggestions
    spec_payload = build_hotspot_priority_spec(requested, args.workdir, args.hotspot_spec_out)
    compile_cmd = compile_command(args.source, binary)
    runnable = []
    for item in spec_payload["candidate_specs"]:
        candidate = item["candidate"]
        cfg = HOTSPOT_CONFIG[candidate]
        cnf = REPO / item["cnf"] if not Path(item["cnf"]).is_absolute() else Path(item["cnf"])
        varmap = REPO / item["varmap"] if not Path(item["varmap"]).is_absolute() else Path(item["varmap"])
        check_f343_vars(varmap, cfg["f343_clauses"])
        f343_cnf = args.workdir / f"{cnf.stem}_F421_F343.cnf"
        inject_cnf(cnf, f343_cnf, cfg["f343_clauses"])
        commands = []
        for seed in seeds:
            commands.extend(hotspot_matrix_commands(
                binary,
                args.hotspot_spec_out,
                candidate,
                cnf,
                varmap,
                f343_cnf,
                args.conflicts,
                seed,
                priority_max,
            ))
        runnable.append({
            "candidate": candidate,
            "cnf": rel(cnf),
            "varmap": rel(varmap),
            "f343_cnf": rel(f343_cnf),
            "hotspot_bits": cfg["hotspot_bits"],
            "commands": commands,
        })
    return {
        "report_id": args.report_id,
        "mode": "run" if args.run else "dry_run",
        "matrix_kind": "actual_p1_a57_hotspot_priority",
        "priority_spec": rel(args.hotspot_spec_out),
        "priority_set": HOTSPOT_PRIORITY_SET,
        "source": rel(args.source),
        "binary": str(binary),
        "conflicts": args.conflicts,
        "seeds": seeds,
        "priority_max_suggestions": priority_max,
        "priority_stride": args.priority_stride,
        "compile_command": compile_cmd,
        "runnable_candidates": runnable,
        "missing_inputs": [],
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


def execute_hotspot_plan(plan: dict[str, Any], timeout: int, append_runs: bool, workdir: Path) -> dict[str, Any]:
    compile_result = run_command(plan["compile_command"], timeout=timeout)
    plan["compile_result"] = compile_result
    if compile_result["returncode"] != 0:
        plan["verdict"] = "compile_failed"
        return plan
    runs = []
    for candidate in plan["runnable_candidates"]:
        candidate_key = candidate["candidate"]
        for arm in candidate["commands"]:
            seed_match = re.search(r"--seed=([0-9]+)", " ".join(arm["cmd"]))
            seed = int(seed_match.group(1)) if seed_match else 0
            arm_name = arm["arm"]
            cnf_path = Path(arm["cnf"])
            audit = audit_cnf(cnf_path)
            log_prefix = workdir / f"{candidate_key}_{arm_name}_seed{seed}"
            result = run_command_logged(
                arm["cmd"],
                log_prefix.with_suffix(".stdout.log"),
                log_prefix.with_suffix(".stderr.log"),
                timeout=timeout,
            )
            status = solver_status(result["metrics"], result["returncode"])
            row = {
                "candidate": candidate_key,
                "arm": arm_name,
                "seed": seed,
                "cnf": rel(cnf_path),
                "audit": audit,
                "status": status,
                **result,
            }
            if append_runs:
                row["append_run"] = append_registry_run(
                    candidate_key,
                    cnf_path,
                    seed,
                    arm_name,
                    result["wall_seconds"],
                    Path(result["stderr_log"]),
                    status,
                )
            runs.append(row)
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
        f"date: {time.strftime('%Y-%m-%d')}",
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
    ap.add_argument("--hotspot-matrix", action="store_true",
                    help="run the F421 actual_p1_a57 hotspot priority matrix")
    ap.add_argument("--hotspot-spec-out", type=Path, default=HOTSPOT_SPEC)
    ap.add_argument("--workdir", type=Path, default=Path("/tmp/F421_hotspot_priority"))
    ap.add_argument("--seeds", default="0,1,2",
                    help="comma-separated solver seeds for --hotspot-matrix")
    ap.add_argument("--append-runs", action="store_true",
                    help="append audited run rows to headline_hunt/registry/runs.jsonl")
    args = ap.parse_args()

    if args.hotspot_matrix:
        plan = build_hotspot_plan(args)
        payload = execute_hotspot_plan(plan, args.timeout, args.append_runs, args.workdir) if args.run else plan
    else:
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
