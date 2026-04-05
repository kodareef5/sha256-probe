#!/usr/bin/env python3
"""
Script 71: MITM Bit-Level Breakdown of the 8th Register Bottleneck

Prior result from 66c_partial_anchor.py:
  - Matching 7/8 registers (224 bits) at the Round 60 anchor: SAT in ~291s
  - Matching 8/8 registers (256 bits): TIMEOUT at 300s
  - The transition from solvable to intractable lives in register 7 (h60)

THIS EXPERIMENT: Take the 7-register baseline and add PARTIAL matching
of register 7 (the 8th register, index h), bit by bit:
  - 224 + 0  bits = 7 regs only (baseline, ~291s)
  - 224 + 8  bits = 7 regs + first 8 bits of reg 7
  - 224 + 16 bits = 7 regs + first 16 bits of reg 7
  - 224 + 24 bits = 7 regs + first 24 bits of reg 7
  - 224 + 32 bits = 7 regs + all 32 bits of reg 7 = full 256 bits

Also test TOP bits (MSBs) of register 7 instead of bottom bits (LSBs),
since SHA-256 carry propagation might make MSBs harder.

This reveals whether the obstruction is:
  (a) concentrated in specific bits (MSBs vs LSBs)
  (b) uniformly distributed across the register
  (c) threshold-dependent (fine up to N bits, then explodes)
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')

# Local SHA-256 helpers
def ROR(x, n): return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF
def sigma0_py(x): return ROR(x, 7) ^ ROR(x, 18) ^ (x >> 3)
def sigma1_py(x): return ROR(x, 17) ^ ROR(x, 19) ^ (x >> 10)


def eq_specific_bits(cnf, A, B, bit_indices):
    """
    Constrain specific bits of two 32-bit words to be equal.
    A and B are bit arrays (LSB-first, length 32).
    bit_indices is a list of bit positions (0-31) to constrain.
    """
    for i in bit_indices:
        a, b = A[i], B[i]
        if cnf._is_known(a) and cnf._is_known(b):
            if cnf._get_val(a) != cnf._get_val(b):
                cnf.clauses.append([])  # UNSAT
            continue
        if cnf._is_known(a):
            cnf.clauses.append([b] if cnf._get_val(a) else [-b])
            continue
        if cnf._is_known(b):
            cnf.clauses.append([a] if cnf._get_val(b) else [-a])
            continue
        cnf.clauses.append([-a, b])
        cnf.clauses.append([a, -b])


def encode_with_partial_reg7(n_bits_reg7, bit_end="lsb", m0=0x17149975):
    """
    Encode the split sr=60 problem:
      - Full match on registers 0-6 (224 bits)
      - Partial match on register 7: n_bits_reg7 bits

    bit_end controls WHICH bits of register 7 are matched:
      "lsb" -> match bits 0..n_bits_reg7-1 (lowest bits first)
      "msb" -> match bits (32-n_bits_reg7)..31 (highest bits first)
    """
    # Build the two messages (MSB kernel)
    M1 = [m0] + [0xffffffff] * 15
    M2 = M1[:]
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    # Precompute state through round 56 and schedule through W[56]
    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    cnf = enc.CNFBuilder()

    # ===== FORWARD HALF: rounds 57-60 =====
    s1_fwd = tuple(cnf.const_word(v) for v in state1)
    s2_fwd = tuple(cnf.const_word(v) for v in state2)

    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

    fwd_st1 = s1_fwd
    for i in range(4):
        fwd_st1 = cnf.sha256_round_correct(fwd_st1, enc.K[57 + i], w1_free[i])

    fwd_st2 = s2_fwd
    for i in range(4):
        fwd_st2 = cnf.sha256_round_correct(fwd_st2, enc.K[57 + i], w2_free[i])

    # ===== BACKWARD HALF: rounds 61-63 =====
    anc1 = tuple(cnf.free_word(f"anc1_{i}") for i in range(8))
    anc2 = tuple(cnf.free_word(f"anc2_{i}") for i in range(8))

    # Derive schedule words W[61..63] from forward half free Ws
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45]))
    )
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45]))
    )

    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[3]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46]))
    )
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[3]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46]))
    )

    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_61), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47]))
    )
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_61), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47]))
    )

    # Run 3 backward rounds (61, 62, 63) from anchor
    bwd_st1 = anc1
    bwd_st1 = cnf.sha256_round_correct(bwd_st1, enc.K[61], w1_61)
    bwd_st1 = cnf.sha256_round_correct(bwd_st1, enc.K[62], w1_62)
    bwd_st1 = cnf.sha256_round_correct(bwd_st1, enc.K[63], w1_63)

    bwd_st2 = anc2
    bwd_st2 = cnf.sha256_round_correct(bwd_st2, enc.K[61], w2_61)
    bwd_st2 = cnf.sha256_round_correct(bwd_st2, enc.K[62], w2_62)
    bwd_st2 = cnf.sha256_round_correct(bwd_st2, enc.K[63], w2_63)

    # ===== COLLISION CONSTRAINT =====
    for i in range(8):
        cnf.eq_word(bwd_st1[i], bwd_st2[i])

    # ===== ANCHOR MATCHING =====
    # Match registers 0-6 fully (224 bits)
    for reg in range(7):
        cnf.eq_word(fwd_st1[reg], anc1[reg])
        cnf.eq_word(fwd_st2[reg], anc2[reg])

    # Partial match on register 7 (the 8th register, h60)
    if n_bits_reg7 > 0:
        if bit_end == "lsb":
            # Match bits 0, 1, ..., n_bits_reg7-1 (LSBs first)
            bit_indices = list(range(n_bits_reg7))
        elif bit_end == "msb":
            # Match bits 31, 30, ..., 32-n_bits_reg7 (MSBs first)
            bit_indices = list(range(32 - n_bits_reg7, 32))
        else:
            raise ValueError(f"Unknown bit_end: {bit_end}")

        eq_specific_bits(cnf, fwd_st1[7], anc1[7], bit_indices)
        eq_specific_bits(cnf, fwd_st2[7], anc2[7], bit_indices)

    return cnf


def run_one(n_bits_reg7, bit_end, timeout_sec):
    """Encode and solve one configuration."""
    t_enc_start = time.time()
    cnf = encode_with_partial_reg7(n_bits_reg7, bit_end)
    t_enc = time.time() - t_enc_start

    nv = cnf.next_var - 1
    nc = len(cnf.clauses)

    label = f"reg7_{bit_end}{n_bits_reg7}"
    cnf_file = f"/tmp/71_mitm_{label}.cnf"
    cnf.write_dimacs(cnf_file)

    t_solve_start = time.time()
    try:
        r = subprocess.run(
            ["timeout", str(timeout_sec), "kissat", cnf_file],
            capture_output=True, text=True, timeout=timeout_sec + 30
        )
        t_solve = time.time() - t_solve_start

        if r.returncode == 10:
            result = "SAT"
        elif r.returncode == 20:
            result = "UNSAT"
        else:
            result = "TIMEOUT"
    except subprocess.TimeoutExpired:
        t_solve = timeout_sec
        result = "TIMEOUT"

    return result, t_enc, t_solve, nv, nc


def main():
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 600

    print("=" * 85, flush=True)
    print("71: MITM BIT-LEVEL BREAKDOWN OF 8TH REGISTER (h60) BOTTLENECK", flush=True)
    print("=" * 85, flush=True)
    print(flush=True)
    print("Baseline: 7 registers (0-6) fully matched = 224 bits, SAT in ~291s", flush=True)
    print("Question: How does adding bits from register 7 (h60) affect solvability?", flush=True)
    print(f"Timeout per instance: {timeout}s", flush=True)
    print(flush=True)

    def run_phase(phase_name, bit_end, points):
        """Run a phase with early termination after 2 consecutive timeouts."""
        print("-" * 85, flush=True)
        print(f"{phase_name}", flush=True)
        print("-" * 85, flush=True)
        print(f"{'reg7_bits':>10} {'total_bits':>11} {'end':>5} {'vars':>8} {'clauses':>10} {'enc_t':>7} {'result':>8} {'solve_t':>9}", flush=True)
        print("-" * 85, flush=True)

        results = []
        consecutive_timeouts = 0
        for nb in points:
            if consecutive_timeouts >= 2:
                print(f"{nb:10d} {224+nb:11d} {bit_end.upper():>5}     (skipped -- 2 consecutive timeouts)", flush=True)
                results.append((nb, 224+nb, bit_end.upper(), "SKIPPED", timeout, 0, 0))
                continue

            total = 224 + nb
            result, t_enc, t_solve, nv, nc = run_one(nb, bit_end, timeout)
            print(f"{nb:10d} {total:11d} {bit_end.upper():>5} {nv:8d} {nc:10d} {t_enc:6.1f}s {result:>8} {t_solve:8.1f}s", flush=True)
            results.append((nb, total, bit_end.upper(), result, t_solve, nv, nc))

            if result == "TIMEOUT":
                consecutive_timeouts += 1
            else:
                consecutive_timeouts = 0

        return results

    # ===== PRIOR RESULTS (from previous run) =====
    prior_lsb = [
        (0,  224, "LSB", "SAT", 294.9, 11500, 47151),
        (4,  228, "LSB", "SAT", 436.0, 11500, 47167),
        (8,  232, "LSB", "SAT", 464.8, 11500, 47183),
    ]
    print("-" * 85, flush=True)
    print("PRIOR RESULTS (from previous run):", flush=True)
    print("-" * 85, flush=True)
    print(f"{'reg7_bits':>10} {'total_bits':>11} {'end':>5} {'vars':>8} {'clauses':>10} {'enc_t':>7} {'result':>8} {'solve_t':>9}", flush=True)
    print("-" * 85, flush=True)
    for nb, total, end, result, t_solve, nv, nc in prior_lsb:
        print(f"{nb:10d} {total:11d} {end:>5} {nv:8d} {nc:10d}   (prior) {result:>8} {t_solve:8.1f}s", flush=True)
    print(flush=True)

    # ===== PHASE 1: LSB-first matching of register 7 =====
    # We know 0,4,8 are SAT. Test 10, 12, 16, 20, 24, 32 to find transition.
    lsb_points = [10, 12, 16, 20, 24, 32]
    lsb_new = run_phase(
        "PHASE 1: Match LSBs of register 7 (remaining points: 10, 12, 16, 20, 24, 32)",
        "lsb", lsb_points
    )
    lsb_results = prior_lsb + lsb_new

    # ===== PHASE 2: MSB-first matching of register 7 =====
    print(flush=True)
    msb_points = [4, 8, 12, 16, 24, 32]
    msb_results = run_phase(
        "PHASE 2: Match MSBs of register 7 (bits 31, 30, 29, ... from top)",
        "msb", msb_points
    )

    # ===== SUMMARY =====
    print(flush=True)
    print("=" * 85, flush=True)
    print("SUMMARY TABLE", flush=True)
    print("=" * 85, flush=True)
    print(flush=True)
    print(f"{'reg7_bits':>10} {'total':>6} {'end':>5} {'result':>8} {'time':>9}  visual", flush=True)
    print("-" * 70, flush=True)

    all_results = lsb_results + msb_results
    # Sort for display: LSB first, then MSB, each by bit count
    for nb, total, end, result, t_solve, nv, nc in lsb_results:
        bar_len = min(int(t_solve / 10), 40)
        bar = "#" * bar_len
        if result == "TIMEOUT":
            bar += " >>TIMEOUT"
        print(f"{nb:10d} {total:6d} {end:>5} {result:>8} {t_solve:8.1f}s  {bar}", flush=True)

    print(flush=True)
    for nb, total, end, result, t_solve, nv, nc in msb_results:
        bar_len = min(int(t_solve / 10), 40)
        bar = "#" * bar_len
        if result == "TIMEOUT":
            bar += " >>TIMEOUT"
        print(f"{nb:10d} {total:6d} {end:>5} {result:>8} {t_solve:8.1f}s  {bar}", flush=True)

    # ===== ANALYSIS =====
    print(flush=True)
    print("=" * 85, flush=True)
    print("ANALYSIS", flush=True)
    print("=" * 85, flush=True)
    print(flush=True)

    # Find transition points
    def find_transition(results):
        last_sat = None
        first_hard = None
        for nb, total, end, result, t_solve, nv, nc in results:
            if result == "SAT":
                last_sat = nb
            elif result in ("TIMEOUT", "UNSAT") and first_hard is None:
                first_hard = nb
        return last_sat, first_hard

    lsb_last_sat, lsb_first_hard = find_transition(lsb_results)
    msb_last_sat, msb_first_hard = find_transition(msb_results)

    print(f"LSB-first matching:", flush=True)
    if lsb_last_sat is not None:
        print(f"  Last SAT:       {lsb_last_sat} bits of reg 7 ({224+lsb_last_sat} total)", flush=True)
    if lsb_first_hard is not None:
        print(f"  First TIMEOUT:  {lsb_first_hard} bits of reg 7 ({224+lsb_first_hard} total)", flush=True)
    else:
        print(f"  No timeout (all SAT within {timeout}s!)", flush=True)

    print(flush=True)
    print(f"MSB-first matching:", flush=True)
    if msb_last_sat is not None:
        print(f"  Last SAT:       {msb_last_sat} bits of reg 7 ({224+msb_last_sat} total)", flush=True)
    if msb_first_hard is not None:
        print(f"  First TIMEOUT:  {msb_first_hard} bits of reg 7 ({224+msb_first_hard} total)", flush=True)
    else:
        print(f"  No timeout (all SAT within {timeout}s!)", flush=True)

    print(flush=True)
    # Compare LSB vs MSB
    if lsb_first_hard and msb_first_hard:
        if lsb_first_hard > msb_first_hard:
            print("FINDING: MSBs are harder than LSBs.", flush=True)
            print(f"  LSBs tolerate {lsb_first_hard} extra bits; MSBs only {msb_first_hard}.", flush=True)
            print("  -> Carry propagation makes high bits more constrained.", flush=True)
        elif msb_first_hard > lsb_first_hard:
            print("FINDING: LSBs are harder than MSBs.", flush=True)
            print(f"  MSBs tolerate {msb_first_hard} extra bits; LSBs only {lsb_first_hard}.", flush=True)
            print("  -> Low-order bits carry more constraint weight.", flush=True)
        else:
            print("FINDING: LSBs and MSBs equally hard.", flush=True)
            print("  -> Difficulty uniformly distributed across register 7.", flush=True)
    elif lsb_first_hard is None and msb_first_hard is None:
        print("FINDING: ALL configurations solved within timeout!", flush=True)
        print("  -> Register 7 is NOT the bottleneck at this timeout.", flush=True)
        print("  -> The 66c timeout at 300s was likely just marginal.", flush=True)

    # Time scaling analysis
    print(flush=True)
    print("TIME SCALING (LSB):", flush=True)
    for i in range(1, len(lsb_results)):
        nb0, _, _, res0, t0, _, _ = lsb_results[i-1]
        nb1, _, _, res1, t1, _, _ = lsb_results[i]
        if res0 == "SAT" and res1 == "SAT" and t0 > 0.1:
            ratio = t1 / t0
            print(f"  {nb0} -> {nb1} bits: {t0:.1f}s -> {t1:.1f}s  (x{ratio:.2f})", flush=True)

    print(flush=True)
    print("TIME SCALING (MSB):", flush=True)
    for i in range(1, len(msb_results)):
        nb0, _, _, res0, t0, _, _ = msb_results[i-1]
        nb1, _, _, res1, t1, _, _ = msb_results[i]
        if res0 == "SAT" and res1 == "SAT" and t0 > 0.1:
            ratio = t1 / t0
            print(f"  {nb0} -> {nb1} bits: {t0:.1f}s -> {t1:.1f}s  (x{ratio:.2f})", flush=True)

    print(flush=True)
    print("INTERPRETATION:", flush=True)
    print("  - If difficulty is uniform: each +4 bits adds ~equal time factor.", flush=True)
    print("  - If threshold: fine up to N bits, then sudden explosion.", flush=True)
    print("  - If MSB-concentrated: carry chains make MSBs of the 8th register", flush=True)
    print("    the actual obstruction (fixable by targeting carry structure).", flush=True)
    print("  - If LSB-concentrated: the low bits determine register compatibility", flush=True)
    print("    and the solver can't efficiently propagate constraints upward.", flush=True)


if __name__ == "__main__":
    main()
