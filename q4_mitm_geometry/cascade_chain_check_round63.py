#!/usr/bin/env python3
"""
Check whether the 4-level cascade chain already satisfies cascade 2 (de63=0 etc).

The cascade chain forces da=db=dc=dd=0 at round 59. The natural question:
does it ALSO ensure de=df=dg=dh=0 at round 63?

If YES: every 4-level cascade chain tuple is a collision. Search trivial.
If NO: we still need to find (W1[57..60]) such that cascade 2 also closes.
       But the search space is at least 2^128 instead of 2^256.
"""

import sys, os, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import K, MASK, sigma0, sigma1, Sigma0, Sigma1, Ch, Maj, hw, add, IV, precompute_state, build_schedule_tail, run_tail_rounds


def cascade_dw(s1, s2):
    dh = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    T2_1 = (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & MASK
    T2_2 = (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & MASK
    dT2 = (T2_1 - T2_2) & MASK
    return (dh + dSig1 + dCh + dT2) & MASK


def one_round(s, w, i):
    T1 = add(s[7], Sigma1(s[4]), Ch(s[4], s[5], s[6]), K[i], w)
    T2 = add(Sigma0(s[0]), Maj(s[0], s[1], s[2]))
    return (add(T1, T2), s[0], s[1], s[2], add(s[3], T1), s[4], s[5], s[6])


def main():
    m0 = 0x17149975
    fill = 0xFFFFFFFF

    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1, W1_pre = precompute_state(M1)
    s2, W2_pre = precompute_state(M2)

    C57 = cascade_dw(s1, s2)

    n = 10000
    rng = random.Random(42)
    cascade1_ok = 0
    cascade2_ok = 0  # de=df=dg=dh=0 at round 63
    full_collision = 0
    min_total_hw = 256
    best_state = None
    hw_distribution = []

    for trial in range(n):
        w1_57 = rng.getrandbits(32); w2_57 = (w1_57 + C57) & MASK
        s1a = one_round(s1, w1_57, 57); s2a = one_round(s2, w2_57, 57)
        C58 = cascade_dw(s1a, s2a)

        w1_58 = rng.getrandbits(32); w2_58 = (w1_58 + C58) & MASK
        s1b = one_round(s1a, w1_58, 58); s2b = one_round(s2a, w2_58, 58)
        C59 = cascade_dw(s1b, s2b)

        w1_59 = rng.getrandbits(32); w2_59 = (w1_59 + C59) & MASK
        s1c = one_round(s1b, w1_59, 59); s2c = one_round(s2b, w2_59, 59)
        C60 = cascade_dw(s1c, s2c)

        w1_60 = rng.getrandbits(32); w2_60 = (w1_60 + C60) & MASK

        # Run all 64 rounds
        W1_tail = build_schedule_tail(W1_pre, [w1_57, w1_58, w1_59, w1_60])
        W2_tail = build_schedule_tail(W2_pre, [w2_57, w2_58, w2_59, w2_60])
        t1 = run_tail_rounds(s1, W1_tail)
        t2 = run_tail_rounds(s2, W2_tail)
        f1, f2 = t1[-1], t2[-1]

        cascade1_round59 = all(s1c[r] == s2c[r] for r in range(4))
        if cascade1_round59:
            cascade1_ok += 1

        # Check round 63
        d63 = [f1[r] ^ f2[r] for r in range(8)]
        cascade2_at_63 = all(d63[r] == 0 for r in range(4, 8))  # e,f,g,h
        if cascade2_at_63:
            cascade2_ok += 1
        if all(d == 0 for d in d63):
            full_collision += 1

        total_hw = sum(hw(d) for d in d63)
        hw_distribution.append(total_hw)
        if total_hw < min_total_hw:
            min_total_hw = total_hw
            best_state = (w1_57, w1_58, w1_59, w1_60)

    import statistics
    print(f"=== 4-level cascade chain results ({n} samples) ===")
    print(f"Cascade 1 (da=db=dc=dd=0 at round 59): {cascade1_ok}/{n} ({100*cascade1_ok/n:.1f}%)")
    print(f"Cascade 2 (de=df=dg=dh=0 at round 63): {cascade2_ok}/{n} ({100*cascade2_ok/n:.1f}%)")
    print(f"Full collision: {full_collision}/{n}")
    print()
    print(f"Total output HW: mean={statistics.mean(hw_distribution):.1f}, min={min(hw_distribution)}, max={max(hw_distribution)}")
    print(f"Best (W1[57..60]): {[f'0x{w:08x}' for w in best_state]}")


if __name__ == "__main__":
    main()
