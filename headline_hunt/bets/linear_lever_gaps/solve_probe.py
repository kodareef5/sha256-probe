#!/usr/bin/env python3
"""
solve_probe.py — run one solver on a CNF with a wall-clock limit; report
status / wall / conflicts and save the model (v-lines) on SAT.

Usage: solve_probe.py <cnf> <kissat|cadical> <seed> <timeout_s> [model_out]
"""
import os
import re
import subprocess
import sys
import time


def parse_conflicts(text):
    if not text:
        return None
    best = None
    for line in text.splitlines():
        m = re.search(r"conflicts:?\s+(\d+)", line)
        if m:
            best = int(m.group(1))
    return best


def main():
    cnf, solver, seed, timeout = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
    model_out = sys.argv[5] if len(sys.argv) > 5 else None
    if solver == "kissat":
        cmd = ["kissat", f"--seed={seed}", cnf]          # no -q => stats + model
    elif solver == "cadical":
        cmd = ["cadical", f"--seed={seed}", cnf]
    else:
        print(f"unknown solver {solver}"); sys.exit(2)

    t0 = time.time()
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        wall = time.time() - t0
        status = {10: "SAT", 20: "UNSAT"}.get(r.returncode, "UNKNOWN")
        conflicts = parse_conflicts(r.stdout)
        print(f"[{solver} seed={seed}] {status}  wall={wall:.1f}s  conflicts={conflicts}  cnf={os.path.basename(cnf)}")
        if status == "SAT" and model_out:
            with open(model_out, "w") as f:
                f.write(r.stdout)
            print(f"  model saved -> {model_out}")
    except subprocess.TimeoutExpired:
        print(f"[{solver} seed={seed}] TIMEOUT  wall={timeout}s  cnf={os.path.basename(cnf)}")


if __name__ == "__main__":
    main()
