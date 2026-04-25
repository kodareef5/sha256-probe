#!/usr/bin/env python3
"""de58_hardlock_bits.py — Per-bit hard-locked positions in de58 across candidates.

For each candidate, sample W57 → de58. The set of de58 values has a per-bit
structure: some bits NEVER vary (hard-locked) and some vary across the image.

Hard-locked bits are concrete predictions: those bits of de58 are determined
entirely by the candidate, irrespective of W57. They can never be changed by
choosing a different W57.

For sr=61 SAT search: any solution's de58 value must match the hard-locked
pattern of its candidate. This gives a per-candidate de58 "signature" that
SAT branches must satisfy.

Output: per-candidate (locked_mask, locked_value) pair. Together they say:
  for any sample W57:  de58 & locked_mask == locked_value
  the (32 − HW(locked_mask)) varying bits parametrize the image.

Usage: python3 headline_hunt/bets/sr61_n32/de58_hardlock_bits.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
sys.path.insert(0, HERE)
from de58_disjoint_check import candidate_de58_image
import yaml


def hardlock_summary(image):
    or_all = 0
    and_all = 0xFFFFFFFF
    for v in image:
        or_all |= v
        and_all &= v
    locked_mask = (~(or_all ^ and_all)) & 0xFFFFFFFF
    locked_value = and_all & locked_mask
    return locked_mask, locked_value


def main():
    cands_path = os.path.join(REPO, "headline_hunt/registry/candidates.yaml")
    with open(cands_path) as f:
        cands = yaml.safe_load(f)

    print(f"{'Candidate':45s} {'|im|':>8} {'locked':>7} {'varying':>8} locked_mask    locked_val")
    print("-" * 110)
    rows = []
    for c in cands:
        m0 = int(c['m0'], 16)
        fill = int(c['fill'], 16)
        bit = c['kernel']['bit']
        img = candidate_de58_image(m0, fill, bit, n_samples=1 << 17)
        if img is None:
            continue
        mask, val = hardlock_summary(img)
        n_locked = bin(mask).count('1')
        rows.append((c['id'], len(img), n_locked, mask, val))
        print(f"  {c['id'][:43]:43s} {len(img):>8} {n_locked:>7} {32-n_locked:>8} "
              f"{mask:#010x}    {val:#010x}")

    print()
    print(f"Most-locked top 10:")
    for cid, n, nl, mask, val in sorted(rows, key=lambda r: -r[2])[:10]:
        print(f"  locked={nl}/{32-nl} varying  image={n:>6}  {cid}")


if __name__ == "__main__":
    main()
