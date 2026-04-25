#!/usr/bin/env python3
"""multi_residual_compression.py — Extend de58 predictor to multiple residual vars.

The de58 finding showed bit-19's de58 image is 2^8 (24-bit compression).
Question: do OTHER residual variables (de57, de59, dh60, df60, dg60) also
show structural compression? If multiple residuals are jointly compressed,
the cascade-DP search at bit-19 has even more structure to exploit.

Method (per candidate):
  Sample W57 random; trace cascade through round 60 (cascade-1 keeps da[57..60]=0,
  cascade-2 forces de60=0). Record:
    - de57 (= e1_57 - e2_57 modular)
    - de58 (after applying cascade-extending W58)
    - de59 (further extension)
    - dh60 = dg59 = df58 = de57  (shift register equality, sanity check)
    - dg60 = df59 = de58                (shift register)
    - df60 = de59                        (shift register)

  Compute distinct counts per variable.

Observation: by shift register, dh60 = de57, dg60 = de58, df60 = de59.
So measuring these is just measuring (de57, de58, de59).
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
from lib.sha256 import (K, MASK, Sigma0, Sigma1, Ch, Maj, add, precompute_state)


def cascade_offset(s1, s2):
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


def candidate_residuals(m0, fill, kernel_bit, n_samples, seed=42):
    """Sample n W57 random, compute residual variables. Returns dict of Counters."""
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= (1 << kernel_bit)
    M2[9] ^= (1 << kernel_bit)
    s1, _ = precompute_state(M1)
    s2, _ = precompute_state(M2)
    if s1[0] != s2[0]:
        return None

    cw57 = cascade_offset(s1, s2)
    rng = random.Random(seed)

    counts = {
        "de57": Counter(),
        "de58": Counter(),
        "de59": Counter(),
        "dh60": Counter(),
        "dg60": Counter(),
        "df60": Counter(),
        "joint_de57_de58": Counter(),  # joint distribution
    }
    n_held = 0
    for _ in range(n_samples):
        w1_57 = rng.randrange(1 << 32)
        w2_57 = (w1_57 + cw57) & MASK
        s1_57 = apply_round(s1, w1_57, 57)
        s2_57 = apply_round(s2, w2_57, 57)
        if (s1_57[0] - s2_57[0]) & MASK != 0:
            continue
        de57 = (s1_57[4] - s2_57[4]) & MASK

        # Extend to round 58 with cascade
        cw58 = cascade_offset(s1_57, s2_57)
        w1_58 = 0  # canonical choice
        s1_58 = apply_round(s1_57, w1_58, 58)
        s2_58 = apply_round(s2_57, cw58, 58)
        if (s1_58[0] - s2_58[0]) & MASK != 0:
            continue
        de58 = (s1_58[4] - s2_58[4]) & MASK

        # Extend to round 59
        cw59 = cascade_offset(s1_58, s2_58)
        w1_59 = 0
        s1_59 = apply_round(s1_58, w1_59, 59)
        s2_59 = apply_round(s2_58, cw59, 59)
        if (s1_59[0] - s2_59[0]) & MASK != 0:
            continue
        de59 = (s1_59[4] - s2_59[4]) & MASK

        # Extend to round 60 with cascade-2 (forces de60 = 0)
        cw60 = cascade2_offset(s1_59, s2_59)
        w1_60 = 0
        s1_60 = apply_round(s1_59, w1_60, 60)
        s2_60 = apply_round(s2_59, cw60, 60)
        # de60 should be 0 by construction
        # dh60 = g59 (shift register); dg60 = f59 = e58; df60 = e59
        dh60 = (s1_60[7] - s2_60[7]) & MASK
        dg60 = (s1_60[6] - s2_60[6]) & MASK
        df60 = (s1_60[5] - s2_60[5]) & MASK

        n_held += 1
        counts["de57"][de57] += 1
        counts["de58"][de58] += 1
        counts["de59"][de59] += 1
        counts["dh60"][dh60] += 1
        counts["dg60"][dg60] += 1
        counts["df60"][df60] += 1
        counts["joint_de57_de58"][(de57, de58)] += 1

    return counts, n_held


def report(name, counts):
    n = sum(counts.values())
    if n == 0:
        return {"name": name, "distinct": 0, "log2_image": None}
    distinct = len(counts)
    entropy = -sum((c/n) * math.log2(c/n) for c in counts.values() if c > 0)
    log2_dist = math.log2(distinct) if distinct > 0 else 0
    compression = (32 - log2_dist) if log2_dist > 0 else 0
    if name == "joint_de57_de58":
        compression = 64 - log2_dist  # joint of two 32-bit values
    return {"name": name, "distinct": distinct, "log2_image": round(log2_dist, 2),
            "compression_bits": round(compression, 2), "entropy_bits": round(entropy, 2)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=1<<18)
    args = ap.parse_args()

    # Top 5 from de58 ranking + MSB cert for comparison
    candidates = [
        ("0x51ca0b34", "0x55555555", 19, "bit-19 (TOP)"),
        ("0x9cfea9ce", "0x00000000", 31, "MSB-m9cfea9ce-fill0 (#2)"),
        ("0x09990bd2", "0x80000000", 25, "bit-25 (#3)"),
        ("0x56076c68", "0x55555555", 11, "bit-11_m56076c68 (#4)"),
        ("0xbee3704b", "0x00000000", 13, "bit-13_mbee3704b (#5)"),
        ("0x17149975", "0xffffffff", 31, "MSB cert (mediocre)"),
        ("0x189b13c7", "0x80000000", 31, "msb_m189b13c7 (BOTTOM)"),
    ]

    print("# Multi-residual compression sweep (top 5 by de58 + cert + bottom)", file=sys.stderr)
    print(f"# n_samples={args.samples}", file=sys.stderr)

    for m0_hex, fill_hex, bit, tag in candidates:
        m0 = int(m0_hex, 16)
        fill = int(fill_hex, 16)
        t0 = time.time()
        result = candidate_residuals(m0, fill, bit, args.samples)
        elapsed = time.time() - t0
        if result is None:
            print(json.dumps({"tag": tag, "error": "not cascade-eligible"}))
            continue
        counts, n_held = result
        rec = {"tag": tag, "m0": m0_hex, "bit": bit, "n_held": n_held,
               "elapsed_s": round(elapsed, 2)}
        for var in ["de57", "de58", "de59", "dh60", "dg60", "df60", "joint_de57_de58"]:
            rec[var] = report(var, counts[var])
        print(json.dumps(rec))
        sys.stdout.flush()


if __name__ == "__main__":
    main()
