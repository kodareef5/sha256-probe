#!/usr/bin/env python3
"""
Script 30: Ghost Carries — Differential Linearization

THE INSIGHT: We don't fix carries to constants (that killed cubing).
We force carry_M1[i] == carry_M2[i] at each bit position.

If both messages produce the SAME carry at every position, then:
  sum1 = a1 XOR b1 XOR carry
  sum2 = a2 XOR b2 XOR carry
  sum1 XOR sum2 = (a1 XOR a2) XOR (b1 XOR b2)

The differential becomes PURE XOR. The modular addition's non-linearity
vanishes from the collision equation. SAT solvers eat linear systems.

We apply this to the final ripple-carry in the T1 CSA tree of rounds
57-59. This is where the deepest carry chains live.

This adds ~2 clauses per equalized carry bit (eq constraint).
For 16 MSB carries x 3 rounds x 2 additions = ~192 clauses total.
Minimal overhead, maximum linearization.
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')


def encode_ghost_carries(n_carry_bits=16, n_rounds=3, mode="sr60", timeout_sec=3600):
    """
    Encode sr=60 with ghost carry constraints.

    Forces carry_M1 == carry_M2 for the top n_carry_bits MSB positions
    of the T1 ripple-carry addition in the first n_rounds rounds.
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

    # Run both messages through rounds, tracking carries for ghost equalization
    ghost_clauses = 0

    st1 = s1
    st2 = s2

    for r in range(7):
        # --- Message 1 round ---
        a1, b1, c1, d1, e1, f1, g1, h1 = st1
        K_word = cnf.const_word(enc.K[57 + r])
        sig1_1 = cnf.Sigma1(e1)
        ch1 = cnf.Ch(e1, f1, g1)

        # T1 via CSA with tracked final carries
        s1_csa, c1_csa = cnf.csa_layer(h1, sig1_1, ch1)
        s2_csa, c2_csa = cnf.csa_layer(s1_csa, K_word, W1_schedule[r])
        s3_csa, c3_csa = cnf.csa_layer(c1_csa, s2_csa, c2_csa)
        t1_m1, carries_m1 = cnf.add_word(s3_csa, c3_csa, track_carries=True)

        sig0_1 = cnf.Sigma0(a1)
        mj1 = cnf.Maj(a1, b1, c1)
        t2_m1 = cnf.add_word(sig0_1, mj1)
        a_new1 = cnf.add_word(t1_m1, t2_m1)
        e_new1 = cnf.add_word(d1, t1_m1)
        st1 = (a_new1, a1, b1, c1, e_new1, e1, f1, g1)

        # --- Message 2 round ---
        a2, b2, c2, d2, e2, f2, g2, h2 = st2
        sig1_2 = cnf.Sigma1(e2)
        ch2 = cnf.Ch(e2, f2, g2)

        s1_csa2, c1_csa2 = cnf.csa_layer(h2, sig1_2, ch2)
        s2_csa2, c2_csa2 = cnf.csa_layer(s1_csa2, K_word, W2_schedule[r])
        s3_csa2, c3_csa2 = cnf.csa_layer(c1_csa2, s2_csa2, c2_csa2)
        t1_m2, carries_m2 = cnf.add_word(s3_csa2, c3_csa2, track_carries=True)

        sig0_2 = cnf.Sigma0(a2)
        mj2 = cnf.Maj(a2, b2, c2)
        t2_m2 = cnf.add_word(sig0_2, mj2)
        a_new2 = cnf.add_word(t1_m2, t2_m2)
        e_new2 = cnf.add_word(d2, t1_m2)
        st2 = (a_new2, a2, b2, c2, e_new2, e2, f2, g2)

        # --- GHOST CARRY EQUALIZATION ---
        if r < n_rounds:
            # Equalize the top n_carry_bits MSB carries between messages
            for bit in range(32 - n_carry_bits, 32):
                c_m1 = carries_m1[bit]
                c_m2 = carries_m2[bit]

                # Skip if both are already known constants
                if cnf._is_known(c_m1) and cnf._is_known(c_m2):
                    if cnf._get_val(c_m1) != cnf._get_val(c_m2):
                        cnf.clauses.append([])  # Impossible — UNSAT
                    continue

                # Force c_m1 == c_m2
                if cnf._is_known(c_m1):
                    val = cnf._get_val(c_m1)
                    cnf.clauses.append([c_m2] if val else [-c_m2])
                    ghost_clauses += 1
                elif cnf._is_known(c_m2):
                    val = cnf._get_val(c_m2)
                    cnf.clauses.append([c_m1] if val else [-c_m1])
                    ghost_clauses += 1
                else:
                    cnf.clauses.append([-c_m1, c_m2])
                    cnf.clauses.append([c_m1, -c_m2])
                    ghost_clauses += 2

    # Collision constraint
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    cnf_file = f"/tmp/{mode}_ghost_c{n_carry_bits}_r{n_rounds}.cnf"
    cnf.write_dimacs(cnf_file)
    nv = cnf.next_var - 1
    nc = len(cnf.clauses)

    return cnf_file, nv, nc, ghost_clauses


def main():
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 3600

    print("=" * 70, flush=True)
    print("GHOST CARRIES — Differential Linearization", flush=True)
    print("Forcing carry_M1 == carry_M2 to linearize the ARX differential", flush=True)
    print("=" * 70, flush=True)

    # Test multiple configurations
    configs = [
        # (n_carry_bits, n_rounds, mode, label)
        (16, 3, "sr59", "sr=59 baseline (expect ~220s without ghost)"),
        (16, 3, "sr60", "sr=60, 16 MSB carries x 3 rounds"),
        (32, 3, "sr60", "sr=60, ALL 32 carries x 3 rounds"),
        (16, 7, "sr60", "sr=60, 16 MSB carries x ALL 7 rounds"),
        (32, 7, "sr60", "sr=60, ALL 32 carries x ALL 7 rounds (maximum linearization)"),
    ]

    results = []
    for n_carry, n_rounds, mode, label in configs:
        print(f"\n{'='*60}", flush=True)
        print(f"Config: {label}", flush=True)
        print(f"  Carry bits equalized: {n_carry} per round, {n_rounds} rounds", flush=True)

        cnf_file, nv, nc, gc = encode_ghost_carries(n_carry, n_rounds, mode, timeout)
        print(f"  {nv} vars, {nc} clauses, {gc} ghost clauses", flush=True)

        to = min(timeout, 300) if mode == "sr59" else timeout
        print(f"  Running Kissat ({to}s)...", flush=True)

        t0 = time.time()
        r = subprocess.run(["timeout", str(to), "kissat", "-q", cnf_file],
                           capture_output=True, text=True, timeout=to + 30)
        elapsed = time.time() - t0

        if r.returncode == 10:
            status = "SAT"
            print(f"  [!!!] SAT in {elapsed:.1f}s!", flush=True)
        elif r.returncode == 20:
            status = "UNSAT"
            print(f"  [-] UNSAT in {elapsed:.1f}s — ghost carry assumption incompatible!", flush=True)
        else:
            status = "TIMEOUT"
            print(f"  [!] TIMEOUT after {elapsed:.1f}s", flush=True)

        results.append((label, n_carry, n_rounds, mode, status, elapsed, gc))

        # If sr=59 baseline with ghost carries is UNSAT, ghost carries are too strong
        if mode == "sr59" and status == "UNSAT":
            print(f"\n  Ghost carries make even sr=59 UNSAT!", flush=True)
            print(f"  The constraint 'carries must match' is too restrictive.", flush=True)
            print(f"  Reducing carry bits or rounds...", flush=True)
            break

        # If sr=60 SAT, we're done!
        if mode == "sr60" and status == "SAT":
            print(f"\n  [!!!] SR=60 COLLISION VIA GHOST CARRIES!", flush=True)
            break

    print(f"\n{'='*70}", flush=True)
    print("RESULTS SUMMARY", flush=True)
    print(f"{'='*70}", flush=True)
    for label, nc, nr, mode, status, elapsed, gc in results:
        print(f"  {status:>7} {elapsed:7.1f}s  gc={gc:4d}  {label}", flush=True)


if __name__ == "__main__":
    main()
