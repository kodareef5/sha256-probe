#!/usr/bin/env python3
"""
Full structural validation of the cascade-DP residual at r ∈ {61, 62, 63}.

Generates fresh cascade-held samples (W[57..60] random per round, with
W2[t] = W1[t] + cascade_offset(t) computed dynamically from current state)
and checks all the structural constraints derivable from
Theorems 1-4 + shift register propagation.

Constraints checked at each round:

r=61 (active regs {a,e,g,h}, 4 regs):
    R61.1:  da_61 ≡ de_61 (mod 2^32)              — Theorem 4 r=61

r=62 (active regs {a,b,e,f,h}, 5 regs):
    R62.1:  db_62 ≡ df_62 (mod 2^32)              — both = da_61 = de_61 (R61.1 + shift)
    R62.2:  da_62 − de_62 ≡ dT2_62 (mod 2^32)     — unified Thm4 at r=62

r=63 (active regs {a,b,c,e,f,g}, 6 regs):
    R63.1:  dc_63 ≡ dg_63 (mod 2^32)              — both = da_61 = de_61
    R63.2:  db_63 − df_63 ≡ dT2_62 (mod 2^32)     — unified Thm4 at r=62 via shift
    R63.3:  da_63 − de_63 ≡ dT2_63 (mod 2^32)     — unified Thm4 at r=63

Plus the cascade-zero (negative) checks: dd_63 = 0, dh_63 = 0.
"""
import argparse
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
from lib.sha256 import (K, MASK, sigma0, sigma1, Sigma0, Sigma1, Ch, Maj, add,
                        precompute_state)


def cascade_step_offset(s1_r, s2_r):
    dh = (s1_r[7] - s2_r[7]) & MASK
    dSig1 = (Sigma1(s1_r[4]) - Sigma1(s2_r[4])) & MASK
    dCh = (Ch(s1_r[4], s1_r[5], s1_r[6]) - Ch(s2_r[4], s2_r[5], s2_r[6])) & MASK
    T2_1 = (Sigma0(s1_r[0]) + Maj(s1_r[0], s1_r[1], s1_r[2])) & MASK
    T2_2 = (Sigma0(s2_r[0]) + Maj(s2_r[0], s2_r[1], s2_r[2])) & MASK
    return (dh + dSig1 + dCh + T2_1 - T2_2) & MASK


def cascade2_offset(s1_r59, s2_r59):
    dh = (s1_r59[7] - s2_r59[7]) & MASK
    dSig1 = (Sigma1(s1_r59[4]) - Sigma1(s2_r59[4])) & MASK
    dCh = (Ch(s1_r59[4], s1_r59[5], s1_r59[6]) - Ch(s2_r59[4], s2_r59[5], s2_r59[6])) & MASK
    return (dh + dSig1 + dCh) & MASK


def apply_round(state, w, r):
    T1 = add(state[7], Sigma1(state[4]), Ch(state[4], state[5], state[6]), K[r], w)
    T2 = add(Sigma0(state[0]), Maj(state[0], state[1], state[2]))
    a = add(T1, T2)
    e = add(state[3], T1)
    return (a, state[0], state[1], state[2], e, state[4], state[5], state[6])


def diff_modular(s1, s2):
    return tuple((s1[i] - s2[i]) & MASK for i in range(8))


def run_one(s1_init, s2_init, W1_pre, W2_pre, w1_57, w1_58, w1_59, w1_60):
    """Run one cascade-held sample to round 63. Returns (s1_60, s2_60, ..., s1_63, s2_63, W1, W2)."""
    cw57 = cascade_step_offset(s1_init, s2_init)
    w2_57 = (w1_57 + cw57) & MASK
    s1_57 = apply_round(s1_init, w1_57, 57)
    s2_57 = apply_round(s2_init, w2_57, 57)

    cw58 = cascade_step_offset(s1_57, s2_57)
    w2_58 = (w1_58 + cw58) & MASK
    s1_58 = apply_round(s1_57, w1_58, 58)
    s2_58 = apply_round(s2_57, w2_58, 58)

    cw59 = cascade_step_offset(s1_58, s2_58)
    w2_59 = (w1_59 + cw59) & MASK
    s1_59 = apply_round(s1_58, w1_59, 59)
    s2_59 = apply_round(s2_58, w2_59, 59)

    if any((s1_59[i] - s2_59[i]) & MASK != 0 for i in (0, 1, 2, 3)):
        return None

    cw60 = cascade2_offset(s1_59, s2_59)
    w2_60 = (w1_60 + cw60) & MASK
    s1_60 = apply_round(s1_59, w1_60, 60)
    s2_60 = apply_round(s2_59, w2_60, 60)
    if (s1_60[4] - s2_60[4]) & MASK != 0:
        return None

    W1 = list(W1_pre[:57]) + [w1_57, w1_58, w1_59, w1_60]
    W2 = list(W2_pre[:57]) + [w2_57, w2_58, w2_59, w2_60]
    for r in range(61, 64):
        W1.append(add(sigma1(W1[r - 2]), W1[r - 7], sigma0(W1[r - 15]), W1[r - 16]))
        W2.append(add(sigma1(W2[r - 2]), W2[r - 7], sigma0(W2[r - 15]), W2[r - 16]))

    s1, s2 = s1_60, s2_60
    states1, states2 = [s1], [s2]
    for r in range(61, 64):
        s1 = apply_round(s1, W1[r], r)
        s2 = apply_round(s2, W2[r], r)
        states1.append(s1)
        states2.append(s2)

    return states1, states2  # indices: 0=r60, 1=r61, 2=r62, 3=r63


def check_constraints(states1, states2):
    """Returns dict of constraint_name -> bool (satisfied?)."""
    s1_60, s1_61, s1_62, s1_63 = states1
    s2_60, s2_61, s2_62, s2_63 = states2

    # Round-61 active register diffs
    da_61 = (s1_61[0] - s2_61[0]) & MASK
    de_61 = (s1_61[4] - s2_61[4]) & MASK

    # Round-62 active register diffs
    da_62 = (s1_62[0] - s2_62[0]) & MASK
    db_62 = (s1_62[1] - s2_62[1]) & MASK
    de_62 = (s1_62[4] - s2_62[4]) & MASK
    df_62 = (s1_62[5] - s2_62[5]) & MASK

    # Round-63 active register diffs
    da_63 = (s1_63[0] - s2_63[0]) & MASK
    db_63 = (s1_63[1] - s2_63[1]) & MASK
    dc_63 = (s1_63[2] - s2_63[2]) & MASK
    de_63 = (s1_63[4] - s2_63[4]) & MASK
    df_63 = (s1_63[5] - s2_63[5]) & MASK
    dg_63 = (s1_63[6] - s2_63[6]) & MASK

    # dT2_62 = dSigma0(a_61) + dMaj(a_61, b_61, c_61); b_61=a_60, c_61=a_59=b_60
    a1_61, a2_61 = s1_61[0], s2_61[0]
    a1_60, a2_60 = s1_60[0], s2_60[0]
    a1_59, a2_59 = s1_60[1], s2_60[1]  # b_60 = a_59
    dSigma0_a61 = (Sigma0(a1_61) - Sigma0(a2_61)) & MASK
    dMaj_61 = (Maj(a1_61, a1_60, a1_59) - Maj(a2_61, a2_60, a2_59)) & MASK
    dT2_62 = (dSigma0_a61 + dMaj_61) & MASK

    # dT2_63 = dSigma0(a_62) + dMaj(a_62, a_61, a_60); b_62=a_61, c_62=a_60
    a1_62, a2_62 = s1_62[0], s2_62[0]
    dSigma0_a62 = (Sigma0(a1_62) - Sigma0(a2_62)) & MASK
    dMaj_62 = (Maj(a1_62, a1_61, a1_60) - Maj(a2_62, a2_61, a2_60)) & MASK
    dT2_63 = (dSigma0_a62 + dMaj_62) & MASK

    return {
        "R61.1": da_61 == de_61,
        "R62.1": db_62 == df_62,
        "R62.2": ((da_62 - de_62) & MASK) == dT2_62,
        "R63.1": dc_63 == dg_63,
        "R63.2": ((db_63 - df_63) & MASK) == dT2_62,
        "R63.3": ((da_63 - de_63) & MASK) == dT2_63,
        "Z63d": (s1_63[3] - s2_63[3]) & MASK == 0,
        "Z63h": (s1_63[7] - s2_63[7]) & MASK == 0,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m0", default="0x17149975")
    ap.add_argument("--fill", default="0xffffffff")
    ap.add_argument("--kernel-bit", type=int, default=31)
    ap.add_argument("--samples", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    m0 = int(args.m0, 16)
    fill = int(args.fill, 16)
    diff = 1 << args.kernel_bit
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= diff
    M2[9] ^= diff
    s1_init, W1_pre = precompute_state(M1)
    s2_init, W2_pre = precompute_state(M2)

    if s1_init[0] != s2_init[0]:
        print(f"ERROR: candidate not cascade-eligible (da_56 != 0)", file=sys.stderr)
        sys.exit(2)

    rng = random.Random(args.seed)
    counts = {k: 0 for k in ("R61.1", "R62.1", "R62.2", "R63.1", "R63.2", "R63.3", "Z63d", "Z63h")}
    n_held = 0
    n_failed_cascade = 0

    for _ in range(args.samples):
        w1_57 = rng.randrange(2**32)
        w1_58 = rng.randrange(2**32)
        w1_59 = rng.randrange(2**32)
        w1_60 = rng.randrange(2**32)
        result = run_one(s1_init, s2_init, W1_pre, W2_pre, w1_57, w1_58, w1_59, w1_60)
        if result is None:
            n_failed_cascade += 1
            continue
        states1, states2 = result
        n_held += 1
        for k, ok in check_constraints(states1, states2).items():
            if ok:
                counts[k] += 1

    print(f"candidate: m0={args.m0} fill={args.fill} bit={args.kernel_bit}")
    print(f"samples requested: {args.samples}, cascade-held: {n_held}, "
          f"cascade-broke: {n_failed_cascade}")
    print()
    print("Modular constraints (each row should be n_held / n_held = 100%):")
    for k in ("R61.1", "R62.1", "R62.2", "R63.1", "R63.2", "R63.3", "Z63d", "Z63h"):
        rate = counts[k] / n_held * 100 if n_held else 0
        print(f"  {k}: {counts[k]}/{n_held} ({rate:.4f}%)")


if __name__ == "__main__":
    main()
