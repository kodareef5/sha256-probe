#!/usr/bin/env python3
"""
Script 29: Asymmetric Schedule Compliance — The Slack Thief

Standard sr=60: BOTH messages enforce W[61] via schedule equation.
This gives 4 free words x 2 messages x 32 bits = 256 bits = 0 slack.

Asymmetric sr=60: Only M1 enforces W[61]. M2's W[61] is FREE.
This gives: M1: 4 free words (128 bits) + M2: 5 free words (160 bits) = 288 bits.
Collision: 256 bits. Slack: 32 bits!

The schedule compliance is: M1 has sr=60 (44/48 equations). M2 has sr=59 (43/48).
The COLLISION still covers all 64 rounds. The final hash match is still real.

If this solves, we've found a collision where:
  - M1 satisfies 44 schedule equations (sr=60 for M1)
  - M2 satisfies 43 schedule equations (sr=59 for M2)
  - H(M1) = H(M2) across all 64 rounds

This is arguably MORE interesting than symmetric sr=60 because it
shows schedule compliance need not be uniform across messages.
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')


def encode_asymmetric_sr60(timeout_sec=3600):
    """
    M1: sr=60 (W[57..60] free, W[61..63] enforced)
    M2: sr=59 (W[57..61] free, W[62..63] enforced)
    Collision: H1 == H2 over all 64 rounds
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

    # M1: 4 free words (sr=60)
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(4)]

    # M2: 5 free words (sr=59 — W[61] is FREE for M2!)
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(5)]

    # M1 schedule: W[61] enforced from W[59]
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45])))

    # M1: W[62] from W[60], W[63] from W[61]
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[3]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46])))
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_61), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47])))

    W1_tail = list(w1_free) + [w1_61, w1_62, w1_63]

    # M2: W[62] from W[60], W[63] from W[61] (W[61] is FREE for M2)
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[3]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46])))
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[4]), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47])))

    W2_tail = list(w2_free) + [w2_62, w2_63]

    # Compression rounds
    st1 = s1
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, enc.K[57+i], W1_tail[i])
    st2 = s2
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, enc.K[57+i], W2_tail[i])

    # Collision
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    cnf_file = "/tmp/sr60_asymmetric.cnf"
    cnf.write_dimacs(cnf_file)
    nv = cnf.next_var - 1
    nc = len(cnf.clauses)

    print(f"\nAsymmetric sr=60:", flush=True)
    print(f"  M1: 4 free words (sr=60, 128 bits)", flush=True)
    print(f"  M2: 5 free words (sr=59, 160 bits)", flush=True)
    print(f"  Total freedom: 288 bits", flush=True)
    print(f"  Collision: 256 bits", flush=True)
    print(f"  Slack: 32 bits (same as k=16 progressive!)", flush=True)
    print(f"  {nv} vars, {nc} clauses", flush=True)

    print(f"\nRunning Kissat ({timeout_sec}s)...", flush=True)
    t0 = time.time()
    r = subprocess.run(["timeout", str(timeout_sec), "kissat", "-q", cnf_file],
                       capture_output=True, text=True, timeout=timeout_sec + 30)
    elapsed = time.time() - t0

    if r.returncode == 10:
        print(f"[!!!] SAT in {elapsed:.1f}s!", flush=True)
        print(f"ASYMMETRIC SR=60 COLLISION FOUND!", flush=True)
        print(f"M1 has sr=60 (44/48 schedule equations)", flush=True)
        print(f"M2 has sr=59 (43/48 schedule equations)", flush=True)
        return "SAT", elapsed
    elif r.returncode == 20:
        print(f"[-] UNSAT in {elapsed:.1f}s", flush=True)
        return "UNSAT", elapsed
    else:
        print(f"[!] TIMEOUT after {elapsed:.1f}s", flush=True)
        return "TIMEOUT", elapsed


def main():
    timeout = int(sys.argv[1]) if len(sys.argv) > 1 else 3600

    print("=" * 60, flush=True)
    print("Asymmetric Schedule: sr=60 for M1, sr=59 for M2", flush=True)
    print("The 'Slack Thief' — steal slack from one message", flush=True)
    print("=" * 60, flush=True)

    result, elapsed = encode_asymmetric_sr60(timeout)

    if result == "SAT":
        print(f"\n[!!!] This proves schedule compliance need not be symmetric!", flush=True)
    elif result == "TIMEOUT":
        print(f"\n  32 bits of slack (from asymmetry) still not enough.", flush=True)
        print(f"  Compare: symmetric k=16 (32 bits slack) also timed out at 600s.", flush=True)
        print(f"  The slack distribution matters, not just the total.", flush=True)


if __name__ == "__main__":
    main()
