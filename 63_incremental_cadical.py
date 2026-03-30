#!/usr/bin/env python3
"""
Script 63: CaDiCaL vs Kissat on k=0, k=3, and k=4 progressive constraints

HYPOTHESIS: CaDiCaL's different preprocessing (vivification, substitution,
bounded variable elimination) may solve the k=3 and k=4 problems faster
than Kissat. CaDiCaL 3.0's inprocessing strategy differs enough that it
could shine on this structure.

METHOD:
  1. Generate DIMACS for k=0 (pure sr59), k=3, k=4
  2. Run both CaDiCaL and Kissat on each
  3. Compare times and search statistics

CONTEXT:
  k=0: pure sr=59, 5 free words, no schedule constraint on W[61]
  k=3: constrains bits 0,1,2 of W[61] to match schedule equation
  k=4: adds bit 3 -- just 4 more clauses total
  Kissat baselines: k=0 ~220s, k=3 ~109s, k=4 ~1776s
"""

import sys
import os
import time
import subprocess
import re

# Import encoder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
mod = import_module('13_custom_cnf_encoder')

# SHA-256 helpers
def ROR(x, n): return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF
def sigma0_py(x): return ROR(x, 7) ^ ROR(x, 18) ^ (x >> 3)
def sigma1_py(x): return ROR(x, 17) ^ ROR(x, 19) ^ (x >> 10)

CADICAL = "/usr/local/bin/cadical"
KISSAT = "kissat"


def encode_sr59_plus_k(k_bits):
    """
    Encode sr=59 with k additional bits of W[61] schedule compliance.
    Returns (cnf, cnf_file_path, n_vars, n_clauses).
    """
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1[:]
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = mod.precompute_state(M1)
    state2, W2_pre = mod.precompute_state(M2)

    cnf = mod.CNFBuilder()

    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    # 5 free words (sr=59 base)
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(5)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(5)]

    # W[62] enforced from W[60], W[63] from W[61]
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[3]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46]))
    )
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[3]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46]))
    )
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[4]), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47]))
    )
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[4]), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47]))
    )

    W1_tail = list(w1_free) + [w1_62, w1_63]
    W2_tail = list(w2_free) + [w2_62, w2_63]

    # Run 7 rounds
    st1 = s1
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, mod.K[57+i], W1_tail[i])
    st2 = s2
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, mod.K[57+i], W2_tail[i])

    # Collision constraint
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    # Progressive W[61] schedule constraint (k bits)
    if k_bits > 0:
        w1_61_sched = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
            cnf.add_word(cnf.const_word(sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45]))
        )
        w2_61_sched = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
            cnf.add_word(cnf.const_word(sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45]))
        )

        for bit in range(min(k_bits, 32)):
            a1, b1 = w1_free[4][bit], w1_61_sched[bit]
            a2, b2 = w2_free[4][bit], w2_61_sched[bit]

            # Equality constraint for message 1
            if cnf._is_known(a1) and cnf._is_known(b1):
                if cnf._get_val(a1) != cnf._get_val(b1):
                    cnf.clauses.append([])
            elif cnf._is_known(a1):
                cnf.clauses.append([b1] if cnf._get_val(a1) else [-b1])
            elif cnf._is_known(b1):
                cnf.clauses.append([a1] if cnf._get_val(b1) else [-a1])
            else:
                cnf.clauses.append([-a1, b1])
                cnf.clauses.append([a1, -b1])

            # Equality constraint for message 2
            if cnf._is_known(a2) and cnf._is_known(b2):
                if cnf._get_val(a2) != cnf._get_val(b2):
                    cnf.clauses.append([])
            elif cnf._is_known(a2):
                cnf.clauses.append([b2] if cnf._get_val(a2) else [-b2])
            elif cnf._is_known(b2):
                cnf.clauses.append([a2] if cnf._get_val(b2) else [-a2])
            else:
                cnf.clauses.append([-a2, b2])
                cnf.clauses.append([a2, -b2])

    cnf_file = f"/tmp/sr59_k{k_bits}_test63.cnf"
    n_vars, n_clauses = cnf.write_dimacs(cnf_file)

    return cnf, cnf_file, n_vars, n_clauses


def parse_cadical_stats(stdout):
    """Parse CaDiCaL's statistics output."""
    stats = {'conflicts': None, 'decisions': None, 'propagations': None}
    for line in stdout.split('\n'):
        # CaDiCaL format: "c conflicts:                 12345        67.89    per second"
        m = re.match(r'^c\s+conflicts:\s+(\d+)', line)
        if m:
            stats['conflicts'] = int(m.group(1))
        m = re.match(r'^c\s+decisions:\s+(\d+)', line)
        if m:
            stats['decisions'] = int(m.group(1))
        m = re.match(r'^c\s+propagations:\s+(\d+)', line)
        if m:
            stats['propagations'] = int(m.group(1))
        # Also parse time from CaDiCaL
        m = re.match(r'^c\s+total process time since initialization:\s+([\d.]+)', line)
        if m:
            stats['process_time'] = float(m.group(1))
    return stats


def parse_kissat_stats(stdout):
    """Parse Kissat's statistics output."""
    stats = {'conflicts': None, 'decisions': None, 'propagations': None}
    for line in stdout.split('\n'):
        # Kissat format varies; look for summary lines
        m = re.search(r'c\s+(\d+)\s+conflicts', line)
        if m:
            stats['conflicts'] = int(m.group(1))
        m = re.search(r'c\s+(\d+)\s+decisions', line)
        if m:
            stats['decisions'] = int(m.group(1))
        m = re.search(r'c\s+(\d+)\s+propagations', line)
        if m:
            stats['propagations'] = int(m.group(1))
        m = re.search(r'c\s+process-time:\s+([\d.]+)', line)
        if m:
            stats['process_time'] = float(m.group(1))
    return stats


def run_solver(solver_path, cnf_file, timeout_sec, solver_name):
    """
    Run a SAT solver on a DIMACS file. Returns dict with results.
    """
    info = {
        'solver': solver_name,
        'cnf_file': cnf_file,
        'timeout': timeout_sec,
        'result': 'ERROR',
        'time': 0.0,
        'conflicts': None,
        'decisions': None,
        'propagations': None,
    }

    if solver_name == "cadical":
        cmd = [solver_path, "-t", str(timeout_sec), cnf_file]
    else:
        # kissat uses external timeout
        cmd = ["timeout", str(timeout_sec), solver_path, cnf_file]

    try:
        t0 = time.time()
        proc = subprocess.run(
            cmd,
            capture_output=True, text=True,
            timeout=timeout_sec + 120
        )
        elapsed = time.time() - t0
        info['time'] = elapsed

        stdout = proc.stdout

        # Parse result line
        for line in stdout.split('\n'):
            if line.startswith('s SATISFIABLE'):
                info['result'] = 'SAT'
                break
            elif line.startswith('s UNSATISFIABLE'):
                info['result'] = 'UNSAT'
                break

        if info['result'] == 'ERROR':
            if proc.returncode == 10:
                info['result'] = 'SAT'
            elif proc.returncode == 20:
                info['result'] = 'UNSAT'
            elif proc.returncode == 124:
                info['result'] = 'TIMEOUT'
            else:
                info['result'] = 'TIMEOUT'

        # Parse statistics
        if solver_name == "cadical":
            stats = parse_cadical_stats(stdout)
        else:
            stats = parse_kissat_stats(stdout)

        info['conflicts'] = stats.get('conflicts')
        info['decisions'] = stats.get('decisions')
        info['propagations'] = stats.get('propagations')
        if 'process_time' in stats:
            info['process_time'] = stats['process_time']

        # Extract solution variables if SAT
        if info['result'] == 'SAT':
            solution = {}
            for line in stdout.split('\n'):
                if line.startswith('v '):
                    for lit in line[2:].split():
                        lit_val = int(lit)
                        if lit_val != 0:
                            solution[abs(lit_val)] = (lit_val > 0)
            info['solution'] = solution

    except subprocess.TimeoutExpired:
        info['time'] = timeout_sec
        info['result'] = 'TIMEOUT'
    except FileNotFoundError:
        info['result'] = f'NOT_FOUND ({solver_path})'

    return info


def fmt(n):
    """Format number with commas, or N/A."""
    if n is None:
        return "N/A"
    return f"{n:,}"


def print_result(info, n_vars, n_clauses, k):
    """Print formatted result."""
    print(f"  Solver:        {info['solver']}")
    print(f"  Problem:       sr59+k{k} ({n_vars} vars, {n_clauses} clauses)")
    print(f"  Result:        {info['result']}")
    print(f"  Wall time:     {info['time']:.1f}s")
    if info.get('process_time'):
        print(f"  Process time:  {info['process_time']:.1f}s")
    if info['conflicts'] is not None:
        print(f"  Conflicts:     {fmt(info['conflicts'])}")
    if info['decisions'] is not None:
        print(f"  Decisions:     {fmt(info['decisions'])}")
    if info['propagations'] is not None:
        print(f"  Propagations:  {fmt(info['propagations'])}")


def main():
    print("=" * 70, flush=True)
    print("Script 63: CaDiCaL vs Kissat on progressive constraints", flush=True)
    print("=" * 70, flush=True)
    print(flush=True)
    print("Known Kissat baselines:", flush=True)
    print("  k=0 (pure sr59): ~220s SAT", flush=True)
    print("  k=3:              ~109s SAT", flush=True)
    print("  k=4:             ~1776s SAT", flush=True)
    print(flush=True)

    # Test matrix: (k, cadical_timeout, kissat_timeout)
    tests = [
        (0, 600, 300),     # k=0: pure sr59
        (3, 600, 300),     # k=3: easy
        (4, 1800, 1800),   # k=4: the hard transition
    ]

    all_results = []

    for k, cad_timeout, kis_timeout in tests:
        print("=" * 70, flush=True)
        print(f"k={k}: sr=59 + {k} bits of W[61] schedule compliance", flush=True)
        print("=" * 70, flush=True)

        # Encode
        t0 = time.time()
        cnf, cnf_file, nv, nc = encode_sr59_plus_k(k)
        t_enc = time.time() - t0
        print(f"  Encoded: {nv} vars, {nc} clauses in {t_enc:.1f}s", flush=True)
        print(f"  File: {cnf_file}", flush=True)
        print(flush=True)

        # Run CaDiCaL
        print(f"  --- CaDiCaL (timeout {cad_timeout}s) ---", flush=True)
        cad_result = run_solver(CADICAL, cnf_file, cad_timeout, "cadical")
        print_result(cad_result, nv, nc, k)
        print(flush=True)

        # Run Kissat (only if CaDiCaL didn't already show this is easy)
        print(f"  --- Kissat (timeout {kis_timeout}s) ---", flush=True)
        kis_result = run_solver(KISSAT, cnf_file, kis_timeout, "kissat")
        print_result(kis_result, nv, nc, k)
        print(flush=True)

        all_results.append({
            'k': k, 'nv': nv, 'nc': nc,
            'cadical': cad_result, 'kissat': kis_result,
        })

    # ================================================================
    # SUMMARY TABLE
    # ================================================================
    print("=" * 70, flush=True)
    print("COMPARISON SUMMARY", flush=True)
    print("=" * 70, flush=True)
    print(flush=True)

    hdr = f"{'k':>3} {'vars':>7} {'cls':>7} | {'CaDiCaL':>8} {'time':>8} {'conflicts':>12} | {'Kissat':>8} {'time':>8} {'conflicts':>12} | {'speedup':>8}"
    print(hdr, flush=True)
    print("-" * len(hdr), flush=True)

    for r in all_results:
        k = r['k']
        cad = r['cadical']
        kis = r['kissat']

        # Compute speedup (Kissat time / CaDiCaL time, >1 means CaDiCaL faster)
        if cad['result'] == 'SAT' and kis['result'] == 'SAT' and cad['time'] > 0:
            speedup = kis['time'] / cad['time']
            sp_str = f"{speedup:.2f}x"
        elif cad['result'] == 'TIMEOUT' and kis['result'] == 'SAT':
            sp_str = "Kis wins"
        elif kis['result'] == 'TIMEOUT' and cad['result'] == 'SAT':
            sp_str = "Cad wins"
        elif cad['result'] == 'TIMEOUT' and kis['result'] == 'TIMEOUT':
            sp_str = "both TO"
        else:
            sp_str = "---"

        print(f"{k:3d} {r['nv']:7d} {r['nc']:7d} | "
              f"{cad['result']:>8} {cad['time']:>7.1f}s {fmt(cad['conflicts']):>12} | "
              f"{kis['result']:>8} {kis['time']:>7.1f}s {fmt(kis['conflicts']):>12} | "
              f"{sp_str:>8}",
              flush=True)

    print(flush=True)

    # ================================================================
    # ANALYSIS
    # ================================================================
    print("ANALYSIS:", flush=True)
    print(flush=True)

    for r in all_results:
        k = r['k']
        cad = r['cadical']
        kis = r['kissat']

        print(f"  k={k}:", flush=True)
        if cad['result'] == 'SAT' and kis['result'] == 'SAT':
            if cad['time'] < kis['time']:
                ratio = kis['time'] / cad['time']
                print(f"    CaDiCaL {ratio:.1f}x faster ({cad['time']:.1f}s vs {kis['time']:.1f}s)", flush=True)
            else:
                ratio = cad['time'] / kis['time']
                print(f"    Kissat {ratio:.1f}x faster ({kis['time']:.1f}s vs {cad['time']:.1f}s)", flush=True)
        elif cad['result'] == 'TIMEOUT':
            print(f"    CaDiCaL TIMEOUT at {cad['timeout']}s", flush=True)
            if kis['result'] == 'SAT':
                print(f"    Kissat solved in {kis['time']:.1f}s", flush=True)
        elif kis['result'] == 'TIMEOUT':
            print(f"    Kissat TIMEOUT at {kis['timeout']}s", flush=True)
            if cad['result'] == 'SAT':
                print(f"    CaDiCaL solved in {cad['time']:.1f}s", flush=True)

        # Conflict efficiency comparison
        if cad['conflicts'] and kis['conflicts']:
            print(f"    Conflicts: CaDiCaL={fmt(cad['conflicts'])}, Kissat={fmt(kis['conflicts'])}", flush=True)

    # k=3 -> k=4 transition analysis
    k3_data = next((r for r in all_results if r['k'] == 3), None)
    k4_data = next((r for r in all_results if r['k'] == 4), None)

    if k3_data and k4_data:
        print(flush=True)
        print("  k=3 -> k=4 TRANSITION:", flush=True)

        for solver_key, name in [('cadical', 'CaDiCaL'), ('kissat', 'Kissat')]:
            s3 = k3_data[solver_key]
            s4 = k4_data[solver_key]
            if s3['result'] == 'SAT' and s4['result'] == 'SAT' and s3['time'] > 0:
                ratio = s4['time'] / s3['time']
                print(f"    {name}: k=4 is {ratio:.1f}x harder than k=3", flush=True)
            elif s3['result'] == 'SAT' and s4['result'] == 'TIMEOUT':
                print(f"    {name}: k=3 SAT in {s3['time']:.1f}s, k=4 TIMEOUT", flush=True)

    print(flush=True)
    print("CONCLUSIONS:", flush=True)

    # Check if CaDiCaL ever beat Kissat
    cadical_wins = sum(1 for r in all_results
                       if r['cadical']['result'] == 'SAT'
                       and (r['kissat']['result'] != 'SAT'
                            or r['cadical']['time'] < r['kissat']['time']))
    kissat_wins = sum(1 for r in all_results
                      if r['kissat']['result'] == 'SAT'
                      and (r['cadical']['result'] != 'SAT'
                           or r['kissat']['time'] < r['cadical']['time']))

    if kissat_wins > cadical_wins:
        print("  Kissat dominates CaDiCaL on this problem class.", flush=True)
        print("  Kissat's focused CDCL search without heavy inprocessing", flush=True)
        print("  is better suited for the SHA-256 collision structure.", flush=True)
    elif cadical_wins > kissat_wins:
        print("  CaDiCaL outperforms Kissat on this problem class.", flush=True)
        print("  Its vivification/substitution preprocessing pays off.", flush=True)
    else:
        print("  Mixed results -- neither solver consistently dominates.", flush=True)

    # Check if k=3->k=4 cliff exists for both solvers
    if k3_data and k4_data:
        k3_cad_sat = k3_data['cadical']['result'] == 'SAT'
        k4_cad_sat = k4_data['cadical']['result'] == 'SAT'
        k3_kis_sat = k3_data['kissat']['result'] == 'SAT'
        k4_kis_sat = k4_data['kissat']['result'] == 'SAT'

        if k3_cad_sat and not k4_cad_sat and k3_kis_sat and not k4_kis_sat:
            print("  The k=3->k=4 hardness cliff is SOLVER-INDEPENDENT.", flush=True)
            print("  This is a structural property of the SHA-256 schedule,", flush=True)
            print("  not an artifact of solver heuristics.", flush=True)
        elif k3_cad_sat and not k4_cad_sat and k4_kis_sat:
            print("  CaDiCaL fails at k=4 where Kissat succeeds.", flush=True)
            print("  The cliff is real but Kissat's search handles it better.", flush=True)

    print(flush=True)


if __name__ == "__main__":
    main()
