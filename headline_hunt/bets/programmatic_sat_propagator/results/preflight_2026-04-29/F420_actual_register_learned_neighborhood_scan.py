#!/usr/bin/env python3
"""F420 cross-candidate actual-register learned-neighborhood scan.

This is a narrow reproduction runner for the F419 watch surface:
actual p1/p2 a/e registers for rounds 57..63 plus aux_modular_diff targets.
It audits every CNF before launching the CaDiCaL IPASIR-UP binary.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import time
from pathlib import Path


REPO = Path(__file__).resolve().parents[5]
CNF_DIR = REPO / "headline_hunt/bets/cascade_aux_encoding/cnfs"
RESULT_DIR = REPO / "headline_hunt/bets/programmatic_sat_propagator/results/preflight_2026-04-29"

CANDIDATES = {
    "bit2_ma896ee41_fillffffffff": {
        "cnf": CNF_DIR / "aux_force_sr60_n32_bit2_ma896ee41_fillffffffff.cnf",
        "bit": 2,
        "m0": "0xa896ee41",
        "fill": "0xffffffff",
        "f343": [[12401], [12423, 12424]],
    },
    "bit24_mdc27e18c_fillffffffff": {
        "cnf": CNF_DIR / "aux_force_sr60_n32_bit24_mdc27e18c_fillffffffff.cnf",
        "bit": 24,
        "m0": "0xdc27e18c",
        "fill": "0xffffffff",
        "f343": [[12364], [12386, -12387]],
    },
    "bit28_md1acca79_fillffffffff": {
        "cnf": CNF_DIR / "aux_force_sr60_n32_bit28_md1acca79_fillffffffff.cnf",
        "bit": 28,
        "m0": "0xd1acca79",
        "fill": "0xffffffff",
        "f343": [[-12352], [12374, 12375]],
    },
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def audit_cnf(path: Path) -> dict:
    proc = subprocess.run(
        ["python3", str(REPO / "headline_hunt/infra/audit_cnf.py"), str(path)],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    verdict = None
    for line in proc.stdout.splitlines():
        match = re.search(r"VERDICT:\s+([A-Z_]+)", line)
        if match:
            verdict = match.group(1)
            break
    out = {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "verdict": verdict,
    }
    if proc.returncode != 0 or verdict != "CONFIRMED":
        raise RuntimeError(f"audit failed for {path}: {out}")
    return out


def inject_cnf(base: Path, out: Path, clauses: list[list[int]]) -> None:
    lines = base.read_text().splitlines()
    header_idx = None
    for idx, line in enumerate(lines):
        if line.startswith("p cnf "):
            header_idx = idx
            parts = line.split()
            if len(parts) != 4:
                raise ValueError(f"bad DIMACS header in {base}: {line}")
            n_vars = int(parts[2])
            n_clauses = int(parts[3])
            lines[idx] = f"p cnf {n_vars} {n_clauses + len(clauses)}"
            break
    if header_idx is None:
        raise ValueError(f"missing DIMACS header in {base}")

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as f:
        for line in lines:
            f.write(line)
            f.write("\n")
        f.write("c F420 injected F343 clauses from F414\n")
        for clause in clauses:
            f.write(" ".join(str(lit) for lit in clause))
            f.write(" 0\n")


def ensure_cnf_and_varmap(candidate: str, spec: dict, workdir: Path) -> tuple[Path, Path, dict | None]:
    base_cnf = spec["cnf"]
    base_varmap = Path(f"{base_cnf}.varmap.json")
    if base_cnf.exists() and base_varmap.exists():
        return base_cnf, base_varmap, None

    generated_cnf = workdir / base_cnf.name
    cmd = [
        "python3",
        str(REPO / "headline_hunt/bets/cascade_aux_encoding/encoders/cascade_aux_encoder.py"),
        "--sr",
        "60",
        "--m0",
        str(spec["m0"]),
        "--fill",
        str(spec["fill"]),
        "--kernel-bit",
        str(spec["bit"]),
        "--mode",
        "force",
        "--out",
        str(generated_cnf),
        "--varmap",
        "+",
        "--quiet",
    ]
    proc = subprocess.run(
        cmd,
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"failed to regenerate missing CNF/varmap for {candidate}: {proc.stderr}")
    generated_varmap = Path(f"{generated_cnf}.varmap.json")
    if not generated_cnf.exists() or not generated_varmap.exists():
        raise RuntimeError(f"encoder did not create {generated_cnf} and sidecar")
    return generated_cnf, generated_varmap, {"cmd": cmd, "stdout": proc.stdout, "stderr": proc.stderr}


def check_f343_vars(varmap_path: Path, clauses: list[list[int]]) -> None:
    data = json.loads(varmap_path.read_text())
    d_w57 = data["aux_W"]["57"]
    expected = {abs(clauses[0][0]), abs(clauses[1][0]), abs(clauses[1][1])}
    actual = {abs(int(d_w57[0])), abs(int(d_w57[22])), abs(int(d_w57[23]))}
    if expected != actual:
        raise RuntimeError(f"F343 clause vars do not match {varmap_path}: expected {expected}, actual {actual}")


def watch_args(varmap_path: Path) -> list[str]:
    data = json.loads(varmap_path.read_text())
    labels_by_var: dict[int, str] = {}

    def add(label: str, lit: int) -> None:
        var = abs(int(lit))
        if var <= 1:
            return
        # CaDiCaL's learner watcher is keyed by SAT var, so duplicate labels
        # for the same var collapse to the last label seen by cascade_propagator.
        labels_by_var[var] = label

    for side in ("actual_p1", "actual_p2"):
        regs = data.get(side, {})
        for reg in ("a", "e"):
            for rnd in range(57, 64):
                key = f"{reg}_{rnd}"
                for bit, lit in enumerate(regs.get(key, [])):
                    add(f"{side}_{reg}_{rnd}_b{bit}", lit)

    for key, lits in data.get("aux_modular_diff", {}).items():
        reg, rnd = key.split("_")
        for bit, lit in enumerate(lits):
            add(f"auxmod_{reg}_{rnd}_b{bit}", lit)

    return [f"--learn-watch-var={label}:{var}" for var, label in sorted(labels_by_var.items())]


METRIC_PATTERNS = {
    "result": re.compile(r"^Result:\s+(-?\d+)"),
    "decisions": re.compile(r"^\s+decisions:\s+(\d+)"),
    "backtracks": re.compile(r"^\s+backtracks:\s+(\d+)"),
    "learned_exported": re.compile(r"^\s+learned exported:\s+(\d+)"),
    "learned_touching_watched": re.compile(r"^\s+learned touching watched:\s+(\d+)"),
    "learn_touch": re.compile(r"^\s+learn_touch:\s+label=(\S+)\s+clauses=(\d+)"),
}


def parse_metrics(stderr: str) -> dict:
    metrics: dict[str, object] = {"learn_touch_counts": {}}
    touch_counts = metrics["learn_touch_counts"]
    assert isinstance(touch_counts, dict)
    for line in stderr.splitlines():
        for key, pattern in METRIC_PATTERNS.items():
            match = pattern.search(line)
            if not match:
                continue
            if key == "learn_touch":
                touch_counts[match.group(1)] = int(match.group(2))
            else:
                metrics[key] = int(match.group(1))
            break
    return metrics


def top_counts(metrics: dict, n: int = 16) -> list[list[object]]:
    counts = metrics.get("learn_touch_counts", {})
    if not isinstance(counts, dict):
        return []
    return [[label, value] for label, value in sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:n]]


def run_solver(binary: Path, cnf: Path, varmap: Path, args: list[str], stdout: Path, stderr: Path, conflicts: int) -> dict:
    cmd = [str(binary), str(cnf), str(varmap), f"--conflicts={conflicts}", "--learn-max-size=-1", *args]
    start = time.perf_counter()
    proc = subprocess.run(
        cmd,
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    wall = time.perf_counter() - start
    stdout.write_text(proc.stdout)
    stderr.write_text(proc.stderr)
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "wall_seconds": wall,
        "stdout_log": str(stdout),
        "stderr_log": str(stderr),
        "metrics": parse_metrics(proc.stderr),
    }


def append_run(candidate: str, cnf: Path, wall: float, stderr_log: Path, condition: str) -> dict:
    proc = subprocess.run(
        [
            "python3",
            str(REPO / "headline_hunt/infra/append_run.py"),
            "--bet",
            "programmatic_sat_propagator",
            "--candidate",
            f"cand_n32_{candidate}",
            "--cnf",
            str(cnf),
            "--solver",
            "cadical-ipasir-up",
            "--solver-version",
            "3.0.0",
            "--seed",
            "0",
            "--status",
            "TIMEOUT",
            "--wall",
            f"{wall:.6f}",
            "--encoder",
            f"cascade_aux_v1_modeA_sr60_force_F420_{condition}",
            "--log",
            str(stderr_log),
            "--notes",
            f"F420 actual-register learned-neighborhood {condition} for {candidate}",
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"append_run failed for {candidate}/{condition}: {proc.stderr}\n{proc.stdout}")
    return {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def pct_delta(new: int, old: int) -> float | None:
    if old == 0:
        return None
    return 100.0 * (new - old) / old


def add_delta(f343: dict, baseline: dict) -> None:
    delta = {}
    for key in ("decisions", "backtracks", "learned_exported", "learned_touching_watched"):
        a = f343["metrics"].get(key)
        b = baseline["metrics"].get(key)
        if isinstance(a, int) and isinstance(b, int):
            delta[key] = a - b
            delta[f"{key}_pct"] = pct_delta(a, b)
    f343["delta_vs_baseline_same_watcher"] = delta


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--binary", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=RESULT_DIR / "F420_actual_register_cross_candidate_learned_neighborhood.json")
    ap.add_argument("--workdir", type=Path, default=Path("/tmp/F420"))
    ap.add_argument("--conflicts", type=int, default=50000)
    ap.add_argument("--append-runs", action="store_true")
    ap.add_argument("--candidates", nargs="+", default=list(CANDIDATES))
    args = ap.parse_args()

    if not args.binary.exists():
        raise SystemExit(f"missing binary: {args.binary}")

    args.workdir.mkdir(parents=True, exist_ok=True)
    runs_by_candidate: dict[str, dict[str, dict]] = {}
    result = {
        "report_id": "F420",
        "date": utc_now(),
        "bet": "programmatic_sat_propagator",
        "parents": ["F416", "F417", "F418", "F419"],
        "binary": str(args.binary),
        "conflicts": args.conflicts,
        "watch_scope": "actual_p1/p2 a/e rounds57-63 plus aux_modular_diff",
        "runs": [],
    }

    for candidate in args.candidates:
        spec = CANDIDATES[candidate]
        base_cnf, varmap, generated = ensure_cnf_and_varmap(candidate, spec, args.workdir)
        check_f343_vars(varmap, spec["f343"])
        watch = watch_args(varmap)

        f343_cnf = args.workdir / f"{base_cnf.stem}_F420_F343.cnf"
        inject_cnf(base_cnf, f343_cnf, spec["f343"])

        runs_by_candidate[candidate] = {}
        for condition, cnf in (("baseline", base_cnf), ("f343", f343_cnf)):
            audit = audit_cnf(cnf)
            stdout = args.workdir / f"{candidate}_{condition}.stdout.log"
            stderr = args.workdir / f"{candidate}_{condition}.stderr.log"
            run = run_solver(args.binary, cnf, varmap, watch, stdout, stderr, args.conflicts)
            run.update(
                {
                    "candidate": candidate,
                    "condition": condition,
                    "cnf": str(cnf),
                    "varmap": str(varmap),
                    "audit": audit,
                    "generated_input": generated,
                    "n_watch_vars": len(watch),
                    "top_touch_counts": top_counts(run["metrics"]),
                    "f343_clauses": spec["f343"] if condition == "f343" else [],
                }
            )
            if args.append_runs:
                run["append_run"] = append_run(candidate, cnf, run["wall_seconds"], stderr, condition)
            runs_by_candidate[candidate][condition] = run
            result["runs"].append(run)

        add_delta(runs_by_candidate[candidate]["f343"], runs_by_candidate[candidate]["baseline"])

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
