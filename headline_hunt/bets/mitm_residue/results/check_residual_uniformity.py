#!/usr/bin/env python3
"""
After R63.1 (dc_63 = dg_63) and R63.3 (da_63 - de_63 = dT2_63) reduce the
6-active-register residual to 4 modular d.o.f., the natural question:
are those 4 d.o.f. uniformly distributed under random cascade-held W?

Pick the 4 d.o.f. as: (da_63, db_63, dc_63, df_63). Then:
  - de_63 = da_63 - dT2_63 (R63.3) — determined by da_63 + actual a-values
  - dg_63 = dc_63 (R63.1) — determined by dc_63

Empirical test: build the joint distribution of (da_63, db_63, dc_63, df_63)
over a large fresh-sample set, check uniformity in each marginal and check
pairwise correlations. Non-uniformity or strong correlation = hidden structure.
"""
import argparse
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
from validate_residual_structure import run_one
from lib.sha256 import precompute_state, MASK


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m0", default="0x17149975")
    ap.add_argument("--fill", default="0xffffffff")
    ap.add_argument("--kernel-bit", type=int, default=31)
    ap.add_argument("--samples", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    m0 = int(args.m0, 16)
    fill = int(args.fill, 16)
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= (1 << args.kernel_bit)
    M2[9] ^= (1 << args.kernel_bit)
    s1_init, W1_pre = precompute_state(M1)
    s2_init, W2_pre = precompute_state(M2)

    rng = random.Random(args.seed)
    da_list, db_list, dc_list, df_list = [], [], [], []

    for _ in range(args.samples):
        w1_57 = rng.randrange(2**32)
        w1_58 = rng.randrange(2**32)
        w1_59 = rng.randrange(2**32)
        w1_60 = rng.randrange(2**32)
        result = run_one(s1_init, s2_init, W1_pre, W2_pre, w1_57, w1_58, w1_59, w1_60)
        if result is None:
            continue
        states1, states2 = result
        s1_63, s2_63 = states1[3], states2[3]
        da_63 = (s1_63[0] - s2_63[0]) & MASK
        db_63 = (s1_63[1] - s2_63[1]) & MASK
        dc_63 = (s1_63[2] - s2_63[2]) & MASK
        df_63 = (s1_63[5] - s2_63[5]) & MASK
        da_list.append(da_63); db_list.append(db_63); dc_list.append(dc_63); df_list.append(df_63)

    n = len(da_list)
    print(f"cascade-held samples: {n}")

    # Marginal uniformity check via lower-byte distribution (should be ~uniform 0..255)
    def lo_byte_chi2(xs):
        bins = [0] * 256
        for x in xs:
            bins[x & 0xff] += 1
        expected = n / 256
        chi2 = sum((b - expected) ** 2 / expected for b in bins)
        # df=255 chi2 critical value at p=0.001 ≈ 330; normal ≈ 255
        return chi2

    print()
    print("Lower-byte chi-squared (~255 expected for uniform; >330 suggests non-uniform):")
    for name, xs in [("da_63", da_list), ("db_63", db_list), ("dc_63", dc_list), ("df_63", df_list)]:
        chi2 = lo_byte_chi2(xs)
        verdict = "uniform-ish" if chi2 < 330 else "NON-UNIFORM"
        print(f"  {name}: chi2={chi2:.1f}  {verdict}")

    # Bit-bias check: each bit of each var should be ~50% set
    print()
    print("Bit-bias (each bit, fraction set; 50% expected):")
    for name, xs in [("da_63", da_list), ("db_63", db_list), ("dc_63", dc_list), ("df_63", df_list)]:
        biases = []
        for bit in range(32):
            count = sum(1 for x in xs if (x >> bit) & 1)
            biases.append(count / n)
        max_dev = max(abs(b - 0.5) for b in biases)
        max_bit = biases.index(max(biases, key=lambda b: abs(b - 0.5)))
        print(f"  {name}: max deviation {max_dev:.4f} at bit {max_bit}")

    # Pairwise correlation: count how often LSB of pair-(x,y) are equal
    print()
    print("LSB-equality between pairs (should be ~50% for independent):")
    pairs = [
        ("da_63", da_list, "db_63", db_list),
        ("da_63", da_list, "dc_63", dc_list),
        ("da_63", da_list, "df_63", df_list),
        ("db_63", db_list, "dc_63", dc_list),
        ("db_63", db_list, "df_63", df_list),
        ("dc_63", dc_list, "df_63", df_list),
    ]
    for n1, xs1, n2, xs2 in pairs:
        count = sum(1 for a, b in zip(xs1, xs2) if (a & 1) == (b & 1))
        print(f"  ({n1}, {n2}) LSB-eq: {count}/{n} ({count/n*100:.2f}%)")


if __name__ == "__main__":
    main()
