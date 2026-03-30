#!/usr/bin/env python3
"""
Script 09: Reduced DIMACS CNF for sr=60 -> Kissat

Uses Z3's bit-blaster to generate optimized DIMACS CNF from the sr=60
BitVec formulation, then feeds it to Kissat.

The paper's sr59_cdcl.c achieved 3.3x speedup over the basic Python encoder
by precomputing rounds 0-56 and encoding only the 7-round tail with
optimized carry-save adder trees. Here we get a similar effect by:

1. Precomputing rounds 0-56 in Python (constant folding)
2. Encoding only rounds 57-63 as Z3 BitVec constraints
3. Using Z3's optimized bit-blaster to generate CNF
4. Feeding the CNF to Kissat (best-in-class CDCL solver)

This separates the encoding quality (Z3) from the solving engine (Kissat),
potentially getting the best of both worlds.
"""

import sys
import os
import time
import subprocess
import tempfile

try:
    from z3 import *
except ImportError:
    print("Z3 not installed. Install with: pip install z3-solver")
    sys.exit(1)

# SHA-256 functions (pure Python)
def ROR(x, n): return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF
def SHR(x, n): return x >> n
def Ch_py(e, f, g): return ((e & f) ^ ((~e) & g)) & 0xFFFFFFFF
def Maj_py(a, b, c): return (a & b) ^ (a & c) ^ (b & c)
def Sigma0_py(a): return ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22)
def Sigma1_py(e): return ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25)
def sigma0_py(x): return ROR(x, 7) ^ ROR(x, 18) ^ SHR(x, 3)
def sigma1_py(x): return ROR(x, 17) ^ ROR(x, 19) ^ SHR(x, 10)

# Z3 BitVec versions
def ror_z3(x, n): return LShR(x, n) | (x << (32 - n))
def Ch_z3(e, f, g): return (e & f) ^ (~e & g)
def Maj_z3(a, b, c): return (a & b) ^ (a & c) ^ (b & c)
def Sigma0_z3(a): return ror_z3(a, 2) ^ ror_z3(a, 13) ^ ror_z3(a, 22)
def Sigma1_z3(e): return ror_z3(e, 6) ^ ror_z3(e, 11) ^ ror_z3(e, 25)
def sigma0_z3(x): return ror_z3(x, 7) ^ ror_z3(x, 18) ^ LShR(x, 3)
def sigma1_z3(x): return ror_z3(x, 17) ^ ror_z3(x, 19) ^ LShR(x, 10)

K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
]
IV = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
      0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19]


def precompute_state(M):
    W = [0] * 57
    for i in range(16): W[i] = M[i]
    for i in range(16, 57):
        W[i] = (sigma1_py(W[i-2]) + W[i-7] + sigma0_py(W[i-15]) + W[i-16]) & 0xFFFFFFFF
    a, b, c, d, e, f, g, h = IV
    for i in range(57):
        T1 = (h + Sigma1_py(e) + Ch_py(e, f, g) + K[i] + W[i]) & 0xFFFFFFFF
        T2 = (Sigma0_py(a) + Maj_py(a, b, c)) & 0xFFFFFFFF
        h = g; g = f; f = e; e = (d + T1) & 0xFFFFFFFF
        d = c; c = b; b = a; a = (T1 + T2) & 0xFFFFFFFF
    return (a, b, c, d, e, f, g, h), W


def build_and_export_cnf(mode="sr60"):
    """
    Build the Z3 instance and export as DIMACS CNF.
    mode: "sr60" (4 free words) or "sr59" (5 free words, for baseline)
    """
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = precompute_state(M1)
    state2, W2_pre = precompute_state(M2)

    assert state1[0] == state2[0], "da[56] must be 0!"

    if mode == "sr60":
        n_free = 4
        print("Building sr=60 instance (4 free words, 0 slack)")
    else:
        n_free = 5
        print("Building sr=59 instance (5 free words, 64 slack)")

    # Free variables
    w1 = [BitVec(f'w1_{57+i}', 32) for i in range(n_free)]
    w2 = [BitVec(f'w2_{57+i}', 32) for i in range(n_free)]

    # Build schedule cascade
    if n_free == 5:
        # sr=59: W[57..61] free, W[62] enforced from W[60], W[63] from W[61]
        w1_62 = sigma1_z3(w1[3]) + BitVecVal(W1_pre[55], 32) + BitVecVal(sigma0_py(W1_pre[47]), 32) + BitVecVal(W1_pre[46], 32)
        w2_62 = sigma1_z3(w2[3]) + BitVecVal(W2_pre[55], 32) + BitVecVal(sigma0_py(W2_pre[47]), 32) + BitVecVal(W2_pre[46], 32)
        w1_63 = sigma1_z3(w1[4]) + BitVecVal(W1_pre[56], 32) + BitVecVal(sigma0_py(W1_pre[48]), 32) + BitVecVal(W1_pre[47], 32)
        w2_63 = sigma1_z3(w2[4]) + BitVecVal(W2_pre[56], 32) + BitVecVal(sigma0_py(W2_pre[48]), 32) + BitVecVal(W2_pre[47], 32)
        W1_tail = list(w1) + [w1_62, w1_63]
        W2_tail = list(w2) + [w2_62, w2_63]
    else:
        # sr=60: W[57..60] free, W[61] enforced from W[59], W[62] from W[60], W[63] from W[61]
        w1_61 = sigma1_z3(w1[2]) + BitVecVal(W1_pre[54], 32) + BitVecVal(sigma0_py(W1_pre[46]), 32) + BitVecVal(W1_pre[45], 32)
        w2_61 = sigma1_z3(w2[2]) + BitVecVal(W2_pre[54], 32) + BitVecVal(sigma0_py(W2_pre[46]), 32) + BitVecVal(W2_pre[45], 32)
        w1_62 = sigma1_z3(w1[3]) + BitVecVal(W1_pre[55], 32) + BitVecVal(sigma0_py(W1_pre[47]), 32) + BitVecVal(W1_pre[46], 32)
        w2_62 = sigma1_z3(w2[3]) + BitVecVal(W2_pre[55], 32) + BitVecVal(sigma0_py(W2_pre[47]), 32) + BitVecVal(W2_pre[46], 32)
        w1_63 = sigma1_z3(w1_61) + BitVecVal(W1_pre[56], 32) + BitVecVal(sigma0_py(W1_pre[48]), 32) + BitVecVal(W1_pre[47], 32)
        w2_63 = sigma1_z3(w2_61) + BitVecVal(W2_pre[56], 32) + BitVecVal(sigma0_py(W2_pre[48]), 32) + BitVecVal(W2_pre[47], 32)
        W1_tail = list(w1) + [w1_61, w1_62, w1_63]
        W2_tail = list(w2) + [w2_61, w2_62, w2_63]

    # Symbolic compression rounds 57-63
    def symbolic_rounds(state_init, W_tail):
        a, b, c, d, e, f, g, h = [BitVecVal(x, 32) for x in state_init]
        for i in range(7):
            T1 = h + Sigma1_z3(e) + Ch_z3(e, f, g) + BitVecVal(K[57+i], 32) + W_tail[i]
            T2 = Sigma0_z3(a) + Maj_z3(a, b, c)
            h = g; g = f; f = e; e = d + T1
            d = c; c = b; b = a; a = T1 + T2
        return (a, b, c, d, e, f, g, h)

    final1 = symbolic_rounds(state1, W1_tail)
    final2 = symbolic_rounds(state2, W2_tail)

    # Collect all constraints
    constraints = []
    for i in range(8):
        constraints.append(final1[i] == final2[i])

    # Use Z3's goal/tactic system to bit-blast to CNF
    print("Bit-blasting to CNF via Z3...")
    t0 = time.time()

    g = Goal()
    for c in constraints:
        g.add(c)

    # Apply simplification then bit-blasting
    t = Then('simplify', 'solve-eqs', 'bit-blast', 'tseitin-cnf')
    result = t(g)

    t_blast = time.time() - t0
    print(f"Bit-blasting took {t_blast:.1f}s")

    # Export to DIMACS
    # result is a list of subgoals, each containing clauses
    # We need to convert Z3's internal CNF to DIMACS format

    # Alternative: use Z3's DIMACS export directly
    dimacs_file = f"/tmp/sr{60 if n_free == 4 else 59}_reduced.cnf"

    # Use the solver's DIMACS output
    s = Solver()
    for c in constraints:
        s.add(c)

    # Z3 can export to DIMACS via the sat tactic
    print("Generating DIMACS file...")
    t_dimacs = Then('simplify', 'solve-eqs', 'bit-blast', 'tseitin-cnf')
    subgoals = t_dimacs(g)

    # Convert subgoals to DIMACS manually
    var_map = {}
    next_var = 1
    clauses = []

    for sg in subgoals:
        for clause_expr in sg:
            # Each clause_expr is a Z3 Boolean expression (already in CNF)
            clause = []
            if is_or(clause_expr):
                for lit in clause_expr.children():
                    if is_not(lit):
                        atom = lit.arg(0)
                        name = str(atom)
                        if name not in var_map:
                            var_map[name] = next_var
                            next_var += 1
                        clause.append(-var_map[name])
                    else:
                        name = str(lit)
                        if name not in var_map:
                            var_map[name] = next_var
                            next_var += 1
                        clause.append(var_map[name])
            elif is_not(clause_expr):
                atom = clause_expr.arg(0)
                name = str(atom)
                if name not in var_map:
                    var_map[name] = next_var
                    next_var += 1
                clause.append(-var_map[name])
            elif is_true(clause_expr):
                continue  # Skip tautologies
            elif is_false(clause_expr):
                clause.append(1)
                clause.append(-1)  # Empty clause = UNSAT
            else:
                name = str(clause_expr)
                if name not in var_map:
                    var_map[name] = next_var
                    next_var += 1
                clause.append(var_map[name])

            if clause:
                clauses.append(clause)

    n_vars = next_var - 1
    n_clauses = len(clauses)

    print(f"DIMACS: {n_vars} variables, {n_clauses} clauses")
    print(f"Writing to {dimacs_file}...")

    with open(dimacs_file, 'w') as f:
        f.write(f"p cnf {n_vars} {n_clauses}\n")
        for clause in clauses:
            f.write(" ".join(str(l) for l in clause) + " 0\n")

    print(f"File size: {os.path.getsize(dimacs_file) / 1024:.0f} KB")

    # Find free variable mappings for solution extraction
    free_var_names = []
    for i in range(n_free):
        for bit in range(32):
            name1 = f"w1_{57+i}"
            name2 = f"w2_{57+i}"
            # The bit-blasted names might be different; store what we can find

    return dimacs_file, n_vars, n_clauses, var_map, w1, w2


def run_kissat(dimacs_file, timeout_sec=7200):
    """Run kissat on the DIMACS file."""
    kissat_path = "kissat"

    print(f"\nRunning kissat on {dimacs_file} (timeout: {timeout_sec}s)...")
    t0 = time.time()

    try:
        result = subprocess.run(
            [kissat_path, "--time", str(timeout_sec), dimacs_file],
            capture_output=True, text=True, timeout=timeout_sec + 60
        )
        elapsed = time.time() - t0

        print(f"Kissat exited with code {result.returncode} in {elapsed:.1f}s")

        # Parse output
        lines = result.stdout.split('\n')
        for line in lines:
            if line.startswith('s '):
                print(f"Result: {line}")
            elif 'conflicts' in line.lower() or 'propagations' in line.lower():
                print(f"  {line.strip()}")

        if result.returncode == 10:
            print("\n[!!!] SATISFIABLE!")
            # Extract solution
            solution = {}
            for line in lines:
                if line.startswith('v '):
                    for lit in line[2:].split():
                        lit = int(lit)
                        if lit != 0:
                            solution[abs(lit)] = (lit > 0)
            return "sat", elapsed, solution
        elif result.returncode == 20:
            print("\nUNSATISFIABLE")
            return "unsat", elapsed, None
        else:
            print(f"\nUnknown result (timeout or error)")
            return "unknown", elapsed, None

    except subprocess.TimeoutExpired:
        elapsed = time.time() - t0
        print(f"\nTimeout after {elapsed:.1f}s")
        return "timeout", elapsed, None


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "sr60"
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 3600

    print("=" * 70)
    print(f"Reduced DIMACS CNF Generator + Kissat Solver")
    print(f"Mode: {mode}, Kissat timeout: {timeout}s")
    print("=" * 70)

    # First do sr=59 as baseline
    if mode == "both":
        print("\n--- BASELINE: sr=59 ---")
        cnf_59, nv59, nc59, _, _, _ = build_and_export_cnf("sr59")
        result_59, time_59, _ = run_kissat(cnf_59, timeout_sec=min(timeout, 600))

        print(f"\n--- TARGET: sr=60 ---")
        cnf_60, nv60, nc60, vm60, w1_60, w2_60 = build_and_export_cnf("sr60")
        result_60, time_60, sol60 = run_kissat(cnf_60, timeout_sec=timeout)

        print("\n" + "=" * 70)
        print("COMPARISON")
        print("=" * 70)
        print(f"  sr=59: {nv59} vars, {nc59} clauses -> {result_59} in {time_59:.1f}s")
        print(f"  sr=60: {nv60} vars, {nc60} clauses -> {result_60} in {time_60:.1f}s")
        speedup_ratio = nc59 / nc60 if nc60 > 0 else float('inf')
        print(f"  Clause ratio: {speedup_ratio:.2f}x")

    else:
        cnf_file, nv, nc, var_map, w1, w2 = build_and_export_cnf(mode)
        result, elapsed, solution = run_kissat(cnf_file, timeout_sec=timeout)

        if result == "sat" and mode == "sr60":
            print("\n[!!!] SR=60 SOLVED VIA REDUCED ENCODING + KISSAT!")


if __name__ == "__main__":
    main()
