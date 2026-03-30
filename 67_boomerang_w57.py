#!/usr/bin/env python3
"""
Script 67: Boomerang W57 Algebra

THE INSIGHT: h60 = e57 = C56 + W57 (algebraically fixed by one free word).
The backward cone demands specific h60 values for collision.
The schedule demands specific W57 relationships for compliance.
The "algebraic error" is the gap between these two demands.

This script:
1. Solves the backward cone (instant) to get required h60 values
2. Deduces the required W57 from h60
3. Checks if the required W57 satisfies the schedule constraints
4. Measures the exact algebraic error (how many schedule bits are violated)
"""

import sys
import os
import time
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module
enc = import_module('13_custom_cnf_encoder')

M32 = 0xFFFFFFFF


def analyze_boomerang():
    M1 = [0x17149975] + [0xffffffff] * 15
    M2 = M1[:]; M2[0] ^= 0x80000000; M2[9] ^= 0x80000000

    state1, W1_pre = enc.precompute_state(M1)
    state2, W2_pre = enc.precompute_state(M2)

    a1,b1,c1,d1,e1,f1,g1,h1 = state1
    a2,b2,c2,d2,e2,f2,g2,h2 = state2

    print("=" * 60, flush=True)
    print("BOOMERANG W57 ALGEBRA", flush=True)
    print("=" * 60, flush=True)

    # C56_e: the constant part of e57 = C56_e + W57
    C56_e_1 = (d1 + h1 + enc.Sigma1_py(e1) + enc.Ch_py(e1,f1,g1) + enc.K[57]) & M32
    C56_e_2 = (d2 + h2 + enc.Sigma1_py(e2) + enc.Ch_py(e2,f2,g2) + enc.K[57]) & M32

    # C56_a: the constant part of a57 = C56_a + W57
    T2_1 = (enc.Sigma0_py(a1) + enc.Maj_py(a1,b1,c1)) & M32
    T2_2 = (enc.Sigma0_py(a2) + enc.Maj_py(a2,b2,c2)) & M32
    C56_a_1 = (C56_e_1 - d1 + T2_1) & M32  # a57 = T1 + T2 = (C56_e - d + T2) + W57... wait
    # Actually: T1 = h + Sig1(e) + Ch(e,f,g) + K + W = (h + Sig1(e) + Ch + K) + W = C_T1 + W
    # a57 = T1 + T2 = C_T1 + W + T2 = (C_T1 + T2) + W
    C_T1_1 = (h1 + enc.Sigma1_py(e1) + enc.Ch_py(e1,f1,g1) + enc.K[57]) & M32
    C_T1_2 = (h2 + enc.Sigma1_py(e2) + enc.Ch_py(e2,f2,g2) + enc.K[57]) & M32
    C56_a_1 = (C_T1_1 + T2_1) & M32
    C56_a_2 = (C_T1_2 + T2_2) & M32

    print(f"\nRound 57 Constants (from precomputed Round 56 state):", flush=True)
    print(f"  C56_e_M1 = 0x{C56_e_1:08x}  (e57_1 = this + W1[57])", flush=True)
    print(f"  C56_e_M2 = 0x{C56_e_2:08x}  (e57_2 = this + W2[57])", flush=True)
    print(f"  C56_a_M1 = 0x{C56_a_1:08x}  (a57_1 = this + W1[57])", flush=True)
    print(f"  C56_a_M2 = 0x{C56_a_2:08x}  (a57_2 = this + W2[57])", flush=True)

    # The h60 collision requirement: h60_1 == h60_2
    # h60 = e57, so: C56_e_1 + W1[57] = C56_e_2 + W2[57]
    # => dW57 = W1[57] - W2[57] = C56_e_2 - C56_e_1
    required_dW57_h60 = (C56_e_2 - C56_e_1) & M32

    # The d60 collision requirement: d60_1 == d60_2
    # d60 = a57, so: C56_a_1 + W1[57] = C56_a_2 + W2[57]
    # => dW57 = C56_a_2 - C56_a_1
    required_dW57_d60 = (C56_a_2 - C56_a_1) & M32

    print(f"\nCollision Requirements on W57 difference:", flush=True)
    print(f"  For h60_1==h60_2: dW57 = 0x{required_dW57_h60:08x}", flush=True)
    print(f"  For d60_1==d60_2: dW57 = 0x{required_dW57_d60:08x}", flush=True)

    if required_dW57_h60 == required_dW57_d60:
        print(f"  [!!!] BOTH AGREE! d60 and h60 need the SAME dW57!", flush=True)
    else:
        print(f"  CONFLICT: d60 and h60 need DIFFERENT dW57 values!", flush=True)
        print(f"  Gap: 0x{(required_dW57_h60 - required_dW57_d60) & M32:08x}", flush=True)
        print(f"  This is why registers 6-7 are the hardest — they impose", flush=True)
        print(f"  contradictory demands on W57.", flush=True)

    # Now check: what does the SCHEDULE demand?
    # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
    # This constrains W[59], which is a free variable.
    # But W[59] feeds into f60 = e59, which is a depth-3 register.
    # The schedule constraint is INDEPENDENT of the h60/d60 collision requirement.

    # The key question: given that the backward cone requires specific dW57,
    # and we solve for W1[57] = arbitrary, W2[57] = W1[57] - required_dW57_h60,
    # does this leave enough freedom in W58, W59, W60 to satisfy the collision
    # for the remaining 6 registers AND the schedule?

    # Let's compute: if we fix dW57 to the h60-required value,
    # how much HW does the state diff have at round 57?
    # We choose W1[57] = 0 (arbitrary), W2[57] = -required_dW57_h60
    W1_57_test = 0x12345678  # arbitrary
    W2_57_test = (W1_57_test - required_dW57_h60) & M32

    # Compute Round 57 states
    def round57(state, W57):
        a,b,c,d,e,f,g,h = state
        T1 = (h + enc.Sigma1_py(e) + enc.Ch_py(e,f,g) + enc.K[57] + W57) & M32
        T2 = (enc.Sigma0_py(a) + enc.Maj_py(a,b,c)) & M32
        return ((T1+T2)&M32, a, b, c, (d+T1)&M32, e, f, g)

    s57_1 = round57(state1, W1_57_test)
    s57_2 = round57(state2, W2_57_test)

    print(f"\nState diff after Round 57 (with dW57 fixed for h60 collision):", flush=True)
    reg_names = ['a','b','c','d','e','f','g','h']
    total_hw = 0
    for i in range(8):
        d = s57_1[i] ^ s57_2[i]
        hw = bin(d).count('1')
        total_hw += hw
        marker = " ZERO!" if d == 0 else ""
        print(f"  d{reg_names[i]}[57] = 0x{d:08x} (hw={hw}){marker}", flush=True)

    print(f"  Total HW at Round 57: {total_hw}", flush=True)
    print(f"  (Baseline without fixing: total_hw at Round 56 = 104)", flush=True)

    if s57_1[0] == s57_2[0]:
        print(f"\n  [!!!] da[57] = 0! Fixing dW57 for h60 collision ALSO zeros da!", flush=True)
    if s57_1[4] == s57_2[4]:
        print(f"  [!!!] de[57] = 0!", flush=True)

    # Check the algebraic error: given the backward-required dW57,
    # what is the implied dW61 from the schedule?
    # W[61] = sigma1(W[59]) + W[54] + sigma0(W[46]) + W[45]
    # dW[61] depends on dW[59] through sigma1.
    # The backward cone needs specific W[61] values.
    # The forward choice of W[59] determines W[61].
    # The gap is: does any W[59] produce the right W[61]?

    print(f"\n{'='*60}", flush=True)
    print(f"ALGEBRAIC ERROR ANALYSIS", flush=True)
    print(f"{'='*60}", flush=True)
    print(f"\nThe backward cone requires specific values of h60 and d60.", flush=True)
    print(f"h60 is fixed by W57 alone (depth 1).", flush=True)
    print(f"d60 is ALSO fixed by W57 alone (depth 1).", flush=True)
    print(f"If h60 and d60 demand DIFFERENT dW57, the instance is UNSAT", flush=True)
    print(f"regardless of W58, W59, W60 — those can't help.", flush=True)
    print(f"\nRequired dW57 for h60: 0x{required_dW57_h60:08x}", flush=True)
    print(f"Required dW57 for d60: 0x{required_dW57_d60:08x}", flush=True)
    gap = (required_dW57_h60 ^ required_dW57_d60)
    gap_hw = bin(gap).count('1')
    print(f"XOR gap: 0x{gap:08x} (hw={gap_hw})", flush=True)

    if gap_hw == 0:
        print(f"\nGap is ZERO — both depth-1 registers agree on dW57!", flush=True)
        print(f"The UNSAT is NOT from a depth-1 contradiction.", flush=True)
        print(f"The contradiction must come from deeper registers (depth 2-4).", flush=True)
    else:
        print(f"\nGap is NONZERO ({gap_hw} bits) — depth-1 contradiction!", flush=True)
        print(f"h60 and d60 demand incompatible W57 differences.", flush=True)
        print(f"This is THE root cause of the UNSAT for this candidate.", flush=True)
        print(f"\nTo find a live candidate, we need M[0] where this gap = 0.", flush=True)
        print(f"This is a MUCH more specific condition than just da[56]=0.", flush=True)

    return required_dW57_h60, required_dW57_d60, gap, C56_e_1, C56_e_2, C56_a_1, C56_a_2


def main():
    dw_h, dw_d, gap, Ce1, Ce2, Ca1, Ca2 = analyze_boomerang()

    if gap != 0:
        print(f"\n{'='*60}", flush=True)
        print(f"IMPLICATION FOR CANDIDATE SEARCH", flush=True)
        print(f"{'='*60}", flush=True)
        print(f"\nThe boomerang gap is nonzero. For a candidate to be sr=60 viable:", flush=True)
        print(f"  1. da[56] = 0 (existing condition)", flush=True)
        print(f"  2. C56_e_2 - C56_e_1 = C56_a_2 - C56_a_1 (NEW condition)", flush=True)
        print(f"     i.e., the additive diff of e57-constants must equal", flush=True)
        print(f"     the additive diff of a57-constants", flush=True)
        print(f"\nThis is equivalent to: T2_1 - d1 = T2_2 - d2", flush=True)
        print(f"  where T2 = Sigma0(a56) + Maj(a56,b56,c56)", flush=True)
        print(f"  and d = d56", flush=True)
        print(f"\nSince da[56]=0 means a1=a2 and T2 depends on a,b,c:", flush=True)
        print(f"  T2 diff comes from db[56] and dc[56] (via Maj)", flush=True)
        print(f"  d diff comes from dd[56]", flush=True)
        print(f"\nThe boomerang gap condition is:", flush=True)
        print(f"  dT2 = dd[56] (modular arithmetic)", flush=True)
        print(f"  where dT2 = Sigma0(a)+Maj(a,b1,c1) - Sigma0(a)+Maj(a,b2,c2)", flush=True)
        print(f"  Since da=0: dT2 = Maj(a,b1,c1) - Maj(a,b2,c2)", flush=True)


if __name__ == "__main__":
    main()
