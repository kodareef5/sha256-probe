#!/usr/bin/env python3
"""n10_hardlock.py — Hardlock pattern at N=10 for the discovered MSB candidate.

Today's de58 family finding (at N=32) was: each candidate has bits of de58
that NEVER vary across W57 (hardlocked). This script asks whether the same
pattern emerges at N=10 — empirical generalizability check, complement to
n10_invariants.py.
"""
import random
from n10_invariants import (
    N, MASK, find_cascade_eligible_m0, precompute_state, apply_round,
    cascade1_offset, cascade2_offset,
)


def main():
    m0 = find_cascade_eligible_m0()
    fill = MASK
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= 1 << (N - 1)
    M2[9] ^= 1 << (N - 1)
    s1, _ = precompute_state(M1)
    s2, _ = precompute_state(M2)
    cw57 = cascade1_offset(s1, s2)

    rng = random.Random(42)
    de58_image = set()
    n_kept = 0
    n_samples = 1 << 14
    for _ in range(n_samples):
        w57 = rng.randrange(MASK + 1)
        w2_57 = (w57 + cw57) & MASK
        s1_57 = apply_round(s1, w57, 57)
        s2_57 = apply_round(s2, w2_57, 57)
        if (s1_57[0] - s2_57[0]) & MASK != 0:
            continue
        cw58 = cascade1_offset(s1_57, s2_57)
        s1_58 = apply_round(s1_57, 0, 58)
        s2_58 = apply_round(s2_57, cw58, 58)
        d58 = (s1_58[4] - s2_58[4]) & MASK
        de58_image.add(d58)
        n_kept += 1

    or_all = 0
    and_all = MASK
    for v in de58_image:
        or_all |= v
        and_all &= v
    locked_mask = (~(or_all ^ and_all)) & MASK
    locked_value = and_all & locked_mask
    n_locked = bin(locked_mask).count("1")

    print(f"N={N}, MSB-kernel auto-discovered M0=0x{m0:x}, fill=0x{fill:x}")
    print(f"Samples kept: {n_kept}/{n_samples}")
    print(f"de58 image size: {len(de58_image)}")
    print(f"Hardlock mask:   0b{locked_mask:0{N}b} = 0x{locked_mask:x}")
    print(f"Hardlock value:  0b{locked_value:0{N}b} = 0x{locked_value:x}")
    print(f"Bits locked:     {n_locked}/{N} ({n_locked*100//N}%)")
    print(f"Bits varying:    {N - n_locked}")

    if n_locked > 0:
        print("\nN=10 hardlock pattern CONFIRMED — de58 has hardlocked bits at N=10")
        print("just like at N=32. The structural picture is N-invariant.")
    else:
        print("\nN=10: NO hardlock — every de58 bit varies. Structurally different from N=32.")


if __name__ == "__main__":
    main()
