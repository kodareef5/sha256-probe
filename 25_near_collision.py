#!/usr/bin/env python3
"""
Script 25: Near-Collision Slack Map (Dimension 5)

Instead of requiring H1 == H2 perfectly (256-bit match),
allow N bits to differ. This maps the OUTPUT-side phase transition.

If allowing 4 differing bits makes sr=60 solve instantly, the
solver navigates the schedule fine but chokes on the final collision.
Near-miss solutions can then be used for backbone mining.
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')


def encode_near_collision(mode="sr60", max_diff_bits=0, timeout_sec=300):
    """
    Encode sr=60 but allow up to max_diff_bits of the final hash to differ.

    max_diff_bits=0: standard collision (H1 == H2)
    max_diff_bits=N: at most N bits of H1 XOR H2 can be 1
    """
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    cnf = enc.CNFBuilder()
    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    n_free = 4  # sr=60
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(n_free)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(n_free)]

    W1_schedule = list(w1_free)
    W2_schedule = list(w2_free)

    # W[61] enforced
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45])))
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45])))
    W1_schedule.append(w1_61)
    W2_schedule.append(w2_61)

    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[3]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[3]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46])))
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[4]), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[4]), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47])))

    W1_schedule.extend([w1_62, w1_63])
    W2_schedule.extend([w2_62, w2_63])

    st1 = s1
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, enc.K[57+i], W1_schedule[i])
    st2 = s2
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, enc.K[57+i], W2_schedule[i])

    if max_diff_bits == 0:
        # Perfect collision
        for i in range(8):
            cnf.eq_word(st1[i], st2[i])
    else:
        # Near-collision: XOR of final states must have at most max_diff_bits set bits
        # Compute XOR diff bits
        diff_bits = []
        for i in range(8):
            for bit in range(32):
                d = cnf.xor2(st1[i][bit], st2[i][bit])
                diff_bits.append(d)

        # At-most-N constraint on diff_bits
        # Use sequential counter encoding (efficient for small N)
        # counter[j][k] = "at most k of the first j diff bits are 1"

        # For small N, use a simple approach: create N+1 counter variables per position
        # Actually for N<=16, we can use a sorter network or just sequential counters

        # Sequential counter: c[j] = number of 1s among diff_bits[0..j]
        # c[0] = diff_bits[0]
        # c[j] = c[j-1] + diff_bits[j]  (saturating at max_diff_bits+1)

        # We encode: c[j][k] = "at least k of the first j+1 bits are 1"
        # Constraint: NOT c[255][max_diff_bits+1] (at most max_diff_bits 1s total)

        n = len(diff_bits)
        m = max_diff_bits + 1  # We need counter up to m

        # c[j][k] for j=0..n-1, k=0..m
        # c[j][k] means "the count of 1s in diff_bits[0..j] is >= k"
        c = [[None] * (m + 1) for _ in range(n)]

        for j in range(n):
            for k in range(m + 1):
                if k == 0:
                    c[j][k] = cnf._const(True)  # always >= 0
                elif k > j + 1:
                    c[j][k] = cnf._const(False)  # can't have > j+1 ones in j+1 bits
                elif j == 0:
                    c[0][k] = diff_bits[0] if k == 1 else cnf._const(False)
                else:
                    # c[j][k] = c[j-1][k] OR (diff_bits[j] AND c[j-1][k-1])
                    # Simplified: if diff_bits[j] is known constant...
                    if cnf._is_known(diff_bits[j]):
                        if cnf._get_val(diff_bits[j]):
                            # This bit is 1, so c[j][k] = c[j-1][k-1]
                            c[j][k] = c[j-1][k-1]
                        else:
                            # This bit is 0, so c[j][k] = c[j-1][k]
                            c[j][k] = c[j-1][k]
                    elif c[j-1][k] is not None and cnf._is_known(c[j-1][k]) and cnf._get_val(c[j-1][k]):
                        c[j][k] = cnf._const(True)  # already >= k
                    else:
                        # General case: c[j][k] = c[j-1][k] OR (diff_bits[j] AND c[j-1][k-1])
                        if c[j-1][k-1] is None:
                            c[j][k] = c[j-1][k] if c[j-1][k] is not None else cnf._const(False)
                        else:
                            term = cnf.and2(diff_bits[j], c[j-1][k-1])
                            if c[j-1][k] is not None:
                                c[j][k] = cnf.or2(c[j-1][k], term)
                            else:
                                c[j][k] = term

        # Constraint: NOT c[n-1][m] (count < m, i.e., <= max_diff_bits)
        if c[n-1][m] is not None:
            if cnf._is_known(c[n-1][m]):
                if cnf._get_val(c[n-1][m]):
                    cnf.clauses.append([])  # Always > max_diff_bits, UNSAT
            else:
                cnf.clauses.append([-c[n-1][m]])  # at most max_diff_bits

    cnf_file = f"/tmp/sr60_near_{max_diff_bits}.cnf"
    cnf.write_dimacs(cnf_file)
    nv = cnf.next_var - 1
    nc = len(cnf.clauses)

    t0 = time.time()
    r = subprocess.run(["timeout", str(timeout_sec), "kissat", "-q", cnf_file],
                       capture_output=True, text=True, timeout=timeout_sec + 30)
    elapsed = time.time() - t0

    if r.returncode == 10:
        return "SAT", elapsed, nv, nc
    elif r.returncode == 20:
        return "UNSAT", elapsed, nv, nc
    else:
        return "TIMEOUT", elapsed, nv, nc


def main():
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 300

    print("=" * 60, flush=True)
    print("Near-Collision Slack Map (sr=60)", flush=True)
    print(f"Timeout: {timeout}s per test", flush=True)
    print("=" * 60, flush=True)
    print(f"{'N':>4} {'vars':>7} {'clauses':>9} {'result':>8} {'time':>8}", flush=True)
    print("-" * 45, flush=True)

    for n in [0, 1, 2, 4, 8, 16, 32]:
        result, elapsed, nv, nc = encode_near_collision("sr60", n, timeout)
        marker = ""
        if result == "SAT":
            marker = " <-- SOLVED!"
        print(f"{n:4d} {nv:7d} {nc:9d} {result:>8} {elapsed:7.1f}s{marker}", flush=True)

        if result == "SAT" and n > 0:
            print(f"\n  Near-collision found at N={n}!", flush=True)
            print(f"  The solver can handle the schedule at sr=60,", flush=True)
            print(f"  but needs {n} bits of output slack.", flush=True)


if __name__ == "__main__":
    main()
