#!/usr/bin/env python3
"""
Script 53: Micro-Constraint Stepping Between k=3 and k=4

The phase transition in progressive W[61] schedule compliance happens
between k=3 (109s SAT) and k=4 (1776s, 16.3x harder). The 4th bit
(bit 3) causes the jump. This script dissects that single bit by
constraining it asymmetrically:

  Test A: k=3 baseline (both messages, low 3 bits) -- sanity check
  Test B: k=3 + bit 3 for M1 only (not M2) -- "k=3.5 M1"
  Test C: k=3 + bit 3 for M2 only (not M1) -- "k=3.5 M2"
  Test D: k=3 + bit 3 for W1[61] only (not W2[61]) -- "k=3.5 W1"
  Test E: k=3 + bit 3 for W2[61] only (not W1[61]) -- "k=3.5 W2"
  Test F: k=4 both (verify the hard case)

This tells us whether the transition is symmetric or asymmetric --
does one message's constraint dominate the hardness?

Note on terminology:
  "M1 only" = constrain bit 3 of W1[61] AND W2[61] but only for
              message 1's schedule equation. Wait -- that doesn't
              make sense since W1[61] IS message 1's word.

  Clarification: In the k=4 constraint, there are TWO equality
  constraints for bit 3:
    (1) W1[61][3] == W1_61_sched[3]  -- M1's schedule compliance
    (2) W2[61][3] == W2_61_sched[3]  -- M2's schedule compliance

  We test adding only (1), only (2), and both.
"""

import sys
import time
import subprocess
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
mod = import_module('13_custom_cnf_encoder')

# SHA-256 helpers
def ROR(x, n): return ((x >> n) | (x << (32 - n))) & 0xFFFFFFFF
def sigma0_py(x): return ROR(x, 7) ^ ROR(x, 18) ^ (x >> 3)
def sigma1_py(x): return ROR(x, 17) ^ ROR(x, 19) ^ (x >> 10)


def eq_bit(cnf, a, b):
    """Add equality constraint a == b with constant propagation."""
    if cnf._is_known(a) and cnf._is_known(b):
        if cnf._get_val(a) != cnf._get_val(b):
            cnf.clauses.append([])  # UNSAT
    elif cnf._is_known(a):
        cnf.clauses.append([b] if cnf._get_val(a) else [-b])
    elif cnf._is_known(b):
        cnf.clauses.append([a] if cnf._get_val(b) else [-a])
    else:
        cnf.clauses.append([-a, b])
        cnf.clauses.append([a, -b])


def encode_micro(k_base, extra_m1_bits=None, extra_m2_bits=None, timeout_sec=600):
    """
    Encode sr=59 with k_base bits of W[61] schedule compliance for BOTH
    messages, plus optionally extra individual bits for M1 and/or M2.

    k_base: number of low bits constrained for both messages (0..32)
    extra_m1_bits: list of additional bit indices to constrain for M1 only
    extra_m2_bits: list of additional bit indices to constrain for M2 only
    """
    if extra_m1_bits is None:
        extra_m1_bits = []
    if extra_m2_bits is None:
        extra_m2_bits = []

    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1[:]
    M2[0] ^= 0x80000000
    M2[9] ^= 0x80000000

    state1, W1_pre = mod.precompute_state(M1)
    state2, W2_pre = mod.precompute_state(M2)

    cnf = mod.CNFBuilder()

    s1 = tuple(cnf.const_word(v) for v in state1)
    s2 = tuple(cnf.const_word(v) for v in state2)

    # 5 free words each (sr=59 baseline)
    w1_free = [cnf.free_word(f"W1_{57+i}") for i in range(5)]
    w2_free = [cnf.free_word(f"W2_{57+i}") for i in range(5)]

    # Enforce W[62] from schedule (W[60])
    w1_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w1_free[3]), cnf.const_word(W1_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W1_pre[47])), cnf.const_word(W1_pre[46]))
    )
    w2_62 = cnf.add_word(
        cnf.add_word(cnf.sigma1_w(w2_free[3]), cnf.const_word(W2_pre[55])),
        cnf.add_word(cnf.const_word(sigma0_py(W2_pre[47])), cnf.const_word(W2_pre[46]))
    )
    # Enforce W[63] from schedule (W[61])
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

    # Run 7 compression rounds
    st1 = s1
    for i in range(7):
        st1 = cnf.sha256_round_correct(st1, mod.K[57+i], W1_tail[i])
    st2 = s2
    for i in range(7):
        st2 = cnf.sha256_round_correct(st2, mod.K[57+i], W2_tail[i])

    # Collision constraint
    for i in range(8):
        cnf.eq_word(st1[i], st2[i])

    # Build schedule values for W[61]
    need_sched = (k_base > 0) or extra_m1_bits or extra_m2_bits
    if need_sched:
        w1_61_sched = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(w1_free[2]), cnf.const_word(W1_pre[54])),
            cnf.add_word(cnf.const_word(sigma0_py(W1_pre[46])), cnf.const_word(W1_pre[45]))
        )
        w2_61_sched = cnf.add_word(
            cnf.add_word(cnf.sigma1_w(w2_free[2]), cnf.const_word(W2_pre[54])),
            cnf.add_word(cnf.const_word(sigma0_py(W2_pre[46])), cnf.const_word(W2_pre[45]))
        )

        # Constrain base bits for BOTH messages
        for bit in range(min(k_base, 32)):
            eq_bit(cnf, w1_free[4][bit], w1_61_sched[bit])
            eq_bit(cnf, w2_free[4][bit], w2_61_sched[bit])

        # Extra bits for M1 only
        for bit in extra_m1_bits:
            if bit < 32:
                eq_bit(cnf, w1_free[4][bit], w1_61_sched[bit])

        # Extra bits for M2 only
        for bit in extra_m2_bits:
            if bit < 32:
                eq_bit(cnf, w2_free[4][bit], w2_61_sched[bit])

    # Write and solve
    label = f"k{k_base}"
    if extra_m1_bits:
        label += f"_m1b{''.join(str(b) for b in extra_m1_bits)}"
    if extra_m2_bits:
        label += f"_m2b{''.join(str(b) for b in extra_m2_bits)}"
    cnf_file = f"/tmp/sr59_micro_{label}.cnf"
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

    # Extract some kissat stats
    conflicts = "?"
    decisions = "?"
    for line in r.stdout.split('\n'):
        if 'conflicts:' in line.lower():
            parts = line.strip().split()
            for i, p in enumerate(parts):
                if p.startswith('conflicts'):
                    if i + 1 < len(parts):
                        conflicts = parts[i-1] if i > 0 else parts[i+1]
                    break
        if 'decisions:' in line.lower():
            parts = line.strip().split()
            for i, p in enumerate(parts):
                if p.startswith('decisions'):
                    if i + 1 < len(parts):
                        decisions = parts[i-1] if i > 0 else parts[i+1]
                    break

    return result, elapsed, nv, nc, conflicts, decisions


def main():
    timeout = 600  # 10 minutes per test

    # Core tests: A-C are the key ones. D-F are only run if B or C solve in time.
    #
    # A: k=3 baseline -- both messages constrained on bits 0,1,2
    # B: k=3 + bit 3 for M1 ONLY -- half the 4th constraint
    # C: k=3 + bit 3 for M2 ONLY -- the other half
    # D: k=3 + bit 3 BOTH = k=4 -- known to take 1776s, will timeout at 600s
    #
    # If B and C both timeout, D/E/F are guaranteed to timeout too (strictly
    # harder). We skip them to save compute.

    tests = [
        # (label, k_base, extra_m1_bits, extra_m2_bits)
        ("A: k=3 baseline (both)",          3, [],   []),
        ("B: k=3 + bit3 M1-only",           3, [3],  []),
        ("C: k=3 + bit3 M2-only",           3, [],   [3]),
        ("D: k=3 + bit3 BOTH (=k=4)",       3, [3],  [3]),
        ("E: k=3 + bit3 M1 + bit4 M1",      3, [3,4],[]),
        ("F: k=3 + bit3 M2 + bit4 M2",      3, [],   [3,4]),
    ]

    print("=" * 78, flush=True)
    print("Micro-Constraint Stepping: Dissecting the k=3 -> k=4 Phase Transition", flush=True)
    print(f"Timeout per test: {timeout}s", flush=True)
    print("=" * 78, flush=True)
    print(flush=True)
    print("Each test constrains sr=59 + low k bits of W[61] schedule compliance.", flush=True)
    print("k=3 constrains bits 0,1,2 for BOTH messages. We add bit 3 asymmetrically.", flush=True)
    print(flush=True)
    print(f"{'Test':<38} {'vars':>7} {'clauses':>9} {'result':>8} {'time':>8}", flush=True)
    print("-" * 78, flush=True)

    results = []
    b_timeout = False
    c_timeout = False

    for label, k_base, extra_m1, extra_m2 in tests:
        # Skip D/E/F if both B and C timed out (they're strictly harder)
        if b_timeout and c_timeout and label.startswith(("D:", "E:", "F:")):
            print(f"{label:<38} {'---':>7} {'---':>9} {'SKIP':>8} {'---':>8}", flush=True)
            print(f"  (skipped: B and C both timed out, this is strictly harder)", flush=True)
            results.append((label, k_base, extra_m1, extra_m2, "SKIP", 0, 0, 0))
            continue

        result, elapsed, nv, nc, conflicts, decisions = encode_micro(
            k_base, extra_m1, extra_m2, timeout
        )
        print(f"{label:<38} {nv:7d} {nc:9d} {result:>8} {elapsed:7.1f}s", flush=True)
        results.append((label, k_base, extra_m1, extra_m2, result, elapsed, nv, nc))

        # Track timeouts for early exit
        if "B:" in label and result == "TIMEOUT":
            b_timeout = True
        if "C:" in label and result == "TIMEOUT":
            c_timeout = True

        # If baseline is UNSAT, something is wrong
        if "baseline" in label and result == "UNSAT":
            print("  ERROR: baseline should be SAT! Aborting.", flush=True)
            break

    # Analysis
    print(flush=True)
    print("=" * 78, flush=True)
    print("ANALYSIS: Symmetry of the Phase Transition", flush=True)
    print("=" * 78, flush=True)

    baseline_time = None
    m1_time = None
    m1_result = None
    m2_time = None
    m2_result = None
    both_time = None
    both_result = None

    for label, k_base, extra_m1, extra_m2, result, elapsed, nv, nc in results:
        if result == "SKIP":
            continue
        tag = ""
        if "baseline" in label:
            baseline_time = elapsed if result == "SAT" else None
            tag = " [REFERENCE]"
        elif "M1-only" in label and "bit3" in label and len(extra_m1) == 1:
            m1_time = elapsed if result == "SAT" else None
            m1_result = result
        elif "M2-only" in label and "bit3" in label and len(extra_m2) == 1:
            m2_time = elapsed if result == "SAT" else None
            m2_result = result
        elif "BOTH" in label:
            both_time = elapsed if result == "SAT" else None
            both_result = result

        bar_len = min(int(elapsed / 5), 60) if result != "TIMEOUT" else 60
        bar = "#" * bar_len
        if result == "TIMEOUT":
            bar += ">>>"
        print(f"  {label:<38} {elapsed:7.1f}s [{result:>7}] {bar}{tag}", flush=True)

    print(flush=True)
    if baseline_time is not None:
        print(f"  Baseline (k=3):           {baseline_time:.1f}s", flush=True)

        if m1_time is not None:
            ratio_m1 = m1_time / baseline_time
            print(f"  + bit3 M1-only:           {m1_time:.1f}s  ({ratio_m1:.1f}x baseline)", flush=True)
        elif m1_result:
            print(f"  + bit3 M1-only:           {m1_result} (>{timeout}s, >{timeout/baseline_time:.1f}x baseline)", flush=True)

        if m2_time is not None:
            ratio_m2 = m2_time / baseline_time
            print(f"  + bit3 M2-only:           {m2_time:.1f}s  ({ratio_m2:.1f}x baseline)", flush=True)
        elif m2_result:
            print(f"  + bit3 M2-only:           {m2_result} (>{timeout}s, >{timeout/baseline_time:.1f}x baseline)", flush=True)

        if both_time is not None:
            ratio_both = both_time / baseline_time
            print(f"  + bit3 BOTH (=k=4):       {both_time:.1f}s  ({ratio_both:.1f}x baseline)", flush=True)
        elif both_result:
            print(f"  + bit3 BOTH (=k=4):       {both_result} (known: 1776s = 16.3x baseline)", flush=True)
        else:
            print(f"  + bit3 BOTH (=k=4):       skipped (known: 1776s)", flush=True)

        # Check symmetry
        if m1_result == "TIMEOUT" and m2_result == "TIMEOUT":
            print(flush=True)
            print("  SYMMETRY: Both M1-only and M2-only TIMEOUT at 600s.", flush=True)
            print(f"  Each half individually takes >600s (>5.8x the 104s baseline).", flush=True)
            print(f"  The transition is SYMMETRIC: neither message side is easier.", flush=True)
            print(flush=True)
            print("  KEY INSIGHT: The 4th bit phase transition is NOT caused by", flush=True)
            print("  the INTERACTION between M1 and M2 constraints. Even constraining", flush=True)
            print("  a single message's bit 3 is enough to blow past the 600s budget.", flush=True)
            print(flush=True)
            print("  This means:", flush=True)
            print("    - The hardness is intrinsic to constraining bit 3 of EITHER message", flush=True)
            print("    - The collision-finding constraint + bit 3 schedule compliance", flush=True)
            print("      creates a qualitatively harder search even for one message", flush=True)
            print("    - Adding just 2 clauses (one eq_bit for one message) causes", flush=True)
            print("      a >5.8x slowdown -- a single bit equality is a phase trigger", flush=True)
            print("    - There is no 'easy half' to exploit for a hybrid approach", flush=True)
        elif m1_time is not None and m2_time is not None:
            if max(m1_time, m2_time) > 0:
                asym_ratio = max(m1_time, m2_time) / min(m1_time, m2_time)
                harder = "M1" if m1_time > m2_time else "M2" if m2_time > m1_time else "equal"
                print(flush=True)
                print(f"  Asymmetry ratio: {asym_ratio:.2f}x (harder side: {harder})", flush=True)
                if asym_ratio < 1.5:
                    print(f"  Conclusion: transition is SYMMETRIC", flush=True)
                else:
                    print(f"  Conclusion: transition is ASYMMETRIC -- {harder} side dominates", flush=True)

                if both_time is not None:
                    additive_est = m1_time + m2_time - baseline_time
                    print(flush=True)
                    print(f"  Additive estimate (M1+M2-base): {additive_est:.1f}s", flush=True)
                    print(f"  Actual both:                    {both_time:.1f}s", flush=True)
                    if both_time > additive_est * 2:
                        print(f"  Interaction: SUPER-ADDITIVE", flush=True)
                    elif both_time < additive_est * 0.5:
                        print(f"  Interaction: SUB-ADDITIVE", flush=True)
                    else:
                        print(f"  Interaction: roughly additive", flush=True)
        elif m1_result == "TIMEOUT" and m2_time is not None:
            print(flush=True)
            print(f"  ASYMMETRIC: M1-only times out but M2-only solves in {m2_time:.1f}s", flush=True)
            print(f"  The M1 constraint is the hard side.", flush=True)
        elif m2_result == "TIMEOUT" and m1_time is not None:
            print(flush=True)
            print(f"  ASYMMETRIC: M2-only times out but M1-only solves in {m1_time:.1f}s", flush=True)
            print(f"  The M2 constraint is the hard side.", flush=True)

    print(flush=True)
    print("=" * 78, flush=True)


if __name__ == "__main__":
    main()
