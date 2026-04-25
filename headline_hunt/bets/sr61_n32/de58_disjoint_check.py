#!/usr/bin/env python3
"""de58_disjoint_check.py — Pairwise disjointness analysis of de58 images across candidates.

Finding: the 36 registered candidates' de58 images are 96.7% pairwise disjoint
(only 21 of 630 pairs share any de58 values; max overlap 31 values).
The combined union covers ~0.03% of the 32-bit de58 space.

Usage: python3 headline_hunt/bets/sr61_n32/de58_disjoint_check.py
       (run from project root)
"""
import os
import random
import sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
from lib.sha256 import (K, MASK, Sigma0, Sigma1, Ch, Maj, add, precompute_state)


def cascade1_offset(s1, s2):
    dh = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    T2_1 = (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & MASK
    T2_2 = (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & MASK
    return (dh + dSig1 + dCh + T2_1 - T2_2) & MASK


def apply_round(state, w, r):
    T1 = add(state[7], Sigma1(state[4]), Ch(state[4], state[5], state[6]), K[r], w)
    T2 = add(Sigma0(state[0]), Maj(state[0], state[1], state[2]))
    a = add(T1, T2)
    e = add(state[3], T1)
    return (a, state[0], state[1], state[2], e, state[4], state[5], state[6])


def candidate_de58_image(m0, fill, kernel_bit, n_samples=1<<16, seed=42):
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= (1 << kernel_bit)
    M2[9] ^= (1 << kernel_bit)
    s1, _ = precompute_state(M1)
    s2, _ = precompute_state(M2)
    if s1[0] != s2[0]:
        return None
    cw57 = cascade1_offset(s1, s2)
    rng = random.Random(seed)
    image = set()
    for _ in range(n_samples):
        w57 = rng.randrange(1 << 32)
        w2_57 = (w57 + cw57) & MASK
        s1_57 = apply_round(s1, w57, 57)
        s2_57 = apply_round(s2, w2_57, 57)
        if (s1_57[0] - s2_57[0]) & MASK != 0:
            continue
        cw58 = cascade1_offset(s1_57, s2_57)
        s1_58 = apply_round(s1_57, 0, 58)
        s2_58 = apply_round(s2_57, cw58, 58)
        d58 = (s1_58[4] - s2_58[4]) & MASK
        image.add(d58)
    return image


def main():
    cands_path = os.path.join(REPO, "headline_hunt/registry/candidates.yaml")
    with open(cands_path) as f:
        cands = yaml.safe_load(f)

    images = []
    for c in cands:
        m0 = int(c['m0'], 16)
        fill = int(c['fill'], 16)
        bit = c['kernel']['bit']
        img = candidate_de58_image(m0, fill, bit)
        if img is None:
            continue
        images.append((c['id'], img))

    n = len(images)
    print(f"Analyzed {n} candidates.")

    overlaps = 0
    total_pairs = 0
    overlap_records = []
    for i in range(n):
        for j in range(i + 1, n):
            common = images[i][1] & images[j][1]
            total_pairs += 1
            if len(common) > 0:
                overlaps += 1
                overlap_records.append((images[i][0], images[j][0], len(common)))
    print(f"Pairwise overlaps: {overlaps}/{total_pairs} ({(total_pairs-overlaps)/total_pairs*100:.1f}% disjoint)")

    union = set()
    total_sum = 0
    for _, s in images:
        union |= s
        total_sum += len(s)
    print(f"Union size: {len(union):,}")
    print(f"Sum of sizes: {total_sum:,}")
    print(f"Overlap reduction: {total_sum - len(union):,} ({(total_sum-len(union))/total_sum*100:.4f}%)")
    print(f"Coverage of 32-bit space: {len(union)/2**32*100:.4f}%")

    if overlap_records:
        print("\nOverlapping pairs:")
        for a, b, k in sorted(overlap_records, key=lambda x: -x[2])[:10]:
            print(f"  {a[:35]:35s} ∩ {b[:35]:35s}: {k}")


if __name__ == "__main__":
    main()
