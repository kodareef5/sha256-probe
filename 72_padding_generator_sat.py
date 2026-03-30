#!/usr/bin/env python3
"""
Script 72: SAT-Based Padding Generator for SHA-256 Collision Cryptanalysis

PROBLEM: The paper uses M[1..15] = 0xFFFFFFFF (lazy all-ones padding).
Our campaign showed this is UNSAT at sr=60. But M[1..15] has 480 bits
of freedom -- enough to reshape the Round 56 state completely.

APPROACH: Use Kissat to GENERATE optimal padding values for M[14] and M[15]
(64 bits of freedom) such that da[56] = 0 (and optionally db[56] = 0).

KEY INSIGHT: When M[14] and M[15] are SAT variables, the message schedule
W[14..56] becomes a SAT circuit (each W[i] depends on earlier W values
through sigma0, sigma1, and additions). All 57 rounds must be encoded.
Rounds 0-13 constant-fold completely since W[0..13] are fixed.

LEVELS:
  Level 1: da[56] = 0 only (32 bits constraint, 64 bits freedom = 32 bits slack)
  Level 2: da[56] = 0 AND db[56] = 0 (64 bits constraint, 0 slack)
  Level 3: da[56] = 0 AND minimize state diff hamming weight

Usage:
  python3 72_padding_generator_sat.py [level] [timeout]
  python3 72_padding_generator_sat.py 1 600
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')

# SHA-256 constants (reuse from encoder)
K = enc.K
IV = enc.IV

def ROR(x, n): return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF
def SHR(x, n): return x >> n
def sigma0_py(x): return ROR(x, 7) ^ ROR(x, 18) ^ SHR(x, 3)
def sigma1_py(x): return ROR(x, 17) ^ ROR(x, 19) ^ SHR(x, 10)
def Sigma0_py(a): return ROR(a, 2) ^ ROR(a, 13) ^ ROR(a, 22)
def Sigma1_py(e): return ROR(e, 6) ^ ROR(e, 11) ^ ROR(e, 25)
def Ch_py(e, f, g): return ((e & f) ^ ((~e) & g)) & 0xFFFFFFFF
def Maj_py(a, b, c): return (a & b) ^ (a & c) ^ (b & c)


def native_compress(M):
    """Full SHA-256 compression (57 rounds) in Python for verification."""
    W = list(M) + [0] * 48
    for i in range(16, 64):
        W[i] = (sigma1_py(W[i-2]) + W[i-7] + sigma0_py(W[i-15]) + W[i-16]) & 0xFFFFFFFF
    a, b, c, d, e, f, g, h = IV
    states = [(a, b, c, d, e, f, g, h)]
    for i in range(64):
        T1 = (h + Sigma1_py(e) + Ch_py(e, f, g) + K[i] + W[i]) & 0xFFFFFFFF
        T2 = (Sigma0_py(a) + Maj_py(a, b, c)) & 0xFFFFFFFF
        h = g; g = f; f = e; e = (d + T1) & 0xFFFFFFFF
        d = c; c = b; b = a; a = (T1 + T2) & 0xFFFFFFFF
        states.append((a, b, c, d, e, f, g, h))
    return states, W


def encode_padding_search(m0=0x17149975, fixed_m=None, level=1,
                          block_solutions=None, free_indices=None,
                          fix_bits=None):
    """
    Encode the full 57-round SHA-256 compression as SAT with specified M words
    as free variables.

    m0: fixed M[0] value
    fixed_m: dict mapping M indices 1..15 to fixed values (default: all 0xFFFFFFFF)
    level: 1 = da[56]=0, 2 = da[56]=db[56]=0
    block_solutions: list of dicts {idx: value} to block
    free_indices: list of M[] indices to make free (default: [14, 15])
    fix_bits: dict {(idx, bit): bool_value} to pin specific bits of free words

    Returns: (cnf, free_var_map, state1, state2)
    """
    if fixed_m is None:
        fixed_m = {i: 0xFFFFFFFF for i in range(1, 16)}
    if block_solutions is None:
        block_solutions = []
    if free_indices is None:
        free_indices = [14, 15]
    if fix_bits is None:
        fix_bits = {}

    cnf = enc.CNFBuilder()

    # ===== MESSAGE WORDS =====
    M_words = [None] * 16
    M_words[0] = cnf.const_word(m0)
    for i in range(1, 16):
        if i in free_indices:
            M_words[i] = cnf.free_word(f"M{i}")
        else:
            M_words[i] = cnf.const_word(fixed_m[i])

    # Pin specific bits of free words
    for (idx, bit), val in fix_bits.items():
        if idx in free_indices:
            name = f"M{idx}[{bit}]"
            for var_id, var_name in cnf.free_var_names.items():
                if var_name == name:
                    cnf.clauses.append([var_id if val else -var_id])
                    break

    # ===== MESSAGE SCHEDULE W[0..56] =====
    # W[0..15] = M[0..15] directly
    # W[16..56] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]
    #
    # Since M[14] and M[15] are free, W[14..56] will be SAT circuits.
    # W[0..13] are constants and will be constant-folded.

    W = [None] * 57
    for i in range(16):
        W[i] = M_words[i]

    print("Encoding message schedule W[16..56]...")
    t_sched = time.time()
    for i in range(16, 57):
        # W[i] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]
        s1 = cnf.sigma1_w(W[i-2])
        s0 = cnf.sigma0_w(W[i-15])
        # 4-input addition via CSA: reduce (s1, W[i-7], s0, W[i-16]) to result
        # Use 2 CSA layers + ripple, or just sequential adds
        # CSA approach: CSA(s1, W[i-7], s0) -> (sum1, carry1), then add carry1+sum1+W[i-16]
        # Actually simpler: use add5_csa with a zero, or just chain adds
        sum1, carry1 = cnf.csa_layer(s1, W[i-7], s0)
        sum2, carry2 = cnf.csa_layer(sum1, carry1, W[i-16])
        W[i] = cnf.add_word(sum2, carry2)

        if i % 10 == 0 or i == 56:
            nv = cnf.next_var - 1
            nc = len(cnf.clauses)
            print(f"  W[{i:2d}]: {nv:6d} vars, {nc:7d} clauses")

    t_sched_done = time.time() - t_sched
    print(f"  Schedule encoding: {t_sched_done:.1f}s")

    # ===== ENCODE 57 ROUNDS FOR MESSAGE 1 =====
    # M1 = [m0, fixed_m[1..13], M14, M15]
    # State starts from IV
    print("\nEncoding 57 compression rounds for message 1...")
    t_rounds = time.time()
    state1 = tuple(cnf.const_word(v) for v in IV)
    for i in range(57):
        state1 = cnf.sha256_round_correct(state1, K[i], W[i])
        if i % 10 == 0 or i == 56:
            nv = cnf.next_var - 1
            nc = len(cnf.clauses)
            print(f"  Round {i:2d}: {nv:6d} vars, {nc:7d} clauses")

    # ===== MESSAGE 2: MSB kernel =====
    # M2[0] = M1[0] ^ 0x80000000
    # M2[9] = M1[9] ^ 0x80000000
    # M2[i] = M1[i] for all other i
    # So M2[0] = const, M2[9] = const (0xFFFFFFFF ^ 0x80000000 = 0x7FFFFFFF)
    # M2[14] = M1[14] (same free vars), M2[15] = M1[15] (same free vars)
    # BUT the schedule is DIFFERENT because M2[0] and M2[9] differ

    M2_words = list(M_words)  # shallow copy - free words point to SAME bit arrays
    M2_words[0] = cnf.const_word(m0 ^ 0x80000000)
    # MSB kernel: M2[9] = M1[9] ^ 0x80000000
    if 9 in free_indices:
        # If M[9] is free, XOR its MSB via SAT (flip bit 31)
        m9_bits = list(M_words[9])
        m9_bits[31] = cnf.xor2(m9_bits[31], cnf._const(True))
        M2_words[9] = m9_bits
    else:
        M2_words[9] = cnf.const_word(fixed_m.get(9, 0xFFFFFFFF) ^ 0x80000000)

    W2 = [None] * 57
    for i in range(16):
        W2[i] = M2_words[i]

    print("\nEncoding message 2 schedule W2[16..56]...")
    t_sched2 = time.time()
    for i in range(16, 57):
        s1 = cnf.sigma1_w(W2[i-2])
        s0 = cnf.sigma0_w(W2[i-15])
        sum1, carry1 = cnf.csa_layer(s1, W2[i-7], s0)
        sum2, carry2 = cnf.csa_layer(sum1, carry1, W2[i-16])
        W2[i] = cnf.add_word(sum2, carry2)

        if i % 10 == 0 or i == 56:
            nv = cnf.next_var - 1
            nc = len(cnf.clauses)
            print(f"  W2[{i:2d}]: {nv:6d} vars, {nc:7d} clauses")
    t_sched2_done = time.time() - t_sched2
    print(f"  Schedule 2 encoding: {t_sched2_done:.1f}s")

    print("\nEncoding 57 compression rounds for message 2...")
    state2 = tuple(cnf.const_word(v) for v in IV)
    for i in range(57):
        state2 = cnf.sha256_round_correct(state2, K[i], W2[i])
        if i % 10 == 0 or i == 56:
            nv = cnf.next_var - 1
            nc = len(cnf.clauses)
            print(f"  Round {i:2d}: {nv:6d} vars, {nc:7d} clauses")

    t_rounds_done = time.time() - t_rounds
    print(f"  Round encoding: {t_rounds_done:.1f}s")

    # ===== CONSTRAINTS =====
    print("\nAdding constraints...")

    # Level 1: da[56] = 0 => state1[0] == state2[0] (the 'a' register)
    print("  Level 1: da[56] = 0 (a-register equality)")
    cnf.eq_word(state1[0], state2[0])

    if level >= 2:
        # Level 2: also db[56] = 0 => state1[1] == state2[1]
        print("  Level 2: db[56] = 0 (b-register equality)")
        cnf.eq_word(state1[1], state2[1])

    # Build var map for solution extraction (needed for blocking clauses too)
    var_map = {}
    for var_id, name in cnf.free_var_names.items():
        var_map[name] = var_id

    # ===== BLOCKING CLAUSES =====
    # Each blocked solution is a dict {idx: value} for free indices
    for sol_dict in block_solutions:
        blocking = []
        for idx in free_indices:
            if idx in sol_dict:
                val = sol_dict[idx]
                for bit in range(32):
                    name = f"M{idx}[{bit}]"
                    if name in var_map:
                        vid = var_map[name]
                        if (val >> bit) & 1:
                            blocking.append(-vid)
                        else:
                            blocking.append(vid)
        if blocking:
            cnf.clauses.append(blocking)
            desc = ", ".join(f"M{idx}=0x{sol_dict.get(idx, 0):08x}" for idx in free_indices if idx in sol_dict)
            print(f"  Blocked: {desc}")

    # ===== FINAL STATS =====
    nv = cnf.next_var - 1
    nc = len(cnf.clauses)
    print(f"\nFinal encoding:")
    print(f"  Variables:     {nv:,}")
    print(f"  Clauses:       {nc:,}")
    print(f"  XOR gates:     {cnf.stats['xor']:,}")
    print(f"  MUX gates:     {cnf.stats['mux']:,}")
    print(f"  MAJ gates:     {cnf.stats['maj']:,}")
    print(f"  Full adders:   {cnf.stats['fa']:,}")
    print(f"  Constant folds: {cnf.stats['const_fold']:,}")

    return cnf, var_map, state1, state2


def extract_word_from_solution(solution, var_map, prefix):
    """Extract a 32-bit word from SAT solution given variable name prefix (e.g., 'M14')."""
    val = 0
    for bit in range(32):
        name = f"{prefix}[{bit}]"
        if name in var_map:
            var_id = var_map[name]
            if var_id in solution and solution[var_id]:
                val |= (1 << bit)
    return val


def verify_solution(m0, sol_dict, base_m):
    """
    Verify that found M[] values give da[56]=0.
    sol_dict: {index: value} for free message words
    base_m: {index: value} for all fixed message words (1..15)
    """
    M1 = [m0]
    for i in range(1, 16):
        if i in sol_dict:
            M1.append(sol_dict[i])
        else:
            M1.append(base_m.get(i, 0xFFFFFFFF))

    M2 = list(M1)
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    states1, W1 = native_compress(M1)
    states2, W2 = native_compress(M2)

    s1_57 = states1[57]
    s2_57 = states2[57]

    da = (s1_57[0] - s2_57[0]) & 0xFFFFFFFF
    db = (s1_57[1] - s2_57[1]) & 0xFFFFFFFF

    print(f"\n{'='*70}")
    print("VERIFICATION (native Python SHA-256)")
    print(f"{'='*70}")
    print(f"  M[0]  = 0x{m0:08x}")
    for idx in sorted(sol_dict.keys()):
        print(f"  M[{idx}] = 0x{sol_dict[idx]:08x}  (found by SAT)")
    print(f"\n  State after round 56 (message 1):")
    print(f"    a = 0x{s1_57[0]:08x}  b = 0x{s1_57[1]:08x}  c = 0x{s1_57[2]:08x}  d = 0x{s1_57[3]:08x}")
    print(f"    e = 0x{s1_57[4]:08x}  f = 0x{s1_57[5]:08x}  g = 0x{s1_57[6]:08x}  h = 0x{s1_57[7]:08x}")
    print(f"\n  State after round 56 (message 2):")
    print(f"    a = 0x{s2_57[0]:08x}  b = 0x{s2_57[1]:08x}  c = 0x{s2_57[2]:08x}  d = 0x{s2_57[3]:08x}")
    print(f"    e = 0x{s2_57[4]:08x}  f = 0x{s2_57[5]:08x}  g = 0x{s2_57[6]:08x}  h = 0x{s2_57[7]:08x}")

    print(f"\n  da[56] = 0x{da:08x}  {'== 0 PASS' if da == 0 else '!= 0 FAIL'}")
    print(f"  db[56] = 0x{db:08x}  {'== 0 PASS' if db == 0 else ''}")

    reg_names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    total_hw = 0
    print(f"\n  Full state diff at round 56:")
    for j in range(8):
        diff = s1_57[j] ^ s2_57[j]
        hw = bin(diff).count('1')
        total_hw += hw
        print(f"    d{reg_names[j]}[56] XOR = 0x{diff:08x}  (HW={hw:2d})")
    print(f"    Total XOR Hamming weight: {total_hw}/256")

    # Compare against all-ones reference
    M1_ref = [m0] + [0xFFFFFFFF] * 15
    M2_ref = list(M1_ref); M2_ref[0] ^= 0x80000000; M2_ref[9] ^= 0x80000000
    s1_ref, _ = native_compress(M1_ref)
    s2_ref, _ = native_compress(M2_ref)
    s1r = s1_ref[57]; s2r = s2_ref[57]
    ref_hw = sum(bin(s1r[j] ^ s2r[j]).count('1') for j in range(8))
    print(f"\n  Reference (all-ones padding) XOR HW: {ref_hw}/256")
    if total_hw < ref_hw:
        print(f"  IMPROVEMENT: {ref_hw - total_hw} fewer diff bits!")
    elif total_hw == ref_hw:
        print(f"  Same as reference.")
    else:
        print(f"  Worse by {total_hw - ref_hw} bits.")

    return da == 0, total_hw


def solve_one(cnf_file, timeout, var_map, free_indices, seed=0):
    """Run Kissat on a CNF file and extract solution if SAT."""
    try:
        t_solve_start = time.time()
        cmd = ["timeout", str(timeout), "kissat", "--quiet"]
        if seed > 0:
            cmd += [f"--seed={seed}"]
        cmd.append(cnf_file)
        result = subprocess.run(
            cmd,
            capture_output=True, text=True, timeout=timeout + 60
        )
        t_solve = time.time() - t_solve_start

        lines = result.stdout.split('\n')
        sat_line = [l for l in lines if l.startswith('s ')]

        status = "UNKNOWN"
        if result.returncode == 10:
            status = "SAT"
        elif result.returncode == 20:
            status = "UNSAT"
        else:
            status = "TIMEOUT"

        if sat_line:
            print(f"  Result: {sat_line[0]}  ({t_solve:.1f}s)")
        else:
            print(f"  Result: {status}  ({t_solve:.1f}s)")

        if status == "SAT":
            solution = {}
            for line in lines:
                if line.startswith('v '):
                    for lit in line[2:].split():
                        lit_val = int(lit)
                        if lit_val != 0:
                            solution[abs(lit_val)] = (lit_val > 0)
            sol_dict = {}
            for idx in free_indices:
                sol_dict[idx] = extract_word_from_solution(solution, var_map, f"M{idx}")
            return status, t_solve, sol_dict

        return status, t_solve, None

    except subprocess.TimeoutExpired:
        return "TIMEOUT", timeout, None
    except FileNotFoundError:
        print("  kissat not found!")
        return "ERROR", 0, None


def brute_force_m15(m0, fixed_m):
    """
    Brute-force all 2^32 values of M[15] to find which ones give da[56]=0.
    This is fast because we can precompute most of the schedule and state.
    """
    import struct

    # Build base message
    M_base = [m0]
    for i in range(1, 16):
        M_base.append(fixed_m.get(i, 0xFFFFFFFF))

    # Precompute W[0..14] and partial schedule
    # W[15] = M[15] (variable)
    # W[16] = sigma1(W[14]) + W[9] + sigma0(W[1]) + W[0]  -- W[14] is constant
    # W[17] = sigma1(W[15]) + W[10] + sigma0(W[2]) + W[1]  -- depends on W[15]

    hits = []
    print("Brute-forcing all 2^32 values of M[15]...")
    t0 = time.time()

    # Precompute things that don't depend on M[15]
    W_const = list(M_base[:16])  # W[0..15], where W[15] will be overridden

    for m15 in range(0, 0x100000000, 1):
        if m15 % 0x10000000 == 0:
            elapsed = time.time() - t0
            rate = m15 / elapsed if elapsed > 0 else 0
            print(f"  Progress: {m15 >> 28}/16  ({rate:.0f} vals/s)  hits: {len(hits)}")

        W_const[15] = m15
        W = list(W_const)
        for i in range(16, 57):
            W.append((sigma1_py(W[i-2]) + W[i-7] + sigma0_py(W[i-15]) + W[i-16]) & 0xFFFFFFFF)

        # Compress message 1
        a, b, c, d, e, f, g, h = IV
        for i in range(57):
            T1 = (h + Sigma1_py(e) + Ch_py(e, f, g) + K[i] + W[i]) & 0xFFFFFFFF
            T2 = (Sigma0_py(a) + Maj_py(a, b, c)) & 0xFFFFFFFF
            h = g; g = f; f = e; e = (d + T1) & 0xFFFFFFFF
            d = c; c = b; b = a; a = (T1 + T2) & 0xFFFFFFFF
        a1 = a

        # Message 2 schedule
        M2 = list(M_base)
        M2[0] ^= 0x80000000
        M2[9] ^= 0x80000000
        M2[15] = m15
        W2 = list(M2[:16])
        for i in range(16, 57):
            W2.append((sigma1_py(W2[i-2]) + W2[i-7] + sigma0_py(W2[i-15]) + W2[i-16]) & 0xFFFFFFFF)

        a2, b2, c2, d2, e2, f2, g2, h2 = IV
        for i in range(57):
            T1 = (h2 + Sigma1_py(e2) + Ch_py(e2, f2, g2) + K[i] + W2[i]) & 0xFFFFFFFF
            T2 = (Sigma0_py(a2) + Maj_py(a2, b2, c2)) & 0xFFFFFFFF
            h2 = g2; g2 = f2; f2 = e2; e2 = (d2 + T1) & 0xFFFFFFFF
            d2 = c2; c2 = b2; b2 = a2; a2 = (T1 + T2) & 0xFFFFFFFF

        if a1 == a2:
            hits.append(m15)
            if len(hits) <= 20:
                print(f"  HIT: M[15] = 0x{m15:08x}  (a1=a2=0x{a1:08x})")

    elapsed = time.time() - t0
    return hits, elapsed


def main():
    level = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 120
    mode = sys.argv[3] if len(sys.argv) > 3 else "sat"

    m0 = 0x17149975
    fixed_m = {i: 0xFFFFFFFF for i in range(1, 16)}
    free_indices = [15]

    print("=" * 70)
    print(f"SAT-Based Padding Generator (Level {level}, mode={mode})")
    print("=" * 70)

    if mode == "brute":
        # Pure brute force over M[15] -- reference check
        hits, elapsed = brute_force_m15(m0, fixed_m)
        print(f"\nBrute force complete: {len(hits)} hits in {elapsed:.1f}s")
        for m15 in hits[:10]:
            sol_dict = {15: m15}
            verify_solution(m0, sol_dict, fixed_m)
        return

    # SAT mode: fix top N bits of M[15] to create tractable sub-problems
    # With 8 free bits (fix top 24), each probe is ~91K vars but only 8 bits
    # of real freedom. Should solve instantly if SAT.

    # Actually, try fixing top 8 bits = 256 probes, each with 24 bits freedom
    # 24 bits freedom vs 32 bits constraint = 8 bits over, ~1/256 hit rate
    # So in 256 probes we expect ~1 hit

    n_fixed_bits = 8  # fix top 8 bits of M[15]
    n_probes = 1 << n_fixed_bits  # 256
    n_free_bits = 32 - n_fixed_bits  # 24 bits remain free

    print(f"  M[0]     = 0x{m0:08x} (fixed)")
    print(f"  M[1..14] = 0xFFFFFFFF (fixed)")
    print(f"  M[15]    = top {n_fixed_bits} bits fixed, bottom {n_free_bits} bits free")
    print(f"  Probes   = {n_probes}")
    print(f"  Freedom per probe = {n_free_bits} bits")
    print(f"  Constraint = 32 bits (da[56]=0)")
    if n_free_bits < 32:
        print(f"  Over-constrained by {32 - n_free_bits} bits per probe")
    print(f"  Timeout  = {timeout}s per probe")
    print()

    found_solutions = []
    best_hw = 999
    best_solution = None
    sat_count = 0
    unsat_count = 0
    timeout_count = 0

    for probe in range(n_probes):
        # Fix top n_fixed_bits of M[15]
        fix_bits = {}
        for bit in range(n_fixed_bits):
            bit_pos = 31 - bit  # MSB first
            fix_bits[(15, bit_pos)] = bool((probe >> (n_fixed_bits - 1 - bit)) & 1)

        top_val = probe << n_free_bits
        top_hex = f"0x{top_val:08x}"

        if probe % 16 == 0:
            print(f"  Probe {probe:3d}/{n_probes}: M[15] top={top_hex}  "
                  f"[SAT:{sat_count} UNSAT:{unsat_count} TO:{timeout_count}]")

        t_enc_start = time.time()
        cnf, var_map, state1, state2 = encode_padding_search(
            m0, fixed_m, level,
            free_indices=free_indices,
            fix_bits=fix_bits
        )
        t_enc = time.time() - t_enc_start

        cnf_file = f"/tmp/72_probe.cnf"
        nv, nc = cnf.write_dimacs(cnf_file)

        status, t_solve, sol_dict = solve_one(cnf_file, timeout, var_map, free_indices)

        if status == "SAT" and sol_dict is not None:
            sat_count += 1
            m15_found = sol_dict[15]
            found_solutions.append(sol_dict)

            # Verify and get HW
            ok, hw = verify_solution(m0, sol_dict, fixed_m)
            if ok:
                print(f"  ** HIT #{sat_count}: M[15]=0x{m15_found:08x}  HW={hw}/256")
                if hw < best_hw:
                    best_hw = hw
                    best_solution = sol_dict
                    print(f"     NEW BEST!")
            else:
                print(f"  ** HIT but VERIFICATION FAILED for M[15]=0x{m15_found:08x}")

        elif status == "UNSAT":
            unsat_count += 1
        else:
            timeout_count += 1

    # ===== SUMMARY =====
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    print(f"  Probes: {n_probes}")
    print(f"  SAT: {sat_count}  UNSAT: {unsat_count}  Timeout: {timeout_count}")
    print(f"  Solutions found: {len(found_solutions)}")

    if found_solutions:
        print(f"\n  All solutions:")
        for idx_s, sol_dict in enumerate(found_solutions):
            M1 = [m0]
            for i in range(1, 16):
                M1.append(sol_dict.get(i, fixed_m[i]))
            M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
            s1, _ = native_compress(M1)
            s2, _ = native_compress(M2)
            hw = sum(bin(s1[57][j] ^ s2[57][j]).count('1') for j in range(8))
            marker = " <-- BEST" if sol_dict is best_solution else ""
            print(f"    #{idx_s+1}: M[15]=0x{sol_dict[15]:08x}  HW={hw}/256{marker}")

        if best_solution:
            print(f"\n  Best padding (lowest state diff HW at round 56):")
            print(f"    M[15] = 0x{best_solution[15]:08x}")
            print(f"    XOR HW: {best_hw}/256")

            print(f"\n  Full message block:")
            for i in range(16):
                if i == 0:
                    val = m0
                else:
                    val = best_solution.get(i, fixed_m.get(i, 0))
                print(f"    M[{i:2d}] = 0x{val:08x}")
    else:
        print("  No solutions found in any probe.")


if __name__ == "__main__":
    main()
