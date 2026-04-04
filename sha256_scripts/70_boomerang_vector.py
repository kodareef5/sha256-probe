#!/usr/bin/env python3
"""
Script 70: Boomerang Vector Analysis (W57-W60)

Extends the depth-1 boomerang gap (h60 vs d60 demanding different dW57)
to a full vector across depths 1-4:

  Depth 1: h60=e57, d60=a57         -> constrain dW57
  Depth 2: g60=e58, c60=a58         -> constrain (dW57, dW58)
  Depth 3: f60=e59, b60=a59         -> constrain (dW57, dW58, dW59)
  Depth 4: e60, a60                 -> constrain (dW57, dW58, dW59, dW60)

At each depth, a pair of round-60 registers must collide. Each pair
gives a required dW_k value (once all prior dW are fixed). If the two
registers in a pair demand DIFFERENT dW_k, there is a gap at that depth.

Method: fix dW57 to the h60-required value (ignoring the d60 conflict),
propagate forward, then measure the gap at each subsequent depth.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')

M32 = 0xFFFFFFFF


def sha256_round(state, K_i, W_i):
    """One SHA-256 compression round. Returns new (a,b,c,d,e,f,g,h)."""
    a, b, c, d, e, f, g, h = state
    T1 = (h + enc.Sigma1_py(e) + enc.Ch_py(e, f, g) + K_i + W_i) & M32
    T2 = (enc.Sigma0_py(a) + enc.Maj_py(a, b, c)) & M32
    return ((T1 + T2) & M32, a, b, c, (d + T1) & M32, e, f, g)


def hw(x):
    return bin(x & M32).count('1')


def depth1_analysis(state1, state2):
    """
    Depth 1: h60=e57, d60=a57. Both depend only on W57.
    e57 = C_T1 + W57  (where C_T1 = h + Sig1(e) + Ch(e,f,g) + K[57])
    a57 = C_T1 + W57 + T2  (since a = T1 + T2)
    But e57 = d56 + T1 = d + C_T1_partial + W57
    Actually: e57 = d + T1 = d + (h + Sig1(e) + Ch + K + W57)
    """
    a1, b1, c1, d1, e1, f1, g1, h1 = state1
    a2, b2, c2, d2, e2, f2, g2, h2 = state2

    # C56_e: constant part of e57 = d + h + Sig1(e) + Ch(e,f,g) + K[57] + W57
    C56_e_1 = (d1 + h1 + enc.Sigma1_py(e1) + enc.Ch_py(e1, f1, g1) + enc.K[57]) & M32
    C56_e_2 = (d2 + h2 + enc.Sigma1_py(e2) + enc.Ch_py(e2, f2, g2) + enc.K[57]) & M32

    # C56_a: constant part of a57 = T1 + T2
    C_T1_1 = (h1 + enc.Sigma1_py(e1) + enc.Ch_py(e1, f1, g1) + enc.K[57]) & M32
    C_T1_2 = (h2 + enc.Sigma1_py(e2) + enc.Ch_py(e2, f2, g2) + enc.K[57]) & M32
    T2_1 = (enc.Sigma0_py(a1) + enc.Maj_py(a1, b1, c1)) & M32
    T2_2 = (enc.Sigma0_py(a2) + enc.Maj_py(a2, b2, c2)) & M32
    C56_a_1 = (C_T1_1 + T2_1) & M32
    C56_a_2 = (C_T1_2 + T2_2) & M32

    # h60=e57 collision: C56_e_1 + W1[57] = C56_e_2 + W2[57]
    # => dW57 = C56_e_2 - C56_e_1
    req_dW57_h = (C56_e_2 - C56_e_1) & M32

    # d60=a57 collision: C56_a_1 + W1[57] = C56_a_2 + W2[57]
    # => dW57 = C56_a_2 - C56_a_1
    req_dW57_d = (C56_a_2 - C56_a_1) & M32

    gap = (req_dW57_h ^ req_dW57_d)
    return req_dW57_h, req_dW57_d, gap


def compute_round_state(state, round_idx, W_val):
    """Compute state after one round with given W value."""
    return sha256_round(state, enc.K[round_idx], W_val)


def main():
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1[:]; M2[0] ^= 0x80000000; M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    print("=" * 70, flush=True)
    print("BOOMERANG VECTOR: Depth 1-4 Gap Analysis (W57-W60)", flush=True)
    print("=" * 70, flush=True)
    print(f"M[0] = 0x{M1[0]:08x}", flush=True)
    print(f"Diff: M1[0]^=0x80000000, M1[9]^=0x80000000", flush=True)

    # ===== DEPTH 1 =====
    print(f"\n{'='*70}", flush=True)
    print("DEPTH 1: h60=e57 vs d60=a57 (depends on dW57 only)", flush=True)
    print("=" * 70, flush=True)

    req_dW57_h, req_dW57_d, gap1 = depth1_analysis(state1, state2)

    print(f"  Required dW57 for h60 collision: 0x{req_dW57_h:08x}", flush=True)
    print(f"  Required dW57 for d60 collision: 0x{req_dW57_d:08x}", flush=True)
    print(f"  XOR gap: 0x{gap1:08x}  (HW = {hw(gap1)})", flush=True)
    print(f"  Additive gap: 0x{(req_dW57_h - req_dW57_d) & M32:08x}", flush=True)

    # For depths 2-4, we fix dW57 to the h60-required value and propagate.
    # The idea: h60 collision is satisfied. d60 collision is violated (gap1 != 0).
    # Now propagate to round 57 state, then analyze depth 2.

    # Use a concrete W1[57] value and derive W2[57] from the h60 requirement.
    W1_57 = 0x00000000
    W2_57 = (W1_57 - req_dW57_h) & M32

    s57_1 = compute_round_state(state1, 57, W1_57)
    s57_2 = compute_round_state(state2, 57, W2_57)

    print(f"\n  State diff at Round 57 (dW57 fixed for h60):", flush=True)
    reg_names = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
    for i in range(8):
        d = s57_1[i] ^ s57_2[i]
        tag = " <-- ZERO (h60 satisfied)" if i == 4 else ""
        if i == 0 and d != 0:
            tag = f" <-- d60 gap, HW={hw(d)}"
        elif i == 0 and d == 0:
            tag = " <-- ZERO (d60 also satisfied!)"
        print(f"    d{reg_names[i]}57 = 0x{d:08x} (HW={hw(d)}){tag}", flush=True)

    # Verify h60 is satisfied (e57_1 == e57_2)
    assert s57_1[4] == s57_2[4], "h60 not satisfied despite fixing dW57!"

    # ===== DEPTH 2 =====
    # g60 = e58, c60 = a58. Both depend on round-57 state AND W58.
    # e58 = d57 + T1_58 = d57 + h57 + Sig1(e57) + Ch(e57,f57,g57) + K[58] + W58
    # a58 = T1_58 + T2_58
    #
    # For g60 collision: e58_1 == e58_2
    # For c60 collision: a58_1 == a58_2
    # Each imposes a constraint on W58 (given the round-57 state diff).

    print(f"\n{'='*70}", flush=True)
    print("DEPTH 2: g60=e58 vs c60=a58 (depends on dW57, dW58)", flush=True)
    print("=" * 70, flush=True)

    # Constants for e58 = d57 + h57 + Sig1(e57) + Ch(e57,f57,g57) + K[58] + W58
    def C_e(s):
        a, b, c, d, e, f, g, h = s
        return (d + h + enc.Sigma1_py(e) + enc.Ch_py(e, f, g) + enc.K[58]) & M32

    def C_a(s):
        a, b, c, d, e, f, g, h = s
        T1_const = (h + enc.Sigma1_py(e) + enc.Ch_py(e, f, g) + enc.K[58]) & M32
        T2 = (enc.Sigma0_py(a) + enc.Maj_py(a, b, c)) & M32
        return (T1_const + T2) & M32

    Ce58_1 = C_e(s57_1)
    Ce58_2 = C_e(s57_2)
    Ca58_1 = C_a(s57_1)
    Ca58_2 = C_a(s57_2)

    req_dW58_g = (Ce58_2 - Ce58_1) & M32  # g60 collision
    req_dW58_c = (Ca58_2 - Ca58_1) & M32  # c60 collision

    gap2 = req_dW58_g ^ req_dW58_c

    print(f"  Required dW58 for g60 collision: 0x{req_dW58_g:08x}", flush=True)
    print(f"  Required dW58 for c60 collision: 0x{req_dW58_c:08x}", flush=True)
    print(f"  XOR gap: 0x{gap2:08x}  (HW = {hw(gap2)})", flush=True)
    print(f"  Additive gap: 0x{(req_dW58_g - req_dW58_c) & M32:08x}", flush=True)

    # Propagate to round 58 (fix dW58 for g60 collision)
    W1_58 = 0x00000000
    W2_58 = (W1_58 - req_dW58_g) & M32

    s58_1 = compute_round_state(s57_1, 58, W1_58)
    s58_2 = compute_round_state(s57_2, 58, W2_58)

    print(f"\n  State diff at Round 58 (dW58 fixed for g60):", flush=True)
    for i in range(8):
        d = s58_1[i] ^ s58_2[i]
        tag = ""
        if i == 4 and d == 0: tag = " <-- ZERO (g60 satisfied)"
        if i == 4 and d != 0: tag = f" <-- g60 NOT satisfied??"
        if i == 0 and d == 0: tag = " <-- ZERO (c60 also satisfied!)"
        if i == 0 and d != 0: tag = f" <-- c60 gap, HW={hw(d)}"
        print(f"    d{reg_names[i]}58 = 0x{d:08x} (HW={hw(d)}){tag}", flush=True)

    # ===== DEPTH 3 =====
    # f60 = e59, b60 = a59
    print(f"\n{'='*70}", flush=True)
    print("DEPTH 3: f60=e59 vs b60=a59 (depends on dW57, dW58, dW59)", flush=True)
    print("=" * 70, flush=True)

    def C_e59(s):
        a, b, c, d, e, f, g, h = s
        return (d + h + enc.Sigma1_py(e) + enc.Ch_py(e, f, g) + enc.K[59]) & M32

    def C_a59(s):
        a, b, c, d, e, f, g, h = s
        T1_const = (h + enc.Sigma1_py(e) + enc.Ch_py(e, f, g) + enc.K[59]) & M32
        T2 = (enc.Sigma0_py(a) + enc.Maj_py(a, b, c)) & M32
        return (T1_const + T2) & M32

    Ce59_1 = C_e59(s58_1)
    Ce59_2 = C_e59(s58_2)
    Ca59_1 = C_a59(s58_1)
    Ca59_2 = C_a59(s58_2)

    req_dW59_f = (Ce59_2 - Ce59_1) & M32
    req_dW59_b = (Ca59_2 - Ca59_1) & M32

    gap3 = req_dW59_f ^ req_dW59_b

    print(f"  Required dW59 for f60 collision: 0x{req_dW59_f:08x}", flush=True)
    print(f"  Required dW59 for b60 collision: 0x{req_dW59_b:08x}", flush=True)
    print(f"  XOR gap: 0x{gap3:08x}  (HW = {hw(gap3)})", flush=True)
    print(f"  Additive gap: 0x{(req_dW59_f - req_dW59_b) & M32:08x}", flush=True)

    # Propagate to round 59
    W1_59 = 0x00000000
    W2_59 = (W1_59 - req_dW59_f) & M32

    s59_1 = compute_round_state(s58_1, 59, W1_59)
    s59_2 = compute_round_state(s58_2, 59, W2_59)

    print(f"\n  State diff at Round 59 (dW59 fixed for f60):", flush=True)
    for i in range(8):
        d = s59_1[i] ^ s59_2[i]
        tag = ""
        if i == 4 and d == 0: tag = " <-- ZERO (f60 satisfied)"
        if i == 0 and d == 0: tag = " <-- ZERO (b60 also satisfied!)"
        if i == 0 and d != 0: tag = f" <-- b60 gap, HW={hw(d)}"
        print(f"    d{reg_names[i]}59 = 0x{d:08x} (HW={hw(d)}){tag}", flush=True)

    # ===== DEPTH 4 =====
    # e60 and a60 each depend on all of W57-W60
    # e60 = d59 + T1_60, a60 = T1_60 + T2_60
    # T1_60 depends on (h59, e59, f59, g59, K[60], W60)
    print(f"\n{'='*70}", flush=True)
    print("DEPTH 4: e60 and a60 (depends on dW57-dW60)", flush=True)
    print("=" * 70, flush=True)

    def C_e60(s):
        a, b, c, d, e, f, g, h = s
        return (d + h + enc.Sigma1_py(e) + enc.Ch_py(e, f, g) + enc.K[60]) & M32

    def C_a60(s):
        a, b, c, d, e, f, g, h = s
        T1_const = (h + enc.Sigma1_py(e) + enc.Ch_py(e, f, g) + enc.K[60]) & M32
        T2 = (enc.Sigma0_py(a) + enc.Maj_py(a, b, c)) & M32
        return (T1_const + T2) & M32

    Ce60_1 = C_e60(s59_1)
    Ce60_2 = C_e60(s59_2)
    Ca60_1 = C_a60(s59_1)
    Ca60_2 = C_a60(s59_2)

    req_dW60_e = (Ce60_2 - Ce60_1) & M32
    req_dW60_a = (Ca60_2 - Ca60_1) & M32

    gap4 = req_dW60_e ^ req_dW60_a

    print(f"  Required dW60 for e60 collision: 0x{req_dW60_e:08x}", flush=True)
    print(f"  Required dW60 for a60 collision: 0x{req_dW60_a:08x}", flush=True)
    print(f"  XOR gap: 0x{gap4:08x}  (HW = {hw(gap4)})", flush=True)
    print(f"  Additive gap: 0x{(req_dW60_e - req_dW60_a) & M32:08x}", flush=True)

    # ===== FULL COLLISION CHECK =====
    # If all gaps are zero, a full collision at round 60 is achievable.
    # Check what happens if we fix ALL dW for the e-register chain:
    print(f"\n{'='*70}", flush=True)
    print("VERIFICATION: Full round-60 state with all dW fixed for e-chain", flush=True)
    print("=" * 70, flush=True)

    W1_60 = 0x00000000
    W2_60 = (W1_60 - req_dW60_e) & M32

    s60_1 = compute_round_state(s59_1, 60, W1_60)
    s60_2 = compute_round_state(s59_2, 60, W2_60)

    print(f"  Round 60 state diff:", flush=True)
    zero_count = 0
    for i in range(8):
        d = s60_1[i] ^ s60_2[i]
        tag = " <-- ZERO" if d == 0 else ""
        if d == 0: zero_count += 1
        print(f"    d{reg_names[i]}60 = 0x{d:08x} (HW={hw(d)}){tag}", flush=True)
    print(f"  Registers with zero diff: {zero_count}/8", flush=True)

    # ===== SUMMARY =====
    print(f"\n{'='*70}", flush=True)
    print("BOOMERANG VECTOR SUMMARY", flush=True)
    print("=" * 70, flush=True)
    print(f"  Depth 1 (h60 vs d60, dW57):  gap HW = {hw(gap1):2d}  gap = 0x{gap1:08x}", flush=True)
    print(f"  Depth 2 (g60 vs c60, dW58):  gap HW = {hw(gap2):2d}  gap = 0x{gap2:08x}", flush=True)
    print(f"  Depth 3 (f60 vs b60, dW59):  gap HW = {hw(gap3):2d}  gap = 0x{gap3:08x}", flush=True)
    print(f"  Depth 4 (e60 vs a60, dW60):  gap HW = {hw(gap4):2d}  gap = 0x{gap4:08x}", flush=True)
    total_gap_hw = hw(gap1) + hw(gap2) + hw(gap3) + hw(gap4)
    print(f"  Total gap HW:                {total_gap_hw}", flush=True)

    if total_gap_hw == 0:
        print(f"\n  ALL GAPS ZERO! This candidate has no boomerang contradiction.", flush=True)
        print(f"  Full collision at sr=60 may be achievable.", flush=True)
    elif hw(gap1) > 0 and hw(gap2) == 0 and hw(gap3) == 0 and hw(gap4) == 0:
        print(f"\n  Contradiction is concentrated at depth 1 only.", flush=True)
        print(f"  The single dW57 scalar gap is the sole obstruction.", flush=True)
    elif hw(gap1) > 0:
        print(f"\n  Contradiction starts at depth 1 and cascades deeper.", flush=True)
        print(f"  NOTE: depth 2-4 gaps are computed AFTER fixing dW_k for the", flush=True)
        print(f"  e-register chain. If depth 1 gap were zero, depths 2-4 would", flush=True)
        print(f"  be the binding constraints.", flush=True)
    else:
        print(f"\n  Depth 1 gap is zero but deeper gaps exist.", flush=True)
        print(f"  The contradiction is at deeper cascade levels.", flush=True)

    # ===== ALTERNATIVE: Fix dW57 for d60 instead of h60 =====
    print(f"\n{'='*70}", flush=True)
    print("ALTERNATIVE: Fix dW57 for a-chain (d60) instead of e-chain (h60)", flush=True)
    print("=" * 70, flush=True)

    W1_57_alt = 0x00000000
    W2_57_alt = (W1_57_alt - req_dW57_d) & M32

    s57a_1 = compute_round_state(state1, 57, W1_57_alt)
    s57a_2 = compute_round_state(state2, 57, W2_57_alt)

    # Depth 2 from the a-chain perspective
    Ce58a_1 = C_e(s57a_1)
    Ce58a_2 = C_e(s57a_2)
    Ca58a_1 = C_a(s57a_1)
    Ca58a_2 = C_a(s57a_2)

    req_dW58_g_alt = (Ce58a_2 - Ce58a_1) & M32
    req_dW58_c_alt = (Ca58a_2 - Ca58a_1) & M32
    gap2_alt = req_dW58_g_alt ^ req_dW58_c_alt

    # Propagate
    W2_58_alt = (W1_58 - req_dW58_g_alt) & M32
    s58a_1 = compute_round_state(s57a_1, 58, W1_58)
    s58a_2 = compute_round_state(s57a_2, 58, W2_58_alt)

    Ce59a_1 = C_e59(s58a_1)
    Ce59a_2 = C_e59(s58a_2)
    Ca59a_1 = C_a59(s58a_1)
    Ca59a_2 = C_a59(s58a_2)
    req_dW59_f_alt = (Ce59a_2 - Ce59a_1) & M32
    req_dW59_b_alt = (Ca59a_2 - Ca59a_1) & M32
    gap3_alt = req_dW59_f_alt ^ req_dW59_b_alt

    W2_59_alt = (W1_59 - req_dW59_f_alt) & M32
    s59a_1 = compute_round_state(s58a_1, 59, W1_59)
    s59a_2 = compute_round_state(s58a_2, 59, W2_59_alt)

    Ce60a_1 = C_e60(s59a_1)
    Ce60a_2 = C_e60(s59a_2)
    Ca60a_1 = C_a60(s59a_1)
    Ca60a_2 = C_a60(s59a_2)
    req_dW60_e_alt = (Ce60a_2 - Ce60a_1) & M32
    req_dW60_a_alt = (Ca60a_2 - Ca60a_1) & M32
    gap4_alt = req_dW60_e_alt ^ req_dW60_a_alt

    print(f"  Depth 1 (h60 vs d60, dW57):  d60 satisfied, h60 gap HW = {hw(gap1)}", flush=True)
    print(f"  Depth 2 (g60 vs c60, dW58):  gap HW = {hw(gap2_alt):2d}  gap = 0x{gap2_alt:08x}", flush=True)
    print(f"  Depth 3 (f60 vs b60, dW59):  gap HW = {hw(gap3_alt):2d}  gap = 0x{gap3_alt:08x}", flush=True)
    print(f"  Depth 4 (e60 vs a60, dW60):  gap HW = {hw(gap4_alt):2d}  gap = 0x{gap4_alt:08x}", flush=True)

    # ===== SENSITIVITY: Does the choice of concrete W1[57] matter? =====
    print(f"\n{'='*70}", flush=True)
    print("SENSITIVITY: Do gap values depend on concrete W1[57] choice?", flush=True)
    print("=" * 70, flush=True)

    import random
    random.seed(42)
    samples = 20
    gap_vectors = []
    for trial in range(samples):
        w1_57 = random.randint(0, M32)
        w2_57 = (w1_57 - req_dW57_h) & M32
        t57_1 = compute_round_state(state1, 57, w1_57)
        t57_2 = compute_round_state(state2, 57, w2_57)

        # Depth 2
        tCe58_1 = C_e(t57_1); tCe58_2 = C_e(t57_2)
        tCa58_1 = C_a(t57_1); tCa58_2 = C_a(t57_2)
        t_dW58_g = (tCe58_2 - tCe58_1) & M32
        t_dW58_c = (tCa58_2 - tCa58_1) & M32
        tgap2 = t_dW58_g ^ t_dW58_c

        w1_58 = random.randint(0, M32)
        w2_58 = (w1_58 - t_dW58_g) & M32
        t58_1 = compute_round_state(t57_1, 58, w1_58)
        t58_2 = compute_round_state(t57_2, 58, w2_58)

        # Depth 3
        tCe59_1 = C_e59(t58_1); tCe59_2 = C_e59(t58_2)
        tCa59_1 = C_a59(t58_1); tCa59_2 = C_a59(t58_2)
        t_dW59_f = (tCe59_2 - tCe59_1) & M32
        t_dW59_b = (tCa59_2 - tCa59_1) & M32
        tgap3 = t_dW59_f ^ t_dW59_b

        w1_59 = random.randint(0, M32)
        w2_59 = (w1_59 - t_dW59_f) & M32
        t59_1 = compute_round_state(t58_1, 59, w1_59)
        t59_2 = compute_round_state(t58_2, 59, w2_59)

        # Depth 4
        tCe60_1 = C_e60(t59_1); tCe60_2 = C_e60(t59_2)
        tCa60_1 = C_a60(t59_1); tCa60_2 = C_a60(t59_2)
        t_dW60_e = (tCe60_2 - tCe60_1) & M32
        t_dW60_a = (tCa60_2 - tCa60_1) & M32
        tgap4 = t_dW60_e ^ t_dW60_a

        gap_vectors.append((tgap2, tgap3, tgap4))

    # Check if gap values are constant across random W choices
    unique2 = len(set(g[0] for g in gap_vectors))
    unique3 = len(set(g[1] for g in gap_vectors))
    unique4 = len(set(g[2] for g in gap_vectors))

    print(f"  Across {samples} random (W1[57], W1[58], W1[59]) samples:", flush=True)
    print(f"  Unique depth-2 gaps: {unique2} {'(CONSTANT!)' if unique2 == 1 else '(varies)'}", flush=True)
    print(f"  Unique depth-3 gaps: {unique3} {'(CONSTANT!)' if unique3 == 1 else '(varies)'}", flush=True)
    print(f"  Unique depth-4 gaps: {unique4} {'(CONSTANT!)' if unique4 == 1 else '(varies)'}", flush=True)

    if unique2 > 1:
        hws2 = [hw(g[0]) for g in gap_vectors]
        print(f"    Depth-2 gap HW range: [{min(hws2)}, {max(hws2)}], mean={sum(hws2)/len(hws2):.1f}", flush=True)
    if unique3 > 1:
        hws3 = [hw(g[1]) for g in gap_vectors]
        print(f"    Depth-3 gap HW range: [{min(hws3)}, {max(hws3)}], mean={sum(hws3)/len(hws3):.1f}", flush=True)
    if unique4 > 1:
        hws4 = [hw(g[2]) for g in gap_vectors]
        print(f"    Depth-4 gap HW range: [{min(hws4)}, {max(hws4)}], mean={sum(hws4)/len(hws4):.1f}", flush=True)

    # Show a few samples
    print(f"\n  First 5 samples:", flush=True)
    for i, (g2, g3, g4) in enumerate(gap_vectors[:5]):
        print(f"    Trial {i}: gap2=0x{g2:08x}(HW={hw(g2)}) "
              f"gap3=0x{g3:08x}(HW={hw(g3)}) "
              f"gap4=0x{g4:08x}(HW={hw(g4)})", flush=True)

    print(f"\nDone.", flush=True)


if __name__ == "__main__":
    main()
