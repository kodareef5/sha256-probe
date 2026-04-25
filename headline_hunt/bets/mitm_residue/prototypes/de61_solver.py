#!/usr/bin/env python3
"""
de61_solver.py — Per-triple closed-form solver for de61 = 0.

Given a (W1[57], W1[58], W1[59]) triple on a cascade-eligible candidate,
determine whether any W1[60] choice can make de61 = 0 modular, and if so,
return the set of valid W1[60] values.

Theory (see results/20260424_dch_controllability.md):
  de61 = dh60 + dSigma1(e60) + dCh(e60, f60, g60) + dW[61]   (mod 2^32)

  - dSigma1(e60) = 0 since cascade gives e1_60 = e2_60 (de60 = 0)
  - dh60, dW[61], df60, dg60 are FIXED for the given triple
  - dCh = (e60 AND ctrl_mask) XOR dg60, where ctrl_mask = df60 XOR dg60
  - e60 = const + W1[60] (mod 2^32) — 32-bit free choice via W1[60]

Set target = -(dh60 + dW[61]) mod 2^32. Need dCh ≡ target mod 2^32.

Equivalently (since dCh < 2^32 as integer):
  (e60 AND ctrl_mask) XOR dg60 == target
  → e60 AND ctrl_mask == target XOR dg60

Compatibility check: target XOR dg60 must have zero bits outside ctrl_mask.
  → (target XOR dg60) AND (NOT ctrl_mask) == 0  ... (14-bit constraint, prob 2^-14)

If compatible: e60 must satisfy:
  - ctrl_mask=1 bits: e60[i] = (target XOR dg60)[i]   FIXED
  - ctrl_mask=0 bits: e60[i] is FREE                  → 2^(32 − HW(ctrl_mask)) options

Each valid e60 yields W1[60] = e60 − e60_const (mod 2^32) for some const.

Usage:
    python3 de61_solver.py --m0 0x51ca0b34 --fill 0x55555555 --kernel-bit 19 \
        --w57 0x... --w58 0x... --w59 0x... [--list-witnesses N]
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, REPO)
from lib.sha256 import (K, MASK, sigma0, sigma1, Sigma0, Sigma1, Ch, Maj,
                        add, precompute_state)
sys.path.insert(0, HERE)
from forward_table_builder import cascade_step_offset, cascade2_offset, apply_round


def solve_de61(s1_init, s2_init, W1_pre, W2_pre, w1_57, w1_58, w1_59):
    """Return dict with compatibility status and (if compatible) W1[60] solutions."""
    # Forward through rounds 57, 58, 59
    cw57 = cascade_step_offset(s1_init, s2_init, 57)
    w2_57 = (w1_57 + cw57) & MASK
    s1_57 = apply_round(s1_init, w1_57, 57)
    s2_57 = apply_round(s2_init, w2_57, 57)

    cw58 = cascade_step_offset(s1_57, s2_57, 58)
    w2_58 = (w1_58 + cw58) & MASK
    s1_58 = apply_round(s1_57, w1_58, 58)
    s2_58 = apply_round(s2_57, w2_58, 58)

    cw59 = cascade_step_offset(s1_58, s2_58, 59)
    w2_59 = (w1_59 + cw59) & MASK
    s1_59 = apply_round(s1_58, w1_59, 59)
    s2_59 = apply_round(s2_58, w2_59, 59)

    if (s1_59[1] ^ s2_59[1]) or (s1_59[2] ^ s2_59[2]) or (s1_59[3] ^ s2_59[3]):
        return {"compatible": False, "reason": "cascade-1 broke at round 59"}

    cw60 = cascade2_offset(s1_59, s2_59)

    # Round-60 with placeholder W1[60] = 0 just to get f60, g60, h60 (these don't depend on W1[60]).
    # df60 = de59, dg60 = de58, dh60 = de57 — independent of W1[60].
    s1_60_dummy = apply_round(s1_59, 0, 60)
    s2_60_dummy = apply_round(s2_59, (0 + cw60) & MASK, 60)
    df60 = (s1_60_dummy[5] ^ s2_60_dummy[5])
    dg60 = (s1_60_dummy[6] ^ s2_60_dummy[6])
    dh60 = (s1_60_dummy[7] ^ s2_60_dummy[7])
    # h60 modular diff
    dh60_mod = (s1_60_dummy[7] - s2_60_dummy[7]) & MASK

    # Constant base for e60: e60 = b56 + T1_60 = b56 + (h59 + Sigma1(e59) + Ch + K[60] + W1[60])
    # All terms except W1[60] are fixed for this triple.
    e60_base_1 = add(s1_59[3], s1_59[7], Sigma1(s1_59[4]),
                      Ch(s1_59[4], s1_59[5], s1_59[6]), K[60])
    # When W1[60] = w, e1_60 = (e60_base_1 + w) mod 2^32

    # dW[61] modular: W[61] = sigma1(W[59]) + W_pre[54] + sigma0(W_pre[46]) + W_pre[45]
    w1_61 = add(sigma1(w1_59), W1_pre[54], sigma0(W1_pre[46]), W1_pre[45])
    w2_61 = add(sigma1(w2_59), W2_pre[54], sigma0(W2_pre[46]), W2_pre[45])
    dW61_mod = (w1_61 - w2_61) & MASK

    # Required dCh = target (modular) where target = -(dh60_mod + dW61_mod)
    target = (-(dh60_mod + dW61_mod)) & MASK

    # Compatibility: dCh_xor = (e60 AND ctrl_mask) XOR dg60. We want dCh_modular_value = target.
    # NOTE: dCh as a 32-bit integer equals its XOR representation (it's an unsigned 32-bit value).
    # So we want u := (e60 AND ctrl_mask) such that u XOR dg60 == target (as ints).
    # → u = target XOR dg60.
    # Compat: u must have only bits within ctrl_mask.
    ctrl_mask = df60 ^ dg60
    u = target ^ dg60
    incompatible_bits = u & (~ctrl_mask & MASK)
    if incompatible_bits != 0:
        return {
            "compatible": False,
            "reason": f"u (target XOR dg60) has bits outside ctrl_mask",
            "ctrl_mask": ctrl_mask,
            "ctrl_hw": bin(ctrl_mask).count('1'),
            "u": u,
            "incompatible_bits": incompatible_bits,
            "incompatible_hw": bin(incompatible_bits).count('1'),
        }

    # Compatible. Number of valid e60 = 2^(32 - HW(ctrl_mask)).
    free_bits = 32 - bin(ctrl_mask).count('1')
    e60_const = e60_base_1
    # Required (e60 AND ctrl_mask) = u.
    # → e60[i] = u[i] for ctrl_mask[i] = 1; free for ctrl_mask[i] = 0
    # All e60s of form: u | (any subset of ~ctrl_mask bits).
    # Witness W1[60] = (e60 - e60_const) mod 2^32 for each.
    e60_fixed = u  # bits in ctrl_mask are correct; bits outside are 0
    return {
        "compatible": True,
        "ctrl_mask": ctrl_mask,
        "ctrl_hw": bin(ctrl_mask).count('1'),
        "free_bits": free_bits,
        "valid_e60_count": 1 << free_bits,
        "e60_fixed_pattern": e60_fixed,  # ctrl-bit pattern; free bits to enumerate
        "e60_const": e60_const,
        "first_w1_60": (e60_fixed - e60_const) & MASK,
        "df60": df60,
        "dg60": dg60,
        "dh60": dh60,
        "target": target,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m0", default="0x51ca0b34")
    ap.add_argument("--fill", default="0x55555555")
    ap.add_argument("--kernel-bit", type=int, default=19)
    ap.add_argument("--samples", type=int, default=10000,
                    help="Number of (W57,W58,W59) triples to sample and try")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    m0 = int(args.m0, 16); fill = int(args.fill, 16); kbit = args.kernel_bit
    M1 = [m0] + [fill]*15; M2 = list(M1); M2[0] ^= 1<<kbit; M2[9] ^= 1<<kbit
    s1, W1p = precompute_state(M1); s2, W2p = precompute_state(M2)
    if s1[0] != s2[0]:
        print("ERROR: not cascade-eligible", file=sys.stderr); sys.exit(2)

    import random, time
    rng = random.Random(args.seed)
    n_compat = 0
    n_incompat = 0
    n_cascade_break = 0
    free_bits_dist = []
    incompat_hw = []
    t0 = time.time()
    for trial in range(args.samples):
        result = solve_de61(s1, s2, W1p, W2p,
                             rng.getrandbits(32), rng.getrandbits(32),
                             rng.getrandbits(32))
        if not result["compatible"]:
            if "cascade-1 broke" in result["reason"]:
                n_cascade_break += 1
            else:
                n_incompat += 1
                incompat_hw.append(result["incompatible_hw"])
        else:
            n_compat += 1
            free_bits_dist.append(result["free_bits"])
    elapsed = time.time() - t0
    print(f"Sampled {args.samples} triples in {elapsed:.2f}s ({args.samples/elapsed:.0f}/s)")
    print(f"  cascade-1 broke:    {n_cascade_break}")
    print(f"  de61 INCOMPATIBLE:  {n_incompat}  (mean misfit HW: {sum(incompat_hw)/max(1,len(incompat_hw)):.1f})")
    print(f"  de61 COMPATIBLE:    {n_compat}")
    if n_compat:
        print(f"  Compatible rate:    {100*n_compat/args.samples:.4f}%  (expect 2^-14 = 0.006%)")
        print(f"  Free bits per compatible triple: mean {sum(free_bits_dist)/len(free_bits_dist):.1f}")


if __name__ == "__main__":
    main()


# =====================================================================
# WARNING (2026-04-24): THIS SOLVER IS NON-FUNCTIONAL.
# Conflated XOR-difference and modular-difference for dCh. The XOR
# expression `(e60 AND ctrl_mask) XOR dg60` is correct, but equating
# it with a MODULAR target is wrong. See:
#   results/20260424_de61_solver_bug.md
#
# Empirically: solver claims compatibility on ~0.04% of triples, but
# de61 verified to be non-zero (e.g. 0xeffe61d0) on every "compatible"
# triple. The XOR-vs-modular conversion is the open multi-day problem
# (Lipmaa-Moriai style).
#
# DO NOT USE the solver's `compatible: True` results as evidence of
# de61=0. The dCh controllability ANALYSIS (results/20260424_dch_*)
# remains valid — only the bridge to modular satisfaction is broken.
# =====================================================================
