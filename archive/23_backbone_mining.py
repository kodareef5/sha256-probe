#!/usr/bin/env python3
"""
Script 23: Backbone Mining via Seed Diversity

At k=3, the problem solves in ~109s. By running with 30 different
random seeds, we get 30 diverse solutions. Bits that are FIXED across
all solutions are "backbones" — structural invariants forced by the
math, not by solver heuristics.

If we find backbone bits in the free words or internal carries,
we can hardcode them into sr=60 as unit clauses, effectively
reducing the search space without losing the solution.
"""

import sys
import os
import time
import subprocess
import multiprocessing

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')


def generate_k3_dimacs():
    """Generate the k=3 DIMACS file and return free variable mappings."""
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    cnf = enc.CNFBuilder()
    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(5)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(5)]

    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[3]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[3]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46])))
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[4]), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[4]), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47])))

    W1_tail = list(w1_free) + [w1_62, w1_63]
    W2_tail = list(w2_free) + [w2_62, w2_63]

    st1 = s1
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, enc.K[57+i], W1_tail[i])
    st2 = s2
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, enc.K[57+i], W2_tail[i])

    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    # k=3 schedule compliance
    w1_61_sched = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45])))
    w2_61_sched = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45])))

    for bit in range(3):
        for a, b in [(w1_free[4][bit], w1_61_sched[bit]),
                     (w2_free[4][bit], w2_61_sched[bit])]:
            if cnf._is_known(a) and cnf._is_known(b):
                if cnf._get_val(a) != cnf._get_val(b):
                    cnf.clauses.append([])
            elif cnf._is_known(a):
                cnf.clauses.append([b] if cnf._get_val(a) else [-b])
            elif cnf._is_known(b):
                cnf.clauses.append([a] if cnf._get_val(b) else [-a])
            else:
                cnf.clauses.append([-a, b])
                cnf.clauses.append([a, -b])

    cnf_file = "/tmp/k3_backbone.cnf"
    cnf.write_dimacs(cnf_file)

    # Collect ALL variable names (not just free words)
    return cnf_file, cnf.free_var_names, cnf.next_var - 1


def solve_with_seed(args):
    """Run kissat with a specific seed."""
    cnf_file, seed, timeout = args
    try:
        r = subprocess.run(
            ["kissat", f"--seed={seed}", "-q", cnf_file],
            capture_output=True, text=True,
            timeout=timeout
        )
        if r.returncode == 10:
            # Parse solution
            assignment = {}
            for line in r.stdout.split('\n'):
                if line.startswith('v '):
                    for lit in line[2:].split():
                        v = int(lit)
                        if v != 0:
                            assignment[abs(v)] = (v > 0)
            return seed, "SAT", assignment
        elif r.returncode == 20:
            return seed, "UNSAT", None
        else:
            return seed, "TIMEOUT", None
    except:
        return seed, "ERROR", None


def main():
    n_seeds = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    n_workers = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    print("=" * 60, flush=True)
    print(f"Backbone Mining: k=3 with {n_seeds} seeds", flush=True)
    print(f"Workers: {n_workers}, Timeout: {timeout}s each", flush=True)
    print("=" * 60, flush=True)

    # Generate DIMACS
    print("Generating k=3 DIMACS...", flush=True)
    cnf_file, free_var_names, n_vars = generate_k3_dimacs()
    print(f"  {n_vars} vars, file: {cnf_file}", flush=True)
    print(f"  Free variable names: {len(free_var_names)}", flush=True)

    # Run with different seeds in parallel
    print(f"\nLaunching {n_seeds} Kissat instances...", flush=True)
    tasks = [(cnf_file, seed, timeout) for seed in range(n_seeds)]

    solutions = []
    t_start = time.time()

    with multiprocessing.Pool(n_workers) as pool:
        for seed, status, assignment in pool.imap_unordered(solve_with_seed, tasks):
            if status == "SAT":
                solutions.append(assignment)
                elapsed = time.time() - t_start
                print(f"  Seed {seed:3d}: SAT ({elapsed:.0f}s total, {len(solutions)} solutions)", flush=True)
            elif status == "TIMEOUT":
                print(f"  Seed {seed:3d}: TIMEOUT", flush=True)
            else:
                print(f"  Seed {seed:3d}: {status}", flush=True)

    t_total = time.time() - t_start
    print(f"\nCompleted: {len(solutions)} SAT, {n_seeds - len(solutions)} non-SAT ({t_total:.0f}s)", flush=True)

    if len(solutions) < 2:
        print("Not enough solutions for mining.", flush=True)
        return

    # === BACKBONE MINING ===
    print(f"\n{'='*60}", flush=True)
    print(f"Mining {len(solutions)} solutions for backbones", flush=True)
    print(f"{'='*60}", flush=True)

    # Check every variable that appears in all solutions
    all_vars = set()
    for sol in solutions:
        all_vars.update(sol.keys())

    # Find backbones: variables with same value across ALL solutions
    backbone_true = []
    backbone_false = []
    variable_count = 0

    for var in sorted(all_vars):
        if var == 1:  # Skip the TRUE constant
            continue
        vals = set()
        for sol in solutions:
            if var in sol:
                vals.add(sol[var])
        if len(vals) == 1:
            val = vals.pop()
            if val:
                backbone_true.append(var)
            else:
                backbone_false.append(var)
        variable_count += 1

    total_backbones = len(backbone_true) + len(backbone_false)
    print(f"\n  Total variables checked: {variable_count}", flush=True)
    print(f"  Backbones (fixed across all {len(solutions)} solutions): {total_backbones}", flush=True)
    print(f"    Always TRUE:  {len(backbone_true)}", flush=True)
    print(f"    Always FALSE: {len(backbone_false)}", flush=True)
    print(f"  Free variables: {variable_count - total_backbones}", flush=True)
    print(f"  Backbone ratio: {total_backbones/variable_count*100:.1f}%", flush=True)

    # Identify which free words have backbone bits
    print(f"\n--- Backbones in Free Words ---", flush=True)
    free_backbones = 0
    for var in backbone_true + backbone_false:
        if var in free_var_names:
            val = var in backbone_true
            print(f"  {free_var_names[var]} = {int(val)} (BACKBONE)", flush=True)
            free_backbones += 1

    if free_backbones == 0:
        print(f"  No backbones in free word bits", flush=True)

    print(f"\n  Free word backbones: {free_backbones} / {len(free_var_names)}", flush=True)

    # Show backbone distribution by variable ID range
    print(f"\n--- Backbone Distribution ---", flush=True)
    ranges = [(2, 100), (100, 500), (500, 1000), (1000, 2000),
              (2000, 5000), (5000, 8000), (8000, n_vars+1)]
    for lo, hi in ranges:
        count = sum(1 for v in backbone_true + backbone_false if lo <= v < hi)
        total_in_range = sum(1 for v in all_vars if lo <= v < hi)
        if total_in_range > 0:
            pct = count / total_in_range * 100
            bar = "#" * int(pct / 2)
            print(f"  Vars {lo:5d}-{hi:5d}: {count:4d}/{total_in_range:4d} ({pct:.0f}%) {bar}", flush=True)

    # Check pairwise Hamming distance of solutions (diversity check)
    print(f"\n--- Solution Diversity ---", flush=True)
    for i in range(min(5, len(solutions))):
        for j in range(i+1, min(5, len(solutions))):
            diff = 0
            common = 0
            for var in all_vars:
                if var in solutions[i] and var in solutions[j]:
                    common += 1
                    if solutions[i][var] != solutions[j][var]:
                        diff += 1
            print(f"  Sol {i} vs {j}: {diff} diffs / {common} common vars ({diff/max(1,common)*100:.1f}%)", flush=True)

    # If significant backbones found, save them for injection
    if total_backbones > 50:
        backbone_file = "/tmp/k3_backbones.txt"
        with open(backbone_file, 'w') as f:
            for var in backbone_true:
                f.write(f"{var}\n")
            for var in backbone_false:
                f.write(f"-{var}\n")
        print(f"\n  Backbones saved to {backbone_file} ({total_backbones} unit clauses)", flush=True)
        print(f"  To inject into sr=60: append as unit clauses to the DIMACS file", flush=True)


if __name__ == "__main__":
    main()
