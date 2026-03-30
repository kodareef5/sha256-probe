#!/usr/bin/env python3
"""
Script 15: Cube-and-Conquer for sr=60

CDCL solvers have massive variance. The same problem might take 10s
or 10000s depending on initial branching decisions. We exploit this
by partitioning the search space into thousands of subproblems.

Method:
  1. Generate the base sr=60 DIMACS using our CSA encoder
  2. Fix N bits of W1[57] (or W1[57..58]), generating 2^N subproblems
  3. For each subproblem: append unit clauses fixing those bits, run Kissat
     with a short timeout (30-60s)
  4. If ANY subproblem returns SAT, we've solved sr=60

This exploits the fact that in 4095 out of 4096 subproblems, Kissat
either proves UNSAT quickly (dead branch) or times out (hard branch).
But one "lucky" partition might perfectly align with Kissat's heuristics.
"""

import sys
import os
import time
import subprocess
import multiprocessing
import tempfile
import shutil

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')


def generate_base_dimacs():
    """Generate the base sr=60 CNF and return (filepath, free_var_ids)."""
    cnf = enc.encode_collision('sr60')
    base_file = "/tmp/sr60_cube_base.cnf"
    cnf.write_dimacs(base_file)

    # Collect the variable IDs for W1[57] bits (first 32 free variables)
    w1_57_vars = []
    for bit in range(32):
        name = f"W1_57[{bit}]"
        for vid, vname in cnf.free_var_names.items():
            if vname == name:
                w1_57_vars.append(vid)
                break

    # Also collect W1[58] bits
    w1_58_vars = []
    for bit in range(32):
        name = f"W1_58[{bit}]"
        for vid, vname in cnf.free_var_names.items():
            if vname == name:
                w1_58_vars.append(vid)
                break

    n_vars = cnf.next_var - 1
    n_clauses = len(cnf.clauses)

    return base_file, w1_57_vars, w1_58_vars, n_vars, n_clauses, cnf


def solve_subproblem(args):
    """Solve one subproblem (called by multiprocessing pool)."""
    base_file, cube_idx, fixed_vars, fixed_values, timeout_sec, work_dir = args

    # Create subproblem file by appending unit clauses to base
    sub_file = os.path.join(work_dir, f"cube_{cube_idx}.cnf")

    # Read base file header to get counts
    with open(base_file, 'r') as f:
        header = f.readline()
        parts = header.split()
        n_vars = int(parts[2])
        n_clauses = int(parts[3])

    # Write modified file with extra unit clauses
    n_extra = len(fixed_vars)
    with open(base_file, 'r') as fin, open(sub_file, 'w') as fout:
        # Updated header
        fout.write(f"p cnf {n_vars} {n_clauses + n_extra}\n")
        next(fin)  # skip original header
        # Copy all original clauses
        for line in fin:
            fout.write(line)
        # Add unit clauses for fixed bits
        for var_id, val in zip(fixed_vars, fixed_values):
            fout.write(f"{var_id if val else -var_id} 0\n")

    # Run kissat
    try:
        t0 = time.time()
        result = subprocess.run(
            ["timeout", str(timeout_sec), "kissat", "-q", sub_file],
            capture_output=True, text=True, timeout=timeout_sec + 10
        )
        elapsed = time.time() - t0

        if result.returncode == 10:
            return ("SAT", cube_idx, elapsed, result.stdout)
        elif result.returncode == 20:
            return ("UNSAT", cube_idx, elapsed, None)
        else:
            return ("TIMEOUT", cube_idx, elapsed, None)
    except Exception as e:
        return ("ERROR", cube_idx, 0, str(e))
    finally:
        try:
            os.unlink(sub_file)
        except:
            pass


def main():
    n_bits = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    timeout_per = int(sys.argv[2]) if len(sys.argv) > 2 else 30
    n_workers = int(sys.argv[3]) if len(sys.argv) > 3 else max(1, multiprocessing.cpu_count() - 1)

    n_cubes = 2 ** n_bits
    est_time = n_cubes * timeout_per / n_workers

    print("=" * 70, flush=True)
    print("Cube-and-Conquer for sr=60", flush=True)
    print(f"  Fixed bits: {n_bits} -> {n_cubes} subproblems", flush=True)
    print(f"  Timeout per subproblem: {timeout_per}s", flush=True)
    print(f"  Workers: {n_workers}", flush=True)
    print(f"  Estimated wall time: {est_time:.0f}s ({est_time/3600:.1f}h)", flush=True)
    print("=" * 70, flush=True)

    # Generate base DIMACS
    print("\nGenerating base sr=60 DIMACS...", flush=True)
    base_file, w1_57_vars, w1_58_vars, n_vars, n_clauses, cnf = generate_base_dimacs()
    print(f"  {n_vars} vars, {n_clauses} clauses", flush=True)
    print(f"  W1[57] var IDs: {w1_57_vars[:5]}... ({len(w1_57_vars)} total)", flush=True)

    # Choose which bits to fix (high bits of W1[57] are most impactful)
    if n_bits <= 32:
        # Fix the top n_bits of W1[57]
        fixed_var_ids = [w1_57_vars[31 - i] for i in range(min(n_bits, 32))]
    else:
        # Fix all 32 bits of W1[57] + some of W1[58]
        fixed_var_ids = w1_57_vars + [w1_58_vars[31 - i] for i in range(n_bits - 32)]

    print(f"  Fixing {n_bits} bits from var IDs: {fixed_var_ids}", flush=True)

    # Create work directory
    work_dir = tempfile.mkdtemp(prefix="cube_sr60_")
    print(f"  Work dir: {work_dir}", flush=True)

    # Generate all subproblem arguments
    tasks = []
    for cube_idx in range(n_cubes):
        # Convert cube_idx to bit values
        values = [(cube_idx >> bit) & 1 for bit in range(n_bits)]
        tasks.append((base_file, cube_idx, fixed_var_ids, values, timeout_per, work_dir))

    # Run in parallel
    print(f"\nLaunching {n_cubes} subproblems across {n_workers} workers...", flush=True)
    t_start = time.time()

    sat_found = False
    n_sat = 0
    n_unsat = 0
    n_timeout = 0
    n_error = 0
    sat_result = None

    with multiprocessing.Pool(n_workers) as pool:
        for i, result in enumerate(pool.imap_unordered(solve_subproblem, tasks)):
            status, cube_idx, elapsed, stdout = result

            if status == "SAT":
                n_sat += 1
                sat_found = True
                sat_result = result
                print(f"\n  [!!!] CUBE {cube_idx}: SAT in {elapsed:.1f}s!", flush=True)
                pool.terminate()
                break
            elif status == "UNSAT":
                n_unsat += 1
            elif status == "TIMEOUT":
                n_timeout += 1
            else:
                n_error += 1

            # Progress report
            done = n_sat + n_unsat + n_timeout + n_error
            if done % max(1, n_cubes // 20) == 0 or done == n_cubes:
                elapsed_total = time.time() - t_start
                rate = done / elapsed_total if elapsed_total > 0 else 0
                eta = (n_cubes - done) / rate if rate > 0 else 0
                print(f"  [{done}/{n_cubes}] SAT={n_sat} UNSAT={n_unsat} TO={n_timeout} "
                      f"({elapsed_total:.0f}s, ETA {eta:.0f}s)", flush=True)

    t_total = time.time() - t_start

    # Cleanup
    try:
        shutil.rmtree(work_dir)
    except:
        pass

    # Summary
    print(f"\n{'='*70}", flush=True)
    print("RESULTS", flush=True)
    print(f"{'='*70}", flush=True)
    print(f"  Subproblems: {n_cubes}", flush=True)
    print(f"  SAT: {n_sat}, UNSAT: {n_unsat}, TIMEOUT: {n_timeout}, ERROR: {n_error}", flush=True)
    print(f"  Total time: {t_total:.1f}s ({t_total/3600:.2f}h)", flush=True)
    print(f"  UNSAT fraction: {n_unsat/max(1,n_sat+n_unsat+n_timeout)*100:.1f}%", flush=True)

    if sat_found:
        print(f"\n  [!!!] SR=60 SOLVED VIA CUBE-AND-CONQUER!", flush=True)
        # Extract solution from SAT result
        _, cube_idx, elapsed, stdout = sat_result
        print(f"  Lucky cube: {cube_idx} (binary: {cube_idx:0{n_bits}b})", flush=True)
        print(f"  Solve time: {elapsed:.1f}s", flush=True)
    else:
        print(f"\n  No solution found in {n_cubes} cubes.", flush=True)
        # Analysis
        if n_unsat > n_cubes * 0.8:
            print(f"  High UNSAT rate ({n_unsat/n_cubes*100:.0f}%) suggests most branches are dead.", flush=True)
            print(f"  Try: fewer fixed bits, or fix different variables.", flush=True)
        elif n_timeout > n_cubes * 0.8:
            print(f"  High TIMEOUT rate ({n_timeout/n_cubes*100:.0f}%) suggests subproblems still too hard.", flush=True)
            print(f"  Try: more fixed bits (more partitions), or longer per-cube timeout.", flush=True)


if __name__ == "__main__":
    main()
