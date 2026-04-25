#!/usr/bin/env python3
"""
structural_hillclimb.py — hill-climb on W[57..60] using a structurally-aware
HW metric, motivated by the mitm_residue 4-d.o.f. picture at r=63.

The naive hill-climb (q5_alternative_attacks heritage) plateaus at HW=82
in 1M evals (per `bets/block2_wang/residuals/20260424_hillclimb_negative.md`).
Random sampling reaches HW=58-62 minimum (per build_corpus.py output).

This script tests whether a STRUCTURALLY-AWARE score function changes the
plateau behavior. The structural picture says r=63 has 4 modular d.o.f.:
  - da_63, db_63, dc_63, df_63 are independently free.
  - dg_63 = dc_63 (R63.1)
  - de_63 = da_63 - dT2_63 (R63.3)

Scoring options:
  raw          : sum HW over all 6 active registers (a,b,c,e,f,g)
  free4        : sum HW over the 4 free moduli only (a,b,c,f)
  weighted     : free4 + matched-de bonus (low if da ≈ dT2_63 → low de)
  hybrid       : raw with 2x weight on dc (since it pins dg too)

We compare local-search behavior under each metric.
"""
import argparse
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
from lib.sha256 import (K, MASK, sigma0, sigma1, Sigma0, Sigma1, Ch, Maj, add,
                        precompute_state)


def cascade_step_offset(s1, s2):
    dh = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    T2_1 = (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & MASK
    T2_2 = (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & MASK
    return (dh + dSig1 + dCh + T2_1 - T2_2) & MASK


def cascade2_offset(s1, s2):
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


def hw(x):
    return bin(x & MASK).count("1")


def forward_to_63(s1_init, s2_init, W1_pre, W2_pre, w1_57, w1_58, w1_59, w1_60):
    """Run cascade-held forward to round 63. Returns (state1_63, state2_63) or None."""
    cw57 = cascade_step_offset(s1_init, s2_init)
    w2_57 = (w1_57 + cw57) & MASK
    s1 = apply_round(s1_init, w1_57, 57)
    s2 = apply_round(s2_init, w2_57, 57)

    cw58 = cascade_step_offset(s1, s2)
    w2_58 = (w1_58 + cw58) & MASK
    s1 = apply_round(s1, w1_58, 58)
    s2 = apply_round(s2, w2_58, 58)

    cw59 = cascade_step_offset(s1, s2)
    w2_59 = (w1_59 + cw59) & MASK
    s1 = apply_round(s1, w1_59, 59)
    s2 = apply_round(s2, w2_59, 59)
    if any((s1[i] - s2[i]) & MASK != 0 for i in (0, 1, 2, 3)):
        return None

    cw60 = cascade2_offset(s1, s2)
    w2_60 = (w1_60 + cw60) & MASK
    s1 = apply_round(s1, w1_60, 60)
    s2 = apply_round(s2, w2_60, 60)
    if (s1[4] - s2[4]) & MASK != 0:
        return None

    W1 = list(W1_pre[:57]) + [w1_57, w1_58, w1_59, w1_60]
    W2 = list(W2_pre[:57]) + [w2_57, w2_58, w2_59, w2_60]
    for r in range(61, 64):
        W1.append(add(sigma1(W1[r-2]), W1[r-7], sigma0(W1[r-15]), W1[r-16]))
        W2.append(add(sigma1(W2[r-2]), W2[r-7], sigma0(W2[r-15]), W2[r-16]))
    for r in range(61, 64):
        s1 = apply_round(s1, W1[r], r)
        s2 = apply_round(s2, W2[r], r)
    return s1, s2


def score_residual(s1, s2, mode):
    """mode: 'raw', 'free4', 'hybrid'"""
    da = (s1[0] - s2[0]) & MASK
    db = (s1[1] - s2[1]) & MASK
    dc = (s1[2] - s2[2]) & MASK
    de = (s1[4] - s2[4]) & MASK
    df = (s1[5] - s2[5]) & MASK
    dg = (s1[6] - s2[6]) & MASK
    if mode == "raw":
        return hw(da) + hw(db) + hw(dc) + hw(de) + hw(df) + hw(dg)
    elif mode == "free4":
        return hw(da) + hw(db) + hw(dc) + hw(df)
    elif mode == "hybrid":
        return hw(da) + hw(db) + 2 * hw(dc) + hw(de) + hw(df)
    else:
        raise ValueError(mode)


def hillclimb(s1_init, s2_init, W1_pre, W2_pre, mode, n_steps, seed):
    rng = random.Random(seed)
    # Initialize random
    while True:
        w = [rng.randrange(2**32) for _ in range(4)]
        result = forward_to_63(s1_init, s2_init, W1_pre, W2_pre, *w)
        if result is not None:
            break
    s1, s2 = result
    cur_score = score_residual(s1, s2, mode)
    best_score = cur_score
    best_w = list(w)

    for step in range(n_steps):
        # Pick a random W word and bit, flip it
        wi = rng.randrange(4)
        bit = rng.randrange(32)
        w_try = list(w)
        w_try[wi] ^= (1 << bit)
        result = forward_to_63(s1_init, s2_init, W1_pre, W2_pre, *w_try)
        if result is None:
            continue
        new_score = score_residual(result[0], result[1], mode)
        if new_score <= cur_score:
            w = w_try
            cur_score = new_score
            if cur_score < best_score:
                best_score = cur_score
                best_w = list(w)

    return best_score, best_w


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m0", default="0x17149975")
    ap.add_argument("--fill", default="0xffffffff")
    ap.add_argument("--kernel-bit", type=int, default=31)
    ap.add_argument("--steps", type=int, default=100000)
    ap.add_argument("--restarts", type=int, default=5)
    args = ap.parse_args()

    m0 = int(args.m0, 16)
    fill = int(args.fill, 16)
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= (1 << args.kernel_bit)
    M2[9] ^= (1 << args.kernel_bit)
    s1_init, W1_pre = precompute_state(M1)
    s2_init, W2_pre = precompute_state(M2)

    print(f"Candidate: m0={args.m0} fill={args.fill} bit={args.kernel_bit}")
    print(f"Steps per restart: {args.steps:,}; restarts: {args.restarts}")
    print()

    for mode in ("raw", "free4", "hybrid"):
        results = []
        t0 = time.time()
        for r_idx in range(args.restarts):
            score, w = hillclimb(s1_init, s2_init, W1_pre, W2_pre,
                                 mode=mode, n_steps=args.steps, seed=42 + r_idx)
            results.append((score, w))
        elapsed = time.time() - t0

        # Re-evaluate ALL results under the RAW metric for cross-comparison
        raw_scores = []
        for score, w in results:
            r = forward_to_63(s1_init, s2_init, W1_pre, W2_pre, *w)
            raw_scores.append(score_residual(r[0], r[1], "raw"))
        print(f"mode={mode:<7} restart-best: {[s for s,_ in results]}  "
              f"raw-equiv: {raw_scores}  best-raw={min(raw_scores)}  elapsed={elapsed:.1f}s")


if __name__ == "__main__":
    main()
