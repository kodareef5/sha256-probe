#!/usr/bin/env python3
"""
Script 66c: Partial Anchor Experiment — Forward/Backward Cone Intersection at Round 60

THE KEY EXPERIMENT: Does the forward cone (rounds 57-60) intersect the
backward cone (rounds 61-63) at Round 60?

We split the sr=60 7-round tail at Round 60:
  Forward:  fixed Round 56 state + free W[57..60] -> state at Round 60
  Backward: free anchor state at Round 60 + derived W[61..63] -> collision at Round 63

The two halves share anchor variables at Round 60. Instead of requiring
all 256 bits to match (= full sr=60), we require only the first N bits.

  N=0:   halves independent, trivially SAT
  N=256: equivalent to original sr=60 problem
  Transition point reveals where the hard constraint lives.

Schedule coupling: W[61] depends on W[59] (from forward half), W[62]
depends on W[60], W[63] depends on W[61]. So the backward half uses
the SAME free W variables from the forward half to derive its schedule.
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


def eq_bits(cnf, A, B, n_bits):
    """
    Constrain the first n_bits of two 32-bit words to be equal.
    A and B are bit arrays (LSB-first, length 32).
    """
    for i in range(n_bits):
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


def encode_partial_anchor(n_match_bits, m0=0x17149975):
    """
    Encode the split sr=60 problem with N matching bits at Round 60.

    Forward half:  rounds 57-60 from fixed Round 56 state, free W[57..60]
    Backward half: rounds 61-63 from free anchor state, W[61..63] derived from W[59..61]
    Anchor matching: first n_match_bits of the Round 60 state must agree
    Collision: final state after round 63 must collide (st1 == st2)
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
    # Fixed starting state at Round 56
    s1_fwd = tuple(cnf.const_word(v) for v in state1)
    s2_fwd = tuple(cnf.const_word(v) for v in state2)

    # Free schedule words W[57], W[58], W[59], W[60] for each message
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

    # Run 4 forward rounds (57, 58, 59, 60) for both messages
    fwd_st1 = s1_fwd
    for i in range(4):
        fwd_st1 = cnf.sha256_round_correct(fwd_st1, enc.K[57 + i], w1_free[i])

    fwd_st2 = s2_fwd
    for i in range(4):
        fwd_st2 = cnf.sha256_round_correct(fwd_st2, enc.K[57 + i], w2_free[i])

    # fwd_st1, fwd_st2 are the Round 60 states from the forward half
    # Each is a tuple of 8 x 32-bit words (a, b, c, d, e, f, g, h)

    # ===== BACKWARD HALF: rounds 61-63 =====
    # Free anchor state at Round 60 (what we'll partially constrain)
    anc1 = tuple(cnf.free_word(f"anc1_{i}") for i in range(8))
    anc2 = tuple(cnf.free_word(f"anc2_{i}") for i in range(8))

    # Derive schedule words W[61], W[62], W[63] from the forward half's
    # free W variables. The schedule recurrence is:
    #   W[t] = sigma1(W[t-2]) + W[t-7] + sigma0(W[t-15]) + W[t-16]
    #
    # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
    #   W[59] is w1_free[2] / w2_free[2] (free, from forward half)
    #   W[54], W[46], W[45] are precomputed constants
    #
    # W[62] = sigma1(W[60]) + W[55] + sigma0(W[47]) + W[46]
    #   W[60] is w1_free[3] / w2_free[3] (free, from forward half)
    #
    # W[63] = sigma1(W[61]) + W[56] + sigma0(W[48]) + W[47]
    #   W[61] is derived above

    # W[61] for message 1
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45]))
    )
    # W[61] for message 2
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45]))
    )

    # W[62] for message 1
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[3]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46]))
    )
    # W[62] for message 2
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[3]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46]))
    )

    # W[63] for message 1
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_61), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47]))
    )
    # W[63] for message 2
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_61), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47]))
    )

    # Run 3 backward rounds (61, 62, 63) from the anchor state
    bwd_st1 = anc1
    bwd_st1 = cnf.sha256_round_correct(bwd_st1, enc.K[61], w1_61)
    bwd_st1 = cnf.sha256_round_correct(bwd_st1, enc.K[62], w1_62)
    bwd_st1 = cnf.sha256_round_correct(bwd_st1, enc.K[63], w1_63)

    bwd_st2 = anc2
    bwd_st2 = cnf.sha256_round_correct(bwd_st2, enc.K[61], w2_61)
    bwd_st2 = cnf.sha256_round_correct(bwd_st2, enc.K[62], w2_62)
    bwd_st2 = cnf.sha256_round_correct(bwd_st2, enc.K[63], w2_63)

    # ===== COLLISION CONSTRAINT =====
    # After round 63: bwd_st1 must equal bwd_st2
    for i in range(8):
        cnf.eq_word(bwd_st1[i], bwd_st2[i])

    # ===== ANCHOR MATCHING =====
    # Connect the forward half's Round 60 output to the backward half's
    # Round 60 input by equating the first n_match_bits.
    #
    # State has 8 registers x 32 bits = 256 bits total.
    # We match register-by-register, then bit-by-bit for the partial register.
    n_full_regs = n_match_bits // 32
    n_partial_bits = n_match_bits % 32

    for reg in range(n_full_regs):
        cnf.eq_word(fwd_st1[reg], anc1[reg])
        cnf.eq_word(fwd_st2[reg], anc2[reg])

    if n_partial_bits > 0 and n_full_regs < 8:
        eq_bits(cnf, fwd_st1[n_full_regs], anc1[n_full_regs], n_partial_bits)
        eq_bits(cnf, fwd_st2[n_full_regs], anc2[n_full_regs], n_partial_bits)

    return cnf


def run_experiment(n_match_bits, timeout_sec=300):
    """Encode and solve for a given number of matched bits."""
    t_enc_start = time.time()
    cnf = encode_partial_anchor(n_match_bits)
    t_enc = time.time() - t_enc_start

    nv = cnf.next_var - 1
    nc = len(cnf.clauses)

    cnf_file = f"/tmp/66c_anchor_N{n_match_bits}.cnf"
    cnf.write_dimacs(cnf_file)

    # Run Kissat
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
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 300

    # Test points: 0, 32, 64, 128, 192, 256 bits matched
    # Also add a few intermediate points around where transition might happen
    n_values = [0, 32, 64, 96, 128, 160, 192, 224, 256]

    print("=" * 80, flush=True)
    print("66c: PARTIAL ANCHOR EXPERIMENT", flush=True)
    print("Forward (57-60) / Backward (61-63) cone intersection at Round 60", flush=True)
    print(f"Timeout per instance: {timeout}s", flush=True)
    print("=" * 80, flush=True)
    print(flush=True)
    print(f"{'N_bits':>7} {'regs':>5} {'vars':>8} {'clauses':>10} {'enc_t':>7} {'result':>8} {'solve_t':>9}", flush=True)
    print("-" * 68, flush=True)

    results = []
    for N in n_values:
        n_regs = N // 32
        partial = N % 32

        reg_str = f"{n_regs}"
        if partial > 0:
            reg_str += f"+{partial}b"

        result, t_enc, t_solve, nv, nc = run_experiment(N, timeout)

        print(f"{N:7d} {reg_str:>5} {nv:8d} {nc:10d} {t_enc:6.1f}s {result:>8} {t_solve:8.1f}s", flush=True)
        results.append((N, n_regs, nv, nc, result, t_solve))

        # If we hit UNSAT, the problem is fundamentally impossible at this coupling
        if result == "UNSAT":
            print(f"  -> UNSAT at N={N} bits! Forward/backward cones provably disjoint.", flush=True)

    # Summary
    print(flush=True)
    print("=" * 80, flush=True)
    print("SUMMARY: Forward/Backward Cone Intersection", flush=True)
    print("=" * 80, flush=True)

    last_sat = -1
    first_hard = None
    for N, n_regs, nv, nc, result, t_solve in results:
        marker = ""
        if result == "SAT":
            last_sat = N
            marker = " [cones intersect]"
        elif result == "UNSAT":
            marker = " [cones DISJOINT]"
        elif result == "TIMEOUT":
            if first_hard is None:
                first_hard = N
            marker = " [undecided]"

        bar_len = min(int(t_solve / 3), 40)
        bar = "#" * bar_len
        print(f"  N={N:3d} ({n_regs} regs): {t_solve:7.1f}s [{result:>7}] {bar}{marker}", flush=True)

    print(flush=True)
    if last_sat >= 0:
        print(f"  Last confirmed SAT:      N = {last_sat} bits ({last_sat // 32} registers)", flush=True)
    if first_hard is not None:
        print(f"  First TIMEOUT/UNSAT:     N = {first_hard} bits ({first_hard // 32} registers)", flush=True)
    else:
        first_unsat = next((N for N, _, _, _, r, _ in results if r == "UNSAT"), None)
        if first_unsat is not None:
            print(f"  First UNSAT:             N = {first_unsat} bits ({first_unsat // 32} registers)", flush=True)

    if last_sat >= 0 and last_sat < 256:
        gap_start = last_sat
        gap_end = 256
        for N, _, _, _, r, _ in results:
            if N > last_sat and r in ("TIMEOUT", "UNSAT"):
                gap_end = N
                break
        print(f"  Transition region:       N in [{gap_start}, {gap_end}]", flush=True)
        print(f"  Constraint gap:          {gap_end - gap_start} bits", flush=True)

    print(flush=True)
    print("INTERPRETATION:", flush=True)
    print("  SAT at N=256 => sr=60 is satisfiable (collision exists!)", flush=True)
    print("  UNSAT at N=K => forward cone after 4 rounds cannot produce", flush=True)
    print("                  a state whose first K bits allow a backward", flush=True)
    print("                  3-round collision path to exist.", flush=True)
    print("  The transition point reveals which registers create the", flush=True)
    print("                  bottleneck between forward reachability", flush=True)
    print("                  and backward collision requirements.", flush=True)


if __name__ == "__main__":
    main()
