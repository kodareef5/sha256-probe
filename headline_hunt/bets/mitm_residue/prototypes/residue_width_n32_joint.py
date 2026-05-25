#!/usr/bin/env python3
"""Joint N=32 free-word residue measurement on the sr=60 cert (the proper version).

Matches the reduced-N free_word_mitm_reducedn model at full width: free words
W1[57],W1[58],W1[59],W1[60]; message-2 words chosen by the cascade so da=0 at
rounds 57,58,59 (w2_for_zero_a) and de60=0 (cascade-2). Then run rounds 57..63 and
measure the round-63 residual difference over a random sample:
  - min total round-63 HW (best near-collision found),
  - abcd63 active-bit width (residue degrees of freedom that vary),
  - residual HW histogram.

This is the N=32 analog of the reduced-N tail measurement and tests how close the
oracle-repaired joint free-word object gets to a full collision at full width.
Reuses lib.sha256 (no SHA reimplementation). Single-process; run several with
different --seed in parallel and OR the active masks / take the min HW.

Usage: residue_width_n32_joint.py [n_samples] [seed]
"""
import os
import sys
import time
import random

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, REPO)
from lib.sha256 import (  # noqa: E402
    MASK, K, Sigma0, Sigma1, Ch, Maj, hw, add,
    precompute_state, build_schedule_tail, run_tail_rounds,
)

M0 = 0x17149975
FILL = 0xFFFFFFFF
REG = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']


def one_round(s, w, r):
    a, b, c, d, e, f, g, h = s
    T1 = add(h, Sigma1(e), Ch(e, f, g), K[r], w)
    T2 = add(Sigma0(a), Maj(a, b, c))
    return (add(T1, T2), a, b, c, add(d, T1), e, f, g)


def w2_for_zero_a(s1, s2, r, w1):
    """Choose w2 so the a-register difference after round r is zero."""
    base1 = add(s1[7], Sigma1(s1[4]), Ch(s1[4], s1[5], s1[6]))
    base2 = add(s2[7], Sigma1(s2[4]), Ch(s2[4], s2[5], s2[6]))
    T21 = add(Sigma0(s1[0]), Maj(s1[0], s1[1], s1[2]))
    T22 = add(Sigma0(s2[0]), Maj(s2[0], s2[1], s2[2]))
    return (w1 + base1 - base2 + T21 - T22) & MASK


def cascade2_offset(s1_59, s2_59):
    dh = (s1_59[7] - s2_59[7]) & MASK
    dSig1 = (Sigma1(s1_59[4]) - Sigma1(s2_59[4])) & MASK
    dCh = (Ch(s1_59[4], s1_59[5], s1_59[6]) - Ch(s2_59[4], s2_59[5], s2_59[6])) & MASK
    return (dh + dSig1 + dCh) & MASK


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else (1 << 18)
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42

    M1 = [M0] + [FILL] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1_init, W1_pre = precompute_state(M1)
    s2_init, W2_pre = precompute_state(M2)

    rng = random.Random(seed)
    active = [0] * 8
    gh_g60 = 0   # g60 diff active bits (= e58 diff)
    gh_h60 = 0   # h60 diff active bits (= e57 diff)
    hist = {}
    min_total = 256
    min_abcd = 128
    best = None
    da_breaks = 0
    t0 = time.time()

    for trial in range(n):
        w1_57 = rng.getrandbits(32)
        w1_58 = rng.getrandbits(32)
        w1_59 = rng.getrandbits(32)
        w1_60 = rng.getrandbits(32)

        # cascade chain: zero da at 57,58,59
        s1, s2 = s1_init, s2_init
        w2_57 = w2_for_zero_a(s1, s2, 57, w1_57)
        s1, s2 = one_round(s1, w1_57, 57), one_round(s2, w2_57, 57)
        gh_h60 |= (s1[4] ^ s2[4]) & MASK        # h60 = e57
        w2_58 = w2_for_zero_a(s1, s2, 58, w1_58)
        s1, s2 = one_round(s1, w1_58, 58), one_round(s2, w2_58, 58)
        gh_g60 |= (s1[4] ^ s2[4]) & MASK        # g60 = e58
        w2_59 = w2_for_zero_a(s1, s2, 59, w1_59)
        s1_59 = one_round(s1, w1_59, 59)
        s2_59 = one_round(s2, w2_59, 59)
        if (s1_59[0] ^ s2_59[0]) != 0:
            da_breaks += 1  # da59 should be 0

        # cascade-2: zero de60
        w2_60 = (w1_60 + cascade2_offset(s1_59, s2_59)) & MASK

        sched1 = build_schedule_tail(W1_pre, [w1_57, w1_58, w1_59, w1_60])
        sched2 = build_schedule_tail(W2_pre, [w2_57, w2_58, w2_59, w2_60])
        r63_1 = run_tail_rounds(s1_init, sched1)[7]
        r63_2 = run_tail_rounds(s2_init, sched2)[7]
        diff = [(r63_1[i] ^ r63_2[i]) & MASK for i in range(8)]

        for i in range(8):
            active[i] |= diff[i]
        total = sum(hw(d) for d in diff)
        abcd = sum(hw(diff[i]) for i in range(4))
        hist[total] = hist.get(total, 0) + 1
        if total < min_total:
            min_total = total
            best = (w1_57, w1_58, w1_59, w1_60, [hex(d) for d in diff])
        min_abcd = min(min_abcd, abcd)

    dt = time.time() - t0
    abcd_active = sum(hw(active[i]) for i in range(4))
    efgh_active = sum(hw(active[i]) for i in range(4, 8))
    print(f"N=32 JOINT residue  samples={n} seed={seed}  ({n/dt:.0f}/s)  da59_breaks={da_breaks}")
    print("round-63 active-bit mask per register:")
    for i in range(8):
        print(f"  d{REG[i]}63 active=0x{active[i]:08x} hw={hw(active[i])}")
    print(f"abcd63 active bits={abcd_active}  efgh63 active bits={efgh_active}  total active={abcd_active+efgh_active}/256")
    print(f"gh60 RESIDUE active bits: g60(=e58)=0x{gh_g60:08x} hw={hw(gh_g60)}  "
          f"h60(=e57)=0x{gh_h60:08x} hw={hw(gh_h60)}  TOTAL gh60 active = {hw(gh_g60)+hw(gh_h60)}/64")
    print(f"min round-63 total HW = {min_total}  (min abcd63 HW = {min_abcd})")
    print("round-63 total-HW histogram (low end):", dict(sorted(hist.items())[:14]))
    print("best:", best)


if __name__ == "__main__":
    main()
