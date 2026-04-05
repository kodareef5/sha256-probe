#!/usr/bin/env python3
"""
Script 14: Progressive Constraint Tightening via Custom CNF + Kissat

Maps the hardness transition from sr=59 to sr=60 by constraining
the low k bits of W[61] to match the schedule equation.

Uses our CSA-based custom CNF encoder (which solves sr=59 in 220s)
and kissat (not Z3, which was too slow).

k=0:  pure sr=59 (solved in 220s)
k=32: full sr=60 (timeout at 3600s)

The transition point tells us whether a hybrid approach is viable:
  If k=16 is tractable: brute-force remaining 16 bits = 65536 SAT instances
"""

import sys
import time
import subprocess
import os

# Import encoder
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
mod = import_module('13_custom_cnf_encoder')

# SHA-256 helper
def ROR(x, n): return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF
def sigma0_py(x): return ROR(x, 7) ^ ROR(x, 18) ^ (x >> 3)
def sigma1_py(x): return ROR(x, 17) ^ ROR(x, 19) ^ (x >> 10)


def encode_sr59_plus_k(k_bits, timeout_sec=600):
    """
    Encode sr=59 with k additional bits of W[61] schedule compliance.
    """
    # Reuse the encoder module's precompute
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1[:]
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = mod.precompute_state(M1)
    state2, W2_pre = mod.precompute_state(M2)

    cnf = mod.CNFBuilder()

    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    # 5 free words (sr=59)
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

    # Progressive W[61] schedule constraint
    if k_bits > 0:
        # W[61]_schedule = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
        w1_61_sched = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
            cnf.add_word(cnf.const_word(sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45]))
        )
        w2_61_sched = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
            cnf.add_word(cnf.const_word(sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45]))
        )

        # Constrain low k bits to match
        for bit in range(min(k_bits, 32)):
            cnf.eq_word.__func__  # just to reference
            a1, b1 = w1_free[4][bit], w1_61_sched[bit]
            a2, b2 = w2_free[4][bit], w2_61_sched[bit]
            # eq for each bit
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

    # Write and solve
    cnf_file = f"/tmp/sr59_k{k_bits}.cnf"
    cnf.write_dimacs(cnf_file)
    nv = cnf.next_var - 1
    nc = len(cnf.clauses)

    t0 = time.time()
    r = subprocess.run(
        ["timeout", str(timeout_sec), "kissat", cnf_file],
        capture_output=True, text=True, timeout=timeout_sec + 30
    )
    elapsed = time.time() - t0

    if r.returncode == 10:
        result = "SAT"
    elif r.returncode == 20:
        result = "UNSAT"
    else:
        result = "TIMEOUT"

    return result, elapsed, nv, nc


def main():
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 600

    k_values = [0, 1, 2, 4, 8, 12, 16, 20, 24, 28, 32]

    print("=" * 70, flush=True)
    print("Progressive Constraint: sr=59 + k bits of W[61] schedule", flush=True)
    print(f"Timeout per instance: {timeout}s", flush=True)
    print("=" * 70, flush=True)
    print(f"{'k':>4} {'slack':>6} {'eff_sr':>8} {'vars':>7} {'clauses':>9} {'result':>8} {'time':>8}", flush=True)
    print("-" * 60, flush=True)

    results = []
    for k in k_values:
        slack = max(64 - 2 * k, 0)
        eff_sr = 59 + k / 32.0

        result, elapsed, nv, nc = encode_sr59_plus_k(k, timeout)
        print(f"{k:4d} {slack:6d} {eff_sr:8.2f} {nv:7d} {nc:9d} {result:>8} {elapsed:7.1f}s", flush=True)
        results.append((k, slack, eff_sr, result, elapsed))

        if result == "UNSAT":
            print(f"  UNSAT at k={k}! Schedule constraint incompatible.", flush=True)
            break

    print("\n" + "=" * 70, flush=True)
    print("PHASE TRANSITION MAP", flush=True)
    print("=" * 70, flush=True)
    for k, slack, eff_sr, result, elapsed in results:
        bar = "#" * min(int(elapsed / 5), 60)
        print(f"  k={k:3d} sr={eff_sr:.2f} slack={slack:3d}: {elapsed:7.1f}s [{result:>7}] {bar}", flush=True)

    last_sat = max((k for k, _, _, r, _ in results if r == "SAT"), default=-1)
    first_hard = min((k for k, _, _, r, _ in results if r in ("TIMEOUT", "UNSAT")), default=33)
    print(f"\n  Last SAT:    k={last_sat}", flush=True)
    print(f"  First HARD:  k={first_hard}", flush=True)

    if last_sat >= 8:
        remaining = 32 - last_sat
        n_inst = 2 ** remaining
        est_time = results[[r[0] for r in results].index(last_sat)][4]
        print(f"\n  HYBRID: solve k={last_sat} ({est_time:.0f}s), brute-force {remaining} bits", flush=True)
        print(f"  = {n_inst} instances x {est_time:.0f}s = {n_inst * est_time / 3600:.1f} CPU-hours", flush=True)


if __name__ == "__main__":
    main()
