#!/usr/bin/env python3
"""residual_dimension_growth.py — How does the residual grow from r=60 to r=63?

The multi_residual finding showed: at r=60 (cascade boundary) the only varying
register diff is de58 (image up to 2^18). All others are candidate-fixed.

Question: as we extend through r=61, 62, 63 using the actual SHA-256 message
schedule (NO more cascade-extending), how do the per-round register diffs
(da_r, de_r) grow in image size?

Setup per sample W57 random:
  - cascade-1 forces da[57..60]=0 via cw57 (function of state56) and
    cascade-extending W2[58,59,60] = cw58,cw59,cw60 (functions of state57+).
  - cascade-2 forces de60=0 via cw60' (chosen so da[60] AND de[60] both 0;
    in our setup we use cascade2_offset which gives de60=0; the da_60=0 also
    holds because of cascade-extending construction).
  - For r ∈ {61, 62, 63}: W1[r] = schedule(W1[44..r-1]); W2[r] = schedule(W2[44..r-1]).
    No more cascade choice. dW[r] is determined.

Outputs per candidate: image size of (da_r, de_r) at r ∈ {60, 61, 62, 63}.

Hypothesis from multi_residual writeup: at r=61, 62, 63 the residual expands
to multiple d.o.f. Empirical 4-d.o.f. claim at r=63 should appear here.
"""
import argparse
import json
import math
import os
import random
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
from lib.sha256 import (K, MASK, Sigma0, Sigma1, Ch, Maj, sigma0, sigma1,
                         add, precompute_state)


def cascade1_offset(s1, s2):
    """W2[r] - W1[r] forcing da[r] = 0 modular at round r, given states before r."""
    dh = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    T2_1 = (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & MASK
    T2_2 = (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & MASK
    return (dh + dSig1 + dCh + T2_1 - T2_2) & MASK


def cascade2_offset(s1, s2):
    """W2[r] - W1[r] forcing de[r] = 0 modular at round r."""
    dh = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    return (dh + dSig1 + dCh) & MASK


def apply_round(state, w, r):
    T1 = add(state[7], Sigma1(state[4]), Ch(state[4], state[5], state[6]), K[r], w)
    T2 = add(Sigma0(state[0]), Maj(state[0], state[1], state[2]))
    a = add(T1, T2)
    e = add(state[3], T1)
    return (a, state[0], state[1], state[2], e, state[4], state[5], state[6])


def sweep_candidate(m0, fill, kernel_bit, n_samples, seed=42):
    """Sample W57 random; trace through r=63 with schedule; collect register diffs."""
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= (1 << kernel_bit)
    M2[9] ^= (1 << kernel_bit)
    s1, W1_pre = precompute_state(M1)
    s2, W2_pre = precompute_state(M2)
    if s1[0] != s2[0]:
        return None  # not cascade-eligible (a-collision at r=56)

    cw57 = cascade1_offset(s1, s2)
    rng = random.Random(seed)

    # collectors per round per register
    per_round_diff = {r: {reg: Counter() for reg in "abcdefgh"} for r in range(60, 64)}
    joint = {r: Counter() for r in range(60, 64)}  # (da_r, de_r) joint
    n_held = 0

    for _ in range(n_samples):
        w1_57 = rng.randrange(1 << 32)
        w2_57 = (w1_57 + cw57) & MASK

        # build per-pair full schedule W1[0..63], W2[0..63]
        W1 = list(W1_pre) + [0] * 7   # placeholders for 57..63
        W2 = list(W2_pre) + [0] * 7
        W1[57] = w1_57
        W2[57] = w2_57

        # apply round 57
        s1_57 = apply_round(s1, w1_57, 57)
        s2_57 = apply_round(s2, w2_57, 57)
        if (s1_57[0] - s2_57[0]) & MASK != 0:
            continue

        # cascade-extending W[58,59,60]: pair-1 = 0 canonical, pair-2 = cwN
        W1[58] = 0
        W2[58] = cascade1_offset(s1_57, s2_57)
        s1_58 = apply_round(s1_57, W1[58], 58)
        s2_58 = apply_round(s2_57, W2[58], 58)
        if (s1_58[0] - s2_58[0]) & MASK != 0:
            continue

        W1[59] = 0
        W2[59] = cascade1_offset(s1_58, s2_58)
        s1_59 = apply_round(s1_58, W1[59], 59)
        s2_59 = apply_round(s2_58, W2[59], 59)
        if (s1_59[0] - s2_59[0]) & MASK != 0:
            continue

        # cascade-2 at r=60: force de_60=0
        W1[60] = 0
        W2[60] = cascade2_offset(s1_59, s2_59)
        s1_60 = apply_round(s1_59, W1[60], 60)
        s2_60 = apply_round(s2_59, W2[60], 60)

        # r=61..63: schedule, NO cascade choice
        for r in range(61, 64):
            W1[r] = add(sigma1(W1[r-2]), W1[r-7], sigma0(W1[r-15]), W1[r-16])
            W2[r] = add(sigma1(W2[r-2]), W2[r-7], sigma0(W2[r-15]), W2[r-16])

        s1_61 = apply_round(s1_60, W1[61], 61)
        s2_61 = apply_round(s2_60, W2[61], 61)
        s1_62 = apply_round(s1_61, W1[62], 62)
        s2_62 = apply_round(s2_61, W2[62], 62)
        s1_63 = apply_round(s1_62, W1[63], 63)
        s2_63 = apply_round(s2_62, W2[63], 63)

        states_pair = [(s1_60, s2_60), (s1_61, s2_61), (s1_62, s2_62), (s1_63, s2_63)]
        for r, (sA, sB) in zip(range(60, 64), states_pair):
            for i, reg in enumerate("abcdefgh"):
                d = (sA[i] - sB[i]) & MASK
                per_round_diff[r][reg][d] += 1
            da = (sA[0] - sB[0]) & MASK
            de = (sA[4] - sB[4]) & MASK
            joint[r][(da, de)] += 1

        n_held += 1

    return per_round_diff, joint, n_held


def report_image(counter):
    n = sum(counter.values())
    if n == 0:
        return {"n": 0, "distinct": 0, "log2": None}
    distinct = len(counter)
    log2 = math.log2(distinct) if distinct > 1 else 0.0
    return {"n": n, "distinct": distinct, "log2": round(log2, 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=1<<16)
    ap.add_argument("--candidates", default="top5",
                    help="top5 | all | comma-separated tags")
    args = ap.parse_args()

    pool = [
        ("0x51ca0b34", "0x55555555", 19, "bit19_TOP"),
        ("0x9cfea9ce", "0x00000000", 31, "msb_m9cfea9ce_fill0_SURPRISE"),
        ("0x09990bd2", "0x80000000", 25, "bit25"),
        ("0x56076c68", "0x55555555", 11, "bit11"),
        ("0xbee3704b", "0x00000000", 13, "bit13"),
        ("0x17149975", "0xffffffff", 31, "MSB_CERT"),
        ("0x189b13c7", "0x80000000", 31, "msb_m189b13c7_BOTTOM"),
    ]

    print(f"# residual_dimension_growth: r=60..63 image sizes per register, n_samples={args.samples}",
          file=sys.stderr)

    for m0_hex, fill_hex, bit, tag in pool:
        t0 = time.time()
        result = sweep_candidate(int(m0_hex, 16), int(fill_hex, 16), bit, args.samples)
        elapsed = time.time() - t0
        if result is None:
            print(json.dumps({"tag": tag, "error": "not cascade-eligible"}))
            continue
        per_round, joint, n_held = result
        rec = {
            "tag": tag, "m0": m0_hex, "fill": fill_hex, "bit": bit,
            "n_held": n_held, "elapsed_s": round(elapsed, 1),
        }
        for r in range(60, 64):
            rec[f"r{r}"] = {
                reg: report_image(per_round[r][reg]) for reg in "abcdefgh"
            }
            rec[f"r{r}_joint_da_de"] = report_image(joint[r])
        print(json.dumps(rec))
        sys.stdout.flush()


if __name__ == "__main__":
    main()
