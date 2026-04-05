#!/usr/bin/env python3
"""
Script 38: MaxSAT Register Collision Map

Instead of asking "can ALL 8 registers collide?" (sr=60 answer: TIMEOUT),
ask "which 7 of 8 registers CAN collide?"

This localizes the cryptographic bottleneck. If 7 registers always
collide easily but one specific register never matches, that register
is WHERE the sr=60 hardness lives.

Method: for each register r in {a,b,c,d,e,f,g,h}, encode sr=60
with collision constraints on all registers EXCEPT r. If it solves
fast, register r is the bottleneck absorbing all the entropy.
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')


def encode_partial_collision(excluded_register, mode="sr60", timeout_sec=300):
    """
    Encode sr=60 with collision on all registers EXCEPT excluded_register.
    excluded_register: index 0-7 (a=0, b=1, ..., h=7)
    """
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1.copy()
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    n_free = 5 if mode == "sr59" else 4
    cnf = enc.CNFBuilder()

    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(n_free)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(n_free)]

    W1_schedule = list(w1_free)
    W2_schedule = list(w2_free)

    if mode == "sr60":
        w1_61 = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
            cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45])))
        w2_61 = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
            cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45])))
        W1_schedule.append(w1_61)
        W2_schedule.append(w2_61)

    w60_idx = 3
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[w60_idx]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[w60_idx]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46])))
    w61_idx = 4
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W1_schedule[w61_idx]), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47])))
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(W2_schedule[w61_idx]), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47])))

    W1_schedule.extend([w1_62, w1_63])
    W2_schedule.extend([w2_62, w2_63])

    st1 = s1
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, enc.K[57+i], W1_schedule[i])
    st2 = s2
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, enc.K[57+i], W2_schedule[i])

    # Partial collision: all registers EXCEPT the excluded one
    for i in range(8):
        if i != excluded_register:
            cnf.eq_word(st1[i], st2[i])

    cnf_file = f"/tmp/{mode}_skip_reg{excluded_register}.cnf"
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

    reg_names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']

    print("=" * 70, flush=True)
    print("MaxSAT Register Collision Map", flush=True)
    print("Which register absorbs the sr=60 hardness?", flush=True)
    print(f"Testing: collide 7/8 registers, skip each one in turn", flush=True)
    print(f"Timeout: {timeout}s per test", flush=True)
    print("=" * 70, flush=True)

    print(f"\n{'Skip':>6} {'Result':>8} {'Time':>8} {'Vars':>7} {'Clauses':>9}  Analysis", flush=True)
    print("-" * 65, flush=True)

    results = []
    for reg in range(8):
        result, elapsed, nv, nc = encode_partial_collision(reg, "sr60", timeout)

        analysis = ""
        if result == "SAT":
            analysis = f"<-- Register {reg_names[reg]} is the BOTTLENECK (7/8 collide without it!)"
        elif result == "UNSAT":
            analysis = f"<-- Even 7/8 is UNSAT when skipping {reg_names[reg]}"

        print(f"  d{reg_names[reg]:>1}   {result:>8} {elapsed:7.1f}s {nv:7d} {nc:9d}  {analysis}", flush=True)
        results.append((reg, reg_names[reg], result, elapsed))

    # Also try skipping 2 registers
    print(f"\n{'='*70}", flush=True)
    print("Skipping 2 registers (6/8 collision):", flush=True)
    print(f"{'='*70}", flush=True)

    # Try the most promising pairs (skip a+e since those are computed, not shifted)
    pairs = [(0, 4), (0, 7), (3, 7), (4, 7)]
    for r1, r2 in pairs:
        M1 = [0x17149975] + [0xffffffff] * 15
        M2 = M1.copy()
        M2[0] ^= 0x80000000
        M2[9] ^= 0x80000000

        state1, W1_pre = enc.precompute_state(M1)
        state2, W2_pre = enc.precompute_state(M2)

        cnf = enc.CNFBuilder()
        s1 = tuple(cnf.const_word(v) for v in state1)
        s2 = tuple(cnf.const_word(v) for v in state2)

        w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
        w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

        W1_schedule = list(w1_free)
        W2_schedule = list(w2_free)

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

        for i in range(8):
            if i != r1 and i != r2:
                cnf.eq_word(st1[i], st2[i])

        cnf_file = f"/tmp/sr60_skip_{r1}_{r2}.cnf"
        cnf.write_dimacs(cnf_file)

        t0 = time.time()
        r = subprocess.run(["timeout", str(timeout), "kissat", "-q", cnf_file],
                           capture_output=True, text=True, timeout=timeout + 30)
        elapsed = time.time() - t0

        if r.returncode == 10: status = "SAT"
        elif r.returncode == 20: status = "UNSAT"
        else: status = "TIMEOUT"

        marker = " <-- EASY!" if status == "SAT" and elapsed < 30 else ""
        print(f"  Skip d{reg_names[r1]}+d{reg_names[r2]}: {status:>8} {elapsed:7.1f}s{marker}", flush=True)

    print(f"\n{'='*70}", flush=True)
    print("ANALYSIS", flush=True)
    print(f"{'='*70}", flush=True)

    sat_regs = [name for _, name, result, _ in results if result == "SAT"]
    timeout_regs = [name for _, name, result, _ in results if result == "TIMEOUT"]
    unsat_regs = [name for _, name, result, _ in results if result == "UNSAT"]

    if sat_regs:
        print(f"  Bottleneck registers (7/8 solves without them): {', '.join(sat_regs)}", flush=True)
        print(f"  These registers absorb the cryptographic hardness.", flush=True)
    if timeout_regs:
        print(f"  Hard even at 7/8 (removing doesn't help): {', '.join(timeout_regs)}", flush=True)
        print(f"  The hardness is distributed, not localized.", flush=True)
    if unsat_regs:
        print(f"  Structurally impossible (UNSAT): {', '.join(unsat_regs)}", flush=True)


if __name__ == "__main__":
    main()
