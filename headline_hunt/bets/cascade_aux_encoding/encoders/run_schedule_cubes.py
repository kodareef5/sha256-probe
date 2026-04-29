#!/usr/bin/env python3
"""
run_schedule_cubes.py - Execute schedule_cube_planner JSONL cube manifests.

The runner materializes augmented CNFs as needed, invokes a local SAT solver,
and writes one JSON result per cube. It is intentionally modest: it is meant
for quick cube-and-conquer probes on a laptop or small workstation, not for
cluster scheduling.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import time
from pathlib import Path

from schedule_cube_planner import write_augmented_cnf


def solver_command(solver: str, cnf: Path, conflicts: int) -> list[str]:
    if solver == "cadical":
        cmd = ["cadical", "-q"]
        if conflicts > 0:
            cmd.extend(["-c", str(conflicts)])
        cmd.append(str(cnf))
        return cmd
    if solver == "kissat":
        cmd = ["kissat", "-q"]
        if conflicts > 0:
            cmd.append(f"--conflicts={conflicts}")
        cmd.append(str(cnf))
        return cmd
    raise ValueError("solver must be cadical or kissat")


def classify_result(returncode: int, output: str, timed_out: bool) -> str:
    if timed_out:
        return "TIMEOUT"
    if "s SATISFIABLE" in output:
        return "SAT"
    if "s UNSATISFIABLE" in output:
        return "UNSAT"
    if "UNKNOWN" in output:
        return "UNKNOWN"
    if returncode == 10:
        return "SAT"
    if returncode == 20:
        return "UNSAT"
    return "ERROR"


def output_tail(text: str, max_lines: int = 12) -> list[str]:
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    return lines[-max_lines:]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True, type=Path,
                    help="JSONL manifest from schedule_cube_planner.py")
    ap.add_argument("--out-jsonl", required=True, type=Path, help="result JSONL")
    ap.add_argument("--solver", choices=("cadical", "kissat"), default="cadical")
    ap.add_argument("--limit", type=int, default=0,
                    help="maximum cube records to execute; 0 means all")
    ap.add_argument("--conflicts", type=int, default=0,
                    help="solver conflict limit if supported; 0 means none")
    ap.add_argument("--timeout-sec", type=float, default=0.0,
                    help="per-cube wall timeout; 0 means no Python timeout")
    ap.add_argument("--work-dir", type=Path,
                    help="where to materialize cube CNFs; default is a temp dir")
    ap.add_argument("--keep-cnfs", action="store_true",
                    help="keep materialized CNFs when using a temporary work dir")
    args = ap.parse_args()

    if args.work_dir is None and args.keep_cnfs:
        tmp = None
        work_dir = Path(tempfile.mkdtemp(prefix="schedule_cubes_"))
        print(f"keeping temp CNFs in {work_dir}")
    elif args.work_dir is None:
        tmp = tempfile.TemporaryDirectory(prefix="schedule_cubes_")
        work_dir = Path(tmp.name)
    else:
        tmp = None
        work_dir = args.work_dir
        work_dir.mkdir(parents=True, exist_ok=True)

    args.out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    executed = 0
    try:
        with args.manifest.open() as inp, args.out_jsonl.open("w") as out:
            for line in inp:
                if args.limit and executed >= args.limit:
                    break
                if not line.strip():
                    continue
                rec = json.loads(line)
                cnf_path = Path(rec["cnf_path"]) if rec.get("cnf_path") else None
                if cnf_path is None or not cnf_path.exists():
                    base = Path(rec["base_cnf"])
                    cnf_path = work_dir / f"{base.stem}__{rec['cube_id']}.cnf"
                    write_augmented_cnf(base, cnf_path, rec["clauses"], rec["cube_id"])

                cmd = solver_command(args.solver, cnf_path, args.conflicts)
                t0 = time.monotonic()
                timed_out = False
                try:
                    proc = subprocess.run(
                        cmd,
                        text=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        timeout=args.timeout_sec if args.timeout_sec > 0 else None,
                        check=False,
                    )
                    output = proc.stdout
                    rc = proc.returncode
                except subprocess.TimeoutExpired as exc:
                    timed_out = True
                    output = exc.stdout or ""
                    rc = -1
                wall = time.monotonic() - t0

                result = {
                    "cube_id": rec["cube_id"],
                    "target": rec["target"],
                    "sr": rec["sr"],
                    "round": rec["round"],
                    "depth": rec["depth"],
                    "assignments": rec["assignments"],
                    "solver": args.solver,
                    "conflicts": args.conflicts,
                    "timeout_sec": args.timeout_sec,
                    "status": classify_result(rc, output, timed_out),
                    "returncode": rc,
                    "wall_seconds": round(wall, 6),
                    "cnf_path": str(cnf_path),
                    "output_tail": output_tail(output),
                }
                out.write(json.dumps(result, sort_keys=True))
                out.write("\n")
                out.flush()
                executed += 1
                print(
                    f"{executed}: {result['cube_id']} "
                    f"{result['status']} {result['wall_seconds']:.3f}s"
                )
    finally:
        if tmp is not None:
            tmp.cleanup()

    print(f"wrote {executed} cube results to {args.out_jsonl}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
