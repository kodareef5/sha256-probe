#!/usr/bin/env python3
"""
Script 74: MITM Anchor Round Sweep — Test anchors at rounds 59, 60, 61

Prior result from 66c (anchor at round 60, 4/3 split):
  - 7/8 registers (224 bits): SAT in 291s
  - 232 bits (7 regs + 8 bits): SAT in 469s
  - 256 bits (all 8 regs): TIMEOUT at 3600s

The bottleneck at round 60 was h60 = e57, which depends on only W57
(depth 1 from the fixed round-56 state).

THIS EXPERIMENT: Does anchoring at a DIFFERENT round shift the bottleneck?

Round 59 anchor (3/4 split):
  Forward:  rounds 57-59 (3 rounds, free W[57..59])
  Backward: rounds 59-63 (4 rounds from free anchor, W[60] free, W[61..63] derived)
  h59 = g56 = CONSTANT (no free word dependence!) -- different bottleneck profile

Round 60 anchor (4/3 split) -- baseline from 66c:
  Forward:  rounds 57-60 (4 rounds, free W[57..60])
  Backward: rounds 60-63 (3 rounds from free anchor, W[61..63] derived)
  h60 = e57 (depth 1 from W57)

Round 61 anchor (5/2 split):
  Forward:  rounds 57-61 (5 rounds, free W[57..60], W[61] schedule-derived)
  Backward: rounds 61-63 (2 rounds from anchor, W[62..63] derived)
  Different depth structure again.

We sweep N = 0, 64, 128, 192, 224, 256 matched anchor bits for each.
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
    """Constrain the first n_bits of two 32-bit words to be equal."""
    for i in range(n_bits):
        a, b = A[i], B[i]
        if cnf._is_known(a) and cnf._is_known(b):
            if cnf._get_val(a) != cnf._get_val(b):
                cnf.clauses.append([])
            continue
        if cnf._is_known(a):
            cnf.clauses.append([b] if cnf._get_val(a) else [-b])
            continue
        if cnf._is_known(b):
            cnf.clauses.append([a] if cnf._get_val(b) else [-a])
            continue
        cnf.clauses.append([-a, b])
        cnf.clauses.append([a, -b])


def derive_schedule_word(cnf, W_all, t, W_pre_1, W_pre_2, msg_idx):
    """
    Derive W[t] from the schedule recurrence:
      W[t] = sigma1(W[t-2]) + W[t-7] + sigma0(W[t-15]) + W[t-16]

    W_all: dict mapping round -> bit-array for this message
    W_pre_1, W_pre_2: precomputed schedule arrays for msg1, msg2
    msg_idx: 1 or 2 (which message's precomputed schedule to use)
    """
    W_pre = W_pre_1 if msg_idx == 1 else W_pre_2

    # W[t-2]: must be in W_all (free or derived)
    w_t_minus_2 = W_all[t - 2]

    # W[t-7]: if t-7 <= 56, use precomputed constant; else from W_all
    if t - 7 <= 56:
        w_t_minus_7 = cnf.const_word(W_pre[t - 7])
    else:
        w_t_minus_7 = W_all[t - 7]

    # W[t-15]: always <= 56 for our range (t <= 63 => t-15 <= 48)
    w_t_minus_15_val = sigma0_py(W_pre[t - 15])
    w_t_minus_15 = cnf.const_word(w_t_minus_15_val)

    # W[t-16]: always <= 56 for our range
    w_t_minus_16 = cnf.const_word(W_pre[t - 16])

    # W[t] = sigma1(W[t-2]) + W[t-7] + sigma0(W[t-15]) + W[t-16]
    result = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w_t_minus_2), w_t_minus_7),
        cnf.add_word(w_t_minus_15, w_t_minus_16)
    )
    return result


def encode_anchor_at_round(anchor_round, n_match_bits, m0=0x17149975):
    """
    Encode the MITM split at a given anchor round.

    anchor_round: 59, 60, or 61
    n_match_bits: how many bits of the anchor state to constrain (0..256)
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

    # Determine the split:
    #   Forward: rounds 57 .. anchor_round
    #   Backward: rounds anchor_round .. 63
    n_fwd_rounds = anchor_round - 56   # rounds 57..anchor_round
    n_bwd_rounds = 63 - anchor_round   # rounds (anchor_round+1)..63

    # ===== FORWARD HALF =====
    # Fixed starting state at round 56
    s1_fwd = tuple(cnf.const_word(v) for v in state1)
    s2_fwd = tuple(cnf.const_word(v) for v in state2)

    # Determine which W words are free in the forward half.
    # Free words: W[57] .. W[57 + min(n_fwd_rounds, sr60_free_count) - 1]
    # For the sr=60 problem, we have at most 4 free words (W[57..60]).
    # Beyond W[60], schedule recurrence kicks in.
    #
    # Free W: those in {57..60} that fall within the forward range
    # Derived W: those in {61..anchor_round} that the forward half needs
    max_free_round = 60  # W[57..60] are the 4 free words in sr=60
    fwd_last_round = 56 + n_fwd_rounds  # = anchor_round

    # Create free W variables for W[57..min(60, anchor_round)]
    n_free_w = min(max_free_round, fwd_last_round) - 56  # how many of W57..W60 we need
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(n_free_w)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(n_free_w)]

    # Build the full forward schedule: W[57..anchor_round]
    # Map round -> bit-array
    W1_fwd = {}
    W2_fwd = {}
    for i in range(n_free_w):
        W1_fwd[57 + i] = w1_free[i]
        W2_fwd[57 + i] = w2_free[i]

    # Derive any schedule words beyond W[60] that the forward half needs
    for t in range(61, fwd_last_round + 1):
        W1_fwd[t] = derive_schedule_word(cnf, W1_fwd, t, W1_pre, W2_pre, 1)
        W2_fwd[t] = derive_schedule_word(cnf, W2_fwd, t, W1_pre, W2_pre, 2)

    # Run forward rounds
    fwd_st1 = s1_fwd
    for r in range(57, fwd_last_round + 1):
        fwd_st1 = cnf.sha256_round_correct(fwd_st1, enc.K[r], W1_fwd[r])

    fwd_st2 = s2_fwd
    for r in range(57, fwd_last_round + 1):
        fwd_st2 = cnf.sha256_round_correct(fwd_st2, enc.K[r], W2_fwd[r])

    # ===== BACKWARD HALF =====
    # Free anchor state at the anchor round
    anc1 = tuple(cnf.free_word(f"anc1_{i}") for i in range(8))
    anc2 = tuple(cnf.free_word(f"anc2_{i}") for i in range(8))

    # Build backward schedule: W[anchor_round+1 .. 63]
    # These all depend on W words from the forward half via schedule recurrence.
    # We need W[t-2] for each derived word. Build a combined map.
    W1_all = dict(W1_fwd)  # copy forward schedule
    W2_all = dict(W2_fwd)

    # For the backward half, we may need W words that are "free" in the
    # backward half but constrained by schedule. Specifically:
    # - If anchor_round = 59: backward needs W[60..63]
    #   W[60] is free in backward half (not constrained by schedule from earlier words
    #   since it's one of the sr=60 free words, but the forward half only went to 59
    #   so W[60] wasn't created there)
    # - If anchor_round = 60: backward needs W[61..63], all schedule-derived
    # - If anchor_round = 61: backward needs W[62..63], all schedule-derived

    # For anchor_round=59: W[60] needs to be a free variable in the backward half.
    # It's not constrained by the forward half, but it IS used by the schedule
    # to derive W[62] = sigma1(W[60]) + ...
    # So we create it as a free variable.
    bwd_first_round = anchor_round + 1

    # Determine free W in backward half: those in {57..60} not already in forward
    for t in range(57, 61):
        if t not in W1_all:
            # This free word wasn't used by the forward half; create it
            w1_new = cnf.free_word(f"W1_{t}")
            w2_new = cnf.free_word(f"W2_{t}")
            W1_all[t] = w1_new
            W2_all[t] = w2_new

    # Now derive all schedule words needed for backward half
    for t in range(bwd_first_round, 64):
        if t not in W1_all:
            W1_all[t] = derive_schedule_word(cnf, W1_all, t, W1_pre, W2_pre, 1)
            W2_all[t] = derive_schedule_word(cnf, W2_all, t, W1_pre, W2_pre, 2)

    # Run backward rounds from anchor
    bwd_st1 = anc1
    for r in range(bwd_first_round, 64):
        bwd_st1 = cnf.sha256_round_correct(bwd_st1, enc.K[r], W1_all[r])

    bwd_st2 = anc2
    for r in range(bwd_first_round, 64):
        bwd_st2 = cnf.sha256_round_correct(bwd_st2, enc.K[r], W2_all[r])

    # ===== COLLISION CONSTRAINT =====
    # After round 63: bwd_st1 must equal bwd_st2
    for i in range(8):
        cnf.eq_word(bwd_st1[i], bwd_st2[i])

    # ===== ANCHOR MATCHING =====
    # Connect forward half's anchor-round output to backward half's anchor input
    # by equating the first n_match_bits.
    n_full_regs = n_match_bits // 32
    n_partial_bits = n_match_bits % 32

    for reg in range(n_full_regs):
        cnf.eq_word(fwd_st1[reg], anc1[reg])
        cnf.eq_word(fwd_st2[reg], anc2[reg])

    if n_partial_bits > 0 and n_full_regs < 8:
        eq_bits(cnf, fwd_st1[n_full_regs], anc1[n_full_regs], n_partial_bits)
        eq_bits(cnf, fwd_st2[n_full_regs], anc2[n_full_regs], n_partial_bits)

    return cnf, n_fwd_rounds, n_bwd_rounds, len(w1_free)


def run_one(anchor_round, n_match_bits, timeout_sec=300):
    """Encode and solve one configuration."""
    t_enc_start = time.time()
    cnf, n_fwd, n_bwd, n_free = encode_anchor_at_round(anchor_round, n_match_bits)
    t_enc = time.time() - t_enc_start

    nv = cnf.next_var - 1
    nc = len(cnf.clauses)

    cnf_file = f"/tmp/74_anchor_r{anchor_round}_N{n_match_bits}.cnf"
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

    return result, t_enc, t_solve, nv, nc, n_fwd, n_bwd, n_free


def main():
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 300

    print("=" * 90, flush=True)
    print("74: MITM ANCHOR ROUND SWEEP -- Rounds 59, 60, 61", flush=True)
    print("=" * 90, flush=True)
    print(flush=True)
    print("Question: Does anchoring at a different round shift the bottleneck?", flush=True)
    print(flush=True)
    print("Round 59 (3/4 split): h59 = g56 = CONSTANT (no free word dependence)", flush=True)
    print("Round 60 (4/3 split): h60 = e57 (depth 1, depends on W57) -- baseline", flush=True)
    print("Round 61 (5/2 split): deeper dependence structure", flush=True)
    print(flush=True)
    print(f"Timeout per instance: {timeout}s", flush=True)
    print(flush=True)

    # Test points for partial anchor matching
    n_values = [0, 64, 128, 192, 224, 256]

    # Run for each anchor round
    anchor_rounds = [59, 60, 61]
    all_results = {}  # anchor_round -> list of (N, result, t_solve, nv, nc, n_fwd, n_bwd, n_free)

    for ar in anchor_rounds:
        print("=" * 90, flush=True)
        split_fwd = ar - 56
        split_bwd = 63 - ar
        print(f"ANCHOR AT ROUND {ar}  ({split_fwd}/{split_bwd} split)", flush=True)
        print(f"  Forward:  rounds 57-{ar} ({split_fwd} rounds)", flush=True)
        print(f"  Backward: rounds {ar+1}-63 ({split_bwd} rounds)", flush=True)
        print("=" * 90, flush=True)
        print(f"{'N_bits':>7} {'regs':>5} {'vars':>8} {'clauses':>10} "
              f"{'enc_t':>7} {'result':>8} {'solve_t':>9} {'fwd_W':>6}", flush=True)
        print("-" * 78, flush=True)

        results = []
        for N in n_values:
            n_regs = N // 32
            partial = N % 32
            reg_str = f"{n_regs}"
            if partial > 0:
                reg_str += f"+{partial}b"

            result, t_enc, t_solve, nv, nc, n_fwd, n_bwd, n_free = run_one(ar, N, timeout)
            print(f"{N:7d} {reg_str:>5} {nv:8d} {nc:10d} {t_enc:6.1f}s "
                  f"{result:>8} {t_solve:8.1f}s {n_free:6d}", flush=True)
            results.append((N, result, t_solve, nv, nc, n_fwd, n_bwd, n_free))

        all_results[ar] = results
        print(flush=True)

    # ===== COMPARISON TABLE =====
    print("=" * 90, flush=True)
    print("COMPARISON: Solve time by anchor round and matched bits", flush=True)
    print("=" * 90, flush=True)
    print(flush=True)

    # Header
    header = f"{'N_bits':>7}"
    for ar in anchor_rounds:
        header += f"  {'R'+str(ar)+' result':>12} {'time':>8}"
    print(header, flush=True)
    print("-" * (7 + len(anchor_rounds) * 23), flush=True)

    for idx, N in enumerate(n_values):
        row = f"{N:7d}"
        for ar in anchor_rounds:
            res = all_results[ar][idx]
            result = res[1]
            t_solve = res[2]
            row += f"  {result:>12} {t_solve:7.1f}s"
        print(row, flush=True)

    # ===== ANALYSIS =====
    print(flush=True)
    print("=" * 90, flush=True)
    print("ANALYSIS", flush=True)
    print("=" * 90, flush=True)
    print(flush=True)

    for ar in anchor_rounds:
        results = all_results[ar]
        split_fwd = ar - 56
        split_bwd = 63 - ar

        last_sat_n = -1
        first_hard_n = None
        for N, result, t_solve, nv, nc, n_fwd, n_bwd, n_free in results:
            if result == "SAT":
                last_sat_n = N
            elif result in ("TIMEOUT", "UNSAT") and first_hard_n is None:
                first_hard_n = N

        print(f"Round {ar} anchor ({split_fwd}/{split_bwd} split):", flush=True)
        if last_sat_n >= 0:
            print(f"  Last SAT:       N = {last_sat_n} bits ({last_sat_n // 32} regs)", flush=True)
        if first_hard_n is not None:
            print(f"  First TIMEOUT:  N = {first_hard_n} bits ({first_hard_n // 32} regs)", flush=True)
        else:
            print(f"  No timeout -- all N values solved!", flush=True)

        # Time scaling
        sat_results = [(N, t_solve) for N, result, t_solve, _, _, _, _, _ in results if result == "SAT"]
        if len(sat_results) >= 2:
            print(f"  Time scaling:", flush=True)
            for i in range(1, len(sat_results)):
                n0, t0 = sat_results[i - 1]
                n1, t1 = sat_results[i]
                if t0 > 0.01:
                    ratio = t1 / t0
                    print(f"    N={n0} -> N={n1}: {t0:.1f}s -> {t1:.1f}s (x{ratio:.2f})", flush=True)
        print(flush=True)

    # Visual comparison
    print("VISUAL: Solve time curves", flush=True)
    print("-" * 60, flush=True)
    for ar in anchor_rounds:
        results = all_results[ar]
        label = f"R{ar}"
        for N, result, t_solve, nv, nc, n_fwd, n_bwd, n_free in results:
            bar_width = min(int(t_solve / 5), 50)
            bar = "#" * bar_width
            if result == "TIMEOUT":
                bar += " >>TIMEOUT"
            elif result == "UNSAT":
                bar += " UNSAT"
            print(f"  {label} N={N:3d}: {t_solve:7.1f}s |{bar}", flush=True)
        print(flush=True)

    # Final verdict
    print("=" * 90, flush=True)
    print("VERDICT", flush=True)
    print("=" * 90, flush=True)
    print(flush=True)

    # Find which anchor round reaches the most bits before timeout
    best_ar = None
    best_last_sat = -1
    for ar in anchor_rounds:
        results = all_results[ar]
        last_sat = max((N for N, result, _, _, _, _, _, _ in results if result == "SAT"), default=-1)
        if last_sat > best_last_sat:
            best_last_sat = last_sat
            best_ar = ar

    if best_ar is not None:
        print(f"Best anchor round: {best_ar} (SAT up to N={best_last_sat} bits)", flush=True)
    print(flush=True)

    # Check if any anchor gets all 256 bits
    for ar in anchor_rounds:
        results = all_results[ar]
        full_match = next((r for N, r, _, _, _, _, _, _ in results if N == 256), None)
        if full_match == "SAT":
            print(f"*** Round {ar}: FULL 256-bit match is SAT! ***", flush=True)
        elif full_match == "UNSAT":
            print(f"Round {ar}: FULL 256-bit match is UNSAT.", flush=True)
        else:
            print(f"Round {ar}: FULL 256-bit match timed out at {timeout}s.", flush=True)

    print(flush=True)
    print("INTERPRETATION:", flush=True)
    print("  - Smoothest curve = best anchor choice for MITM decomposition", flush=True)
    print("  - If one anchor avoids the cliff, it may enable solving full 256-bit match", flush=True)
    print("  - The bottleneck register shifts with anchor round:", flush=True)
    print("    R59: h59 = g56 (constant)", flush=True)
    print("    R60: h60 = e57 (depth 1)", flush=True)
    print("    R61: h61 = shifted further", flush=True)


if __name__ == "__main__":
    main()
