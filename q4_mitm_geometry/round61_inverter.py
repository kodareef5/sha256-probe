#!/usr/bin/env python3
"""
round61_inverter.py — Find W1[60] satisfying the round-61 cascade constraint.

At round 60, after the cascade chain has held: a60=b60=c60=d60=e60 same
between messages. So dT2_61 = 0 (Sigma0 and Maj agree). Therefore:

  cascade_dw(state60) = dh60 + dCh(e60, f60, g60)

where:
- dh60 = dg59 (constant from cascade chain prefix)
- e60 = d59 + h59 + Sigma1(e59) + Ch(e59,f59,g59) + K[60] + W1[60]
       = constant + W1[60]
- f60 = e59 (constant from cascade chain prefix)
- g60 = f59 (constant from cascade chain prefix)

So cascade_dw is a function of e60 (and hence W1[60]) only.

The constraint to invert:
  dCh(e60, f60_M1, g60_M1, f60_M2, g60_M2) = target - dh60

where dCh is integer difference of Ch values:
  Ch(e60, f60_M1, g60_M1) - Ch(e60, f60_M2, g60_M2) (mod 2^32)

This script enumerates W1[60] and finds matches. At small N this is
feasible to verify. At N=32, brute force is 2^32 per prefix.
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import K, MASK, sigma0, sigma1, Sigma0, Sigma1, Ch, Maj, hw, add, IV, precompute_state


def one_round(s, w, i):
    T1 = add(s[7], Sigma1(s[4]), Ch(s[4], s[5], s[6]), K[i], w)
    T2 = add(Sigma0(s[0]), Maj(s[0], s[1], s[2]))
    return (add(T1, T2), s[0], s[1], s[2], add(s[3], T1), s[4], s[5], s[6])


def cascade_dw(s1, s2):
    dh = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    T2_1 = (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & MASK
    T2_2 = (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & MASK
    dT2 = (T2_1 - T2_2) & MASK
    return (dh + dSig1 + dCh + dT2) & MASK


def setup_cert_prefix():
    """Compute state after rounds 57, 58, 59 using cert W values."""
    M0 = 0x17149975
    FILL = 0xFFFFFFFF
    M1 = [M0] + [FILL] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1, W1_pre = precompute_state(M1)
    s2, W2_pre = precompute_state(M2)

    C57 = cascade_dw(s1, s2)

    w1_57 = 0x9ccfa55e; w2_57 = (w1_57 + C57) & MASK
    s1a = one_round(s1, w1_57, 57); s2a = one_round(s2, w2_57, 57)
    C58 = cascade_dw(s1a, s2a)

    w1_58 = 0xd9d64416; w2_58 = (w1_58 + C58) & MASK
    s1b = one_round(s1a, w1_58, 58); s2b = one_round(s2a, w2_58, 58)
    C59 = cascade_dw(s1b, s2b)

    w1_59 = 0x9e3ffb08; w2_59 = (w1_59 + C59) & MASK
    s1c = one_round(s1b, w1_59, 59); s2c = one_round(s2b, w2_59, 59)
    C60 = cascade_dw(s1c, s2c)

    return s1c, s2c, C60, W1_pre, W2_pre


def find_valid_w1_60(s1c, s2c, C60, target_C61, max_search=1<<22):
    """Brute-force search for W1[60] such that cascade_dw at round 60 matches target.

    Returns list of matching W1[60] values."""
    matches = []

    for w1_60 in range(max_search):
        w2_60 = (w1_60 + C60) & MASK
        s1d = one_round(s1c, w1_60, 60)
        s2d = one_round(s2c, w2_60, 60)
        rc61 = cascade_dw(s1d, s2d)
        if rc61 == target_C61:
            matches.append(w1_60)
            if len(matches) >= 5:
                break
    return matches


def main():
    print("Round-61 cascade closure inverter")
    print("=" * 60)
    print()

    s1c, s2c, C60, W1_pre, W2_pre = setup_cert_prefix()

    # Cert W1[59] determines the schedule W[61]
    w1_59 = 0x9e3ffb08
    w2_59 = (w1_59 + ((s1c[7] - s2c[7] + Sigma1(s1c[4]) - Sigma1(s2c[4]) + Ch(s1c[4],s1c[5],s1c[6]) - Ch(s2c[4],s2c[5],s2c[6])) & MASK) - 1) & MASK
    # Actually we computed this in setup, but it's not exposed. Let me recompute.
    # No wait, cert W2[59] is 0x587ffaa6
    w2_59 = 0x587ffaa6

    sched_const1_61 = (W1_pre[54] + sigma0(W1_pre[46]) + W1_pre[45]) & MASK
    sched_const2_61 = (W2_pre[54] + sigma0(W2_pre[46]) + W2_pre[45]) & MASK
    sched_dW61 = (sigma1(w2_59) - sigma1(w1_59) + sched_const2_61 - sched_const1_61) & MASK
    print(f"Schedule dW[61] (target): 0x{sched_dW61:08x}")
    print()

    # Now brute-force search W1[60] for matches
    print(f"Searching W1[60] in [0, 2^22) for match...")
    t0 = time.time()
    matches = find_valid_w1_60(s1c, s2c, C60, sched_dW61, max_search=1<<22)
    elapsed = time.time() - t0

    print(f"Found {len(matches)} matches in {elapsed:.1f}s")
    print(f"Matches: {[f'0x{m:08x}' for m in matches[:5]]}")
    print()
    print(f"Cert W1[60] = 0xb6befe82 (in range? {0xb6befe82 < (1<<22)})")
    print()
    print(f"Density estimate: {len(matches) * (2**32) / (1<<22):.1f} matches in 2^32")


if __name__ == "__main__":
    main()
