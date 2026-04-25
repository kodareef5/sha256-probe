#!/usr/bin/env python3
"""n_invariants_cross_candidate.py — Test cascade structural invariants across
ALL cascade-eligible candidates at a fixed N, in addition to the original
single-candidate-per-N probe in n_invariants.py.

Validates: are Theorem 4 + R63.1 + R63.3 universal across CANDIDATES (different
M0 / fill choices) as well as across N values? At N=10 we have 10 cascade-eligible
candidates spanning 6 fill choices.

Usage: python3 n_invariants_cross_candidate.py [N]   (default N=10)
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
from n_invariants import make_helpers


def main():
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    h = make_helpers(N)
    MASK = h['MASK']
    pre = h['precompute_state']
    apply_round = h['apply_round']
    cw1, cw2 = h['cw1'], h['cw2']
    sigma0, sigma1 = h['sigma0'], h['sigma1']
    Sigma0, Maj = h['Sigma0'], h['Maj']
    add = h['add']

    fills_to_try = [MASK, 0, MASK ^ (MASK >> 1), MASK >> 1, 1 << (N - 1), MASK ^ (1 << (N - 1))]
    eligible = []
    for fill in fills_to_try:
        for cand in range(MASK + 1):
            M1 = [cand] + [fill] * 15
            M2 = list(M1); M2[0] ^= 1 << (N - 1); M2[9] ^= 1 << (N - 1)
            s1, _ = pre(M1); s2, _ = pre(M2)
            if s1[0] == s2[0]:
                eligible.append((cand, fill))

    print(f'N={N}, MASK=0x{MASK:x}, eligible candidates: {len(eligible)}')
    print(f'{"M0":>5}  {"fill":>5}  {"|im|":>5}  {"locked":>6}  Th4    R63.1  R63.3')

    n_samples = 4096
    all_pass = True
    for m0, fill in eligible:
        M1 = [m0] + [fill] * 15
        M2 = list(M1); M2[0] ^= 1 << (N - 1); M2[9] ^= 1 << (N - 1)
        s1, W1pre = pre(M1); s2, W2pre = pre(M2)
        cw57 = cw1(s1, s2)
        rng = random.Random(42)
        th4_v = r631_v = r633_v = 0
        image = set(); n_kept = 0
        for _ in range(n_samples):
            w57 = rng.randrange(MASK + 1)
            w2_57 = (w57 + cw57) & MASK
            s1_57 = apply_round(s1, w57, 57); s2_57 = apply_round(s2, w2_57, 57)
            if (s1_57[0] - s2_57[0]) & MASK != 0: continue
            cw58_v = cw1(s1_57, s2_57)
            s1_58 = apply_round(s1_57, 0, 58); s2_58 = apply_round(s2_57, cw58_v, 58)
            d58 = (s1_58[4] - s2_58[4]) & MASK
            image.add(d58)
            cw59_v = cw1(s1_58, s2_58)
            s1_59 = apply_round(s1_58, 0, 59); s2_59 = apply_round(s2_58, cw59_v, 59)
            cw60_v = cw2(s1_59, s2_59)
            s1_60 = apply_round(s1_59, 0, 60); s2_60 = apply_round(s2_59, cw60_v, 60)
            W1 = list(W1pre) + [w57, 0, 0, 0]
            W2 = list(W2pre) + [w2_57, cw58_v, cw59_v, cw60_v]
            for r in (61, 62, 63):
                W1.append(add(sigma1(W1[r-2]), W1[r-7], sigma0(W1[r-15]), W1[r-16]))
                W2.append(add(sigma1(W2[r-2]), W2[r-7], sigma0(W2[r-15]), W2[r-16]))
            s1_61 = apply_round(s1_60, W1[61], 61); s2_61 = apply_round(s2_60, W2[61], 61)
            s1_62 = apply_round(s1_61, W1[62], 62); s2_62 = apply_round(s2_61, W2[62], 62)
            s1_63 = apply_round(s1_62, W1[63], 63); s2_63 = apply_round(s2_62, W2[63], 63)
            if ((s1_61[0]-s2_61[0]) & MASK) != ((s1_61[4]-s2_61[4]) & MASK):
                th4_v += 1
            if ((s1_63[2]-s2_63[2]) & MASK) != ((s1_63[6]-s2_63[6]) & MASK):
                r631_v += 1
            dSig0 = (Sigma0(s1_62[0]) - Sigma0(s2_62[0])) & MASK
            dMaj = (Maj(s1_62[0], s1_62[1], s1_62[2]) - Maj(s2_62[0], s2_62[1], s2_62[2])) & MASK
            dT2 = (dSig0 + dMaj) & MASK
            if ((s1_63[0]-s2_63[0]-(s1_63[4]-s2_63[4])) & MASK) != dT2:
                r633_v += 1
            n_kept += 1
        or_all = 0; and_all = MASK
        for v in image: or_all |= v; and_all &= v
        locked = bin((~(or_all ^ and_all)) & MASK).count('1')
        th4_pct = (n_kept - th4_v) / n_kept * 100 if n_kept else 0
        r631_pct = (n_kept - r631_v) / n_kept * 100 if n_kept else 0
        r633_pct = (n_kept - r633_v) / n_kept * 100 if n_kept else 0
        print(f'  0x{m0:0{(N+3)//4}x}  0x{fill:0{(N+3)//4}x}  {len(image):>5}  {locked:>3}/{N}  '
              f'{th4_pct:5.1f}  {r631_pct:5.1f}  {r633_pct:5.1f}')
        if th4_v or r631_v or r633_v: all_pass = False

    print()
    if all_pass:
        print(f'All {len(eligible)} candidates at N={N} pass Theorem 4 + R63.1 + R63.3 '
              f'at {n_samples} samples each.')
        print('EVIDENCE that invariants are universal across BOTH N AND candidates.')
    else:
        print(f'VIOLATIONS at N={N}. Cascade invariants NOT universal.')


if __name__ == "__main__":
    main()
