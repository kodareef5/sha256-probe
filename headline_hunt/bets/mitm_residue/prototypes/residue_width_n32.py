#!/usr/bin/env python3
"""Measure the effective hard-residue width of the cascade sr=60 MITM at full N=32.

Tests the bet's headline claim ("~24 effective bits in g60/h60; 232/256 anchor bits
almost free"). Method: on the verified sr=60 cert base, sweep W1[57] (W58,W59 fixed
to cert; W60 set per-state by the cascade-2 offset so de60=0 -> de/df/dg/dh=0
through round 63). For each W57, run rounds 57..63 and accumulate the OR of the
round-63 register differences (the "active-bit mask"). popcount(active mask),
restricted to a,b,c,d (e,f,g,h collide for free via cascade-2), is an upper bound
on the effective residue width. Also tracks the round-63 residual HW distribution.

Reuses lib.sha256 (precompute_state, build_schedule_tail, run_tail_rounds) — no
SHA reimplementation. Single-process; run several with different --seed to cover
more of the W57 space in parallel and OR the printed masks.

Usage: residue_width_n32.py [n_samples] [seed]
"""
import os
import sys
import time
import random

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, REPO)
from lib.sha256 import (  # noqa: E402
    MASK, Sigma1, Ch, hw, add, precompute_state, build_schedule_tail, run_tail_rounds,
)

M0 = 0x17149975
FILL = 0xFFFFFFFF
W1_CERT = [0x9ccfa55e, 0xd9d64416, 0x9e3ffb08, 0xb6befe82]
W2_CERT = [0x72e6c8cd, 0x4b96ca51, 0x587ffaa6, 0xea3ce26b]
REG = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']


def cascade1_offset(s1, s2):
    """W2[57] = W1[57] + C s.t. da57 = 0 (cascade-1 init)."""
    from lib.sha256 import Sigma0, Maj
    dh = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    dT2 = ((Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2]))
           - (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2]))) & MASK
    return (dh + dSig1 + dCh + dT2) & MASK


def cascade2_offset(s1_59, s2_59):
    """W2[60] = W1[60] + C s.t. de60 = 0, given round-59 states."""
    dh = (s1_59[7] - s2_59[7]) & MASK
    dSig1 = (Sigma1(s1_59[4]) - Sigma1(s2_59[4])) & MASK
    dCh = (Ch(s1_59[4], s1_59[5], s1_59[6]) - Ch(s2_59[4], s2_59[5], s2_59[6])) & MASK
    return (dh + dSig1 + dCh) & MASK


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else (1 << 20)
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42

    M1 = [M0] + [FILL] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1_init, W1_pre = precompute_state(M1)
    s2_init, W2_pre = precompute_state(M2)
    C_w57 = cascade1_offset(s1_init, s2_init)
    assert (W1_CERT[0] + C_w57) & MASK == W2_CERT[0], "cascade-1 offset != cert"

    rng = random.Random(seed)
    active = [0] * 8          # OR of round-63 register diffs
    hist = {}                 # round-63 total-HW histogram
    abcd_hist = {}            # abcd63-only HW histogram
    min_total = 256
    min_abcd = 128
    broke = 0
    t0 = time.time()

    for trial in range(n):
        w1_57 = W1_CERT[0] if trial == 0 else rng.getrandbits(32)
        w2_57 = (w1_57 + C_w57) & MASK

        # rounds 57..59 to get round-59 states (3 free words)
        tr1 = run_tail_rounds(s1_init, [w1_57, W1_CERT[1], W1_CERT[2]])
        tr2 = run_tail_rounds(s2_init, [w2_57, W2_CERT[1], W2_CERT[2]])
        s1_59, s2_59 = tr1[3], tr2[3]

        C_w60 = cascade2_offset(s1_59, s2_59)
        w1_60 = W1_CERT[3]
        w2_60 = (w1_60 + C_w60) & MASK

        sched1 = build_schedule_tail(W1_pre, [w1_57, W1_CERT[1], W1_CERT[2], w1_60])
        sched2 = build_schedule_tail(W2_pre, [w2_57, W2_CERT[1], W2_CERT[2], w2_60])
        r63_1 = run_tail_rounds(s1_init, sched1)[7]
        r63_2 = run_tail_rounds(s2_init, sched2)[7]
        diff = [(r63_1[i] ^ r63_2[i]) & MASK for i in range(8)]

        for i in range(8):
            active[i] |= diff[i]
        efgh_hw = sum(hw(diff[i]) for i in range(4, 8))
        if efgh_hw != 0:
            broke += 1
        total = sum(hw(d) for d in diff)
        abcd = sum(hw(diff[i]) for i in range(4))
        hist[total] = hist.get(total, 0) + 1
        abcd_hist[abcd] = abcd_hist.get(abcd, 0) + 1
        min_total = min(min_total, total)
        min_abcd = min(min_abcd, abcd)

    dt = time.time() - t0
    abcd_active = sum(hw(active[i]) for i in range(4))
    efgh_active = sum(hw(active[i]) for i in range(4, 8))
    print(f"N=32 RESIDUE WIDTH  samples={n} seed={seed}  ({n/dt:.0f}/s)")
    print(f"cascade-2 efgh63 breaks (should be 0): {broke}")
    print("active-bit mask per register (bits that ever differ over the W57 sweep):")
    for i in range(8):
        print(f"  d{REG[i]}63 active=0x{active[i]:08x} hw={hw(active[i])}")
    print(f"EFFECTIVE RESIDUE WIDTH (abcd63 active bits) = {abcd_active}")
    print(f"  (efgh63 active bits = {efgh_active}, expected 0 via cascade-2)")
    print(f"min round-63 total HW = {min_total}; min abcd63 HW = {min_abcd}")
    print("abcd63 HW histogram (low end):", dict(sorted(abcd_hist.items())[:12]))


if __name__ == "__main__":
    main()
