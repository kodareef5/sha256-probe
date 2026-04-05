#!/usr/bin/env python3
"""
Script 17: Differential Trail Hinting for sr=60

Uses the verified sr=59 collision's differential trail to guide the sr=60
SAT solver. Instead of letting Kissat search blindly, we constrain the
XOR differences of the free words (or state registers) to follow the
known-good sr=59 path.

Approach:
  1. Extract the exact dW[57..60] XOR differences from the sr=59 solution
  2. Add constraints to the sr=60 instance forcing W1[r] XOR W2[r] = dW[r]
     for selected rounds r
  3. This halves the effective free variables (W2 determined from W1 + diff)
     while potentially guiding the solver toward a compatible solution

Risk: if the sr=59 trail is incompatible with any sr=60 solution, these
constraints make the problem UNSAT. We test progressively:
  - Fix diff at round 57 only (32 bits constrained)
  - Fix diff at rounds 57-58 (64 bits)
  - Fix diff at rounds 57-59 (96 bits)
  - Fix diff at rounds 57-60 (128 bits = maximum, W2 fully determined by W1)
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')

# sr=59 verified free words (from the collision certificate)
W1_FREE_SR59 = [0x35ff2fce, 0x091194cf, 0x92290bc7, 0xc136a254, 0xc6841268]
W2_FREE_SR59 = [0x0c16533d, 0x8792091f, 0x93a0f3b6, 0x8b270b72, 0x40110184]

# XOR differences
DW_SR59 = [w1 ^ w2 for w1, w2 in zip(W1_FREE_SR59, W2_FREE_SR59)]


def encode_sr60_with_trail_hint(n_fixed_rounds, timeout_sec=600):
    """
    Encode sr=60 but constrain dW[57..57+n_fixed_rounds-1] to match sr=59 trail.

    n_fixed_rounds=0: pure sr=60 (baseline)
    n_fixed_rounds=1: fix dW[57] only
    n_fixed_rounds=2: fix dW[57] and dW[58]
    n_fixed_rounds=3: fix dW[57..59]
    n_fixed_rounds=4: fix dW[57..60] (W2 fully determined from W1)
    """
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1[:]
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    cnf = enc.CNFBuilder()

    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    # Free variables
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(4)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(4)]

    # Trail hint: constrain W1[r] XOR W2[r] = DW_SR59[r-57]
    for r in range(n_fixed_rounds):
        diff = DW_SR59[r]
        for bit in range(32):
            # W1[r][bit] XOR W2[r][bit] = diff_bit
            diff_bit = (diff >> bit) & 1
            a = w1_free[r][bit]
            b = w2_free[r][bit]
            if diff_bit:
                # a XOR b = 1 => a != b
                cnf.clauses.append([a, b])      # at least one true
                cnf.clauses.append([-a, -b])     # at least one false
            else:
                # a XOR b = 0 => a == b
                cnf.clauses.append([-a, b])
                cnf.clauses.append([a, -b])

    # Schedule enforcement (same as sr=60)
    w1_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45]))
    )
    w2_61 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45]))
    )
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[3]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46]))
    )
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[3]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46]))
    )
    w1_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_61), cnf.const_word(W1_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W1_pre[48])), cnf.const_word(W1_pre[47]))
    )
    w2_63 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_61), cnf.const_word(W2_pre[56])),
        cnf.add_word(cnf.const_word(enc.sigma0_py(W2_pre[48])), cnf.const_word(W2_pre[47]))
    )

    W1_tail = list(w1_free) + [w1_61, w1_62, w1_63]
    W2_tail = list(w2_free) + [w2_61, w2_62, w2_63]

    # Compression rounds 57-63
    st1 = s1
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, enc.K[57+i], W1_tail[i])
    st2 = s2
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, enc.K[57+i], W2_tail[i])

    # Collision constraint
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    # Write and solve
    cnf_file = f"/tmp/sr60_trail_{n_fixed_rounds}.cnf"
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

    print("=" * 70, flush=True)
    print("Differential Trail Hinting for sr=60", flush=True)
    print("=" * 70, flush=True)

    # Show the sr=59 differential trail
    print("\nsr=59 differential trail (XOR differences of free words):", flush=True)
    for i in range(4):
        print(f"  dW[{57+i}] = 0x{DW_SR59[i]:08x}", flush=True)
    print(f"  dW[61]  = 0x{DW_SR59[4]:08x} (not used in sr=60, W[61] is enforced)", flush=True)

    print(f"\nFixing progressively more trail differences:", flush=True)
    print(f"{'n_fixed':>8} {'free_bits':>10} {'constrained':>12} {'vars':>7} {'clauses':>9} {'result':>8} {'time':>8}", flush=True)
    print("-" * 75, flush=True)

    results = []
    for n in [0, 1, 2, 3, 4]:
        free_bits = 256 - n * 64  # each fixed round removes 32 bits from W2's freedom
        constrained = n * 64

        result, elapsed, nv, nc = encode_sr60_with_trail_hint(n, timeout)
        print(f"{n:8d} {free_bits:10d} {constrained:12d} {nv:7d} {nc:9d} {result:>8} {elapsed:7.1f}s", flush=True)
        results.append((n, result, elapsed))

        if result == "UNSAT":
            print(f"  UNSAT: sr=59 trail at {n} rounds is INCOMPATIBLE with sr=60.", flush=True)
        elif result == "SAT":
            print(f"  [!!!] SOLVED with trail hint at {n} round(s)!", flush=True)
            break

    print("\n" + "=" * 70, flush=True)
    print("ANALYSIS", flush=True)
    print("=" * 70, flush=True)

    for n, result, elapsed in results:
        marker = "" if result == "TIMEOUT" else (" <-- BREAKTHROUGH!" if result == "SAT" else " <-- trail incompatible")
        print(f"  {n} fixed rounds: {result:>8} {elapsed:7.1f}s{marker}", flush=True)

    # Check if any hit UNSAT
    unsat_rounds = [n for n, r, _ in results if r == "UNSAT"]
    if unsat_rounds:
        print(f"\n  The sr=59 trail is incompatible with sr=60 starting at round {min(unsat_rounds)}.", flush=True)
        print(f"  This means sr=60 solutions (if they exist) use a DIFFERENT differential path.", flush=True)
    elif all(r == "TIMEOUT" for _, r, _ in results):
        print(f"\n  No trail hint was sufficient to solve sr=60 within {timeout}s.", flush=True)
        print(f"  Consider: longer timeout, or Cube-and-Conquer with trail-biased partitions.", flush=True)


if __name__ == "__main__":
    main()
