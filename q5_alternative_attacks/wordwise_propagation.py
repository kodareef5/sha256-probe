#!/usr/bin/env python3
"""
wordwise_propagation.py — Modular-difference propagation for SHA-256 tail

From the Programmatic SAT paper (Alamgir et al.):
  If we know the SIGNED differences of two addends and one has known
  concrete values, we can compute the MODULAR difference of the sum.

  δA + δB = δC (mod 2^32)

  where δX = X_msg1 - X_msg2 (mod 2^32)

  Signed diff → modular diff conversion:
    '=' at bit i → contributes 0
    'u' at bit i → contributes +2^i
    'n' at bit i → contributes -2^i (= 2^32 - 2^i)
    'x' at bit i → contributes ±2^i (two possibilities)

For the sr=60 problem, the state56 values are fully known, so every
state register has exact signed differences. This means we can compute
exact modular differences for all state registers at round 56.

Then: the modular difference of the sum T1 = h + Σ1(e) + Ch(e,f,g) + K + W
is the sum of the modular differences of each term.

If dW (the free word difference) is the only unknown, we get:
  δT1 = δh + δΣ1(e) + δCh + 0 + δW

This is a SINGLE EQUATION in one unknown (δW). If we want e.g. δT1 = C
for some target value C, then δW = C - δh - δΣ1(e) - δCh.

This is the "boomerang gap" analysis done algebraically!
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def modular_diff(v1, v2):
    """Compute modular difference v1 - v2 (mod 2^32)."""
    return (v1 - v2) & MASK


def analyze_modular_diffs(m0=0x17149975, fill=0xffffffff):
    """Compute modular differences at round 56 and trace through rounds."""
    M1 = [m0] + [fill]*15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000

    s1, W1 = precompute_state(M1)
    s2, W2 = precompute_state(M2)

    assert s1[0] == s2[0], "da[56] != 0"

    regs = ['a','b','c','d','e','f','g','h']

    print(f"Modular Differences at Round 56")
    print(f"M[0]=0x{m0:08x}, fill=0x{fill:08x}")
    print(f"{'='*70}")

    for i in range(8):
        d = modular_diff(s1[i], s2[i])
        print(f"  δ{regs[i]}[56] = 0x{d:08x} (= {d} mod 2^32, hw={hw(d)})")

    # Now compute what the modular differences REQUIRE of W[57]
    print(f"\nRound 57 Modular Difference Equations")
    print(f"{'='*70}")

    # T1 components
    d_h56 = modular_diff(s1[7], s2[7])
    d_Sig1_e56 = modular_diff(Sigma1(s1[4]), Sigma1(s2[4]))
    d_Ch_56 = modular_diff(Ch(s1[4], s1[5], s1[6]), Ch(s2[4], s2[5], s2[6]))
    d_K57 = 0  # same constant for both messages

    print(f"  T1 = h56 + Σ1(e56) + Ch(e56,f56,g56) + K[57] + W[57]")
    print(f"  δT1 = δh56 + δΣ1(e56) + δCh56 + 0 + δW[57]")
    print(f"  δh56      = 0x{d_h56:08x}")
    print(f"  δΣ1(e56)  = 0x{d_Sig1_e56:08x}")
    print(f"  δCh56     = 0x{d_Ch_56:08x}")
    print(f"  Constant part: C_T1 = 0x{add(d_h56, d_Sig1_e56, d_Ch_56):08x}")

    # T2 components
    d_Sig0_a56 = modular_diff(Sigma0(s1[0]), Sigma0(s2[0]))
    d_Maj_56 = modular_diff(Maj(s1[0], s1[1], s1[2]), Maj(s2[0], s2[1], s2[2]))

    print(f"\n  T2 = Σ0(a56) + Maj(a56,b56,c56)")
    print(f"  δT2 = δΣ0(a56) + δMaj56")
    print(f"  δΣ0(a56)  = 0x{d_Sig0_a56:08x} (should be 0 since da56=0)")
    print(f"  δMaj56    = 0x{d_Maj_56:08x}")
    print(f"  δT2       = 0x{add(d_Sig0_a56, d_Maj_56):08x}")

    # New state requirements
    print(f"\nWhat δW[57] must satisfy for each round-57 register to be zero:")
    print(f"  For δe57 = 0: δd56 + δT1 = 0")
    print(f"    → δW[57] = -(δd56 + C_T1) = 0x{(-(s1[3]-s2[3]) - add(d_h56, d_Sig1_e56, d_Ch_56)) & MASK:08x}")
    need_for_e57 = (-(s1[3]-s2[3]) - d_h56 - d_Sig1_e56 - d_Ch_56) & MASK

    print(f"  For δa57 = 0: δT1 + δT2 = 0")
    d_T2 = add(d_Sig0_a56, d_Maj_56)
    need_for_a57 = (-d_T2 - d_h56 - d_Sig1_e56 - d_Ch_56) & MASK
    print(f"    → δW[57] = -(C_T1 + δT2) = 0x{need_for_a57:08x}")

    gap = (need_for_e57 - need_for_a57) & MASK
    print(f"\n  BOOMERANG GAP = δW57_for_e57 - δW57_for_a57 = 0x{gap:08x} (hw={hw(gap)})")
    print(f"  This is the exact algebraic conflict at depth 1.")
    print(f"  The SAT solver must find W[57] values where the carries")
    print(f"  in the modular additions absorb this gap.")

    # Full round-by-round analysis with symbolic dW
    print(f"\nRound-by-Round Modular Difference Propagation")
    print(f"(assuming δW[57..60] are free, tracking through 7 rounds)")
    print(f"{'='*70}")

    # Round 57: most diffs are determined
    print(f"  After round 57:")
    print(f"    δb57 = δa56 = 0  ** ZERO **")
    print(f"    δc57 = δb56 = 0x{modular_diff(s1[1], s2[1]):08x} (hw={hw(modular_diff(s1[1], s2[1]))})")
    print(f"    δd57 = δc56 = 0x{modular_diff(s1[2], s2[2]):08x}")
    print(f"    δf57 = δe56 = 0x{modular_diff(s1[4], s2[4]):08x}")
    print(f"    δg57 = δf56 = 0x{modular_diff(s1[5], s2[5]):08x}")
    print(f"    δh57 = δg56 = 0x{modular_diff(s1[6], s2[6]):08x}")
    print(f"    δa57, δe57 = functions of δW[57]")

    print(f"\n  After round 58:")
    print(f"    δb58 = δa57 (depends on δW[57])")
    print(f"    δc58 = δb57 = 0  ** ZERO propagated from round 57 **")
    print(f"    δd58 = δc57 = 0x{modular_diff(s1[1], s2[1]):08x}")
    print(f"    δf58 = δe57 (depends on δW[57])")
    print(f"    δg58 = δf57 = 0x{modular_diff(s1[4], s2[4]):08x}")
    print(f"    δh58 = δg57 = 0x{modular_diff(s1[5], s2[5]):08x}")
    print(f"    δa58, δe58 = functions of δW[57], δW[58]")

    print(f"\n  After round 59:")
    print(f"    δc59 = δb58 (depends on δW[57])")
    print(f"    δd59 = δc58 = 0  ** ZERO propagated 2 rounds **")
    print(f"    δg59 = δf58 (depends on δW[57])")
    print(f"    δh59 = δg58 = 0x{modular_diff(s1[4], s2[4]):08x}")

    print(f"\n  After round 60:")
    print(f"    δd60 = δc59 (depends on δW[57])")
    print(f"    δh60 = δg59 (depends on δW[57])")
    print(f"    ** These are the MITM hard residue registers **")
    print(f"    ** Both ultimately determined by just δW[57] **")

    print(f"\n  KEY STRUCTURAL INSIGHT:")
    print(f"  The 'zero wave' from δb57=0 propagates as:")
    print(f"    b57=0 → c58=0 → d59=0 → [absorbed into e60 via d+T1]")
    print(f"  This is the 'register zeroing' pattern that makes sr=59 easy.")
    print(f"  For sr=60, the zero wave needs to reach one more round,")
    print(f"  but it gets absorbed into the e-register update at round 60")
    print(f"  where it meets the schedule-determined W[61].")

    return s1, s2, W1, W2


if __name__ == "__main__":
    analyze_modular_diffs()
    print(f"\n{'='*70}")
    print(f"This analysis shows the sr=60 problem has tight algebraic")
    print(f"structure that the signed-diff / modular-diff model captures.")
    print(f"The boomerang gap is the exact quantification of the obstacle.")
    print(f"A decomposed search should first find if ANY gap-absorbing")
    print(f"carry pattern exists, then search for concrete values.")
