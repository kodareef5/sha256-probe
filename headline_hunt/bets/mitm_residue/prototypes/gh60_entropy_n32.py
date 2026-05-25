#!/usr/bin/env python3
"""Decisive test of the ~24-bit gh60 residue claim at N=32 via distinct-value count.

gh60 = (g60_diff, h60_diff) = (e58_diff, e57_diff) is the bet's hard-residue key.
Sweep random (W1[57],W1[58]) pairs (message-2 via cascade da=0 at 57,58), compute
the 64-bit gh60 difference, and count DISTINCT values vs samples. Distinct count is
a LOWER bound on effective residue dimension (unlike active-bit count):
  - if distinct saturates near 2^24 -> CONFIRMS ~24 effective bits;
  - if distinct ~ samples with no ceiling past 2^22 -> REFUTES <=~22-bit gh60.

Reuses lib.sha256. Usage: gh60_entropy_n32.py [n_samples] [seed]
"""
import os
import sys
import time
import random

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.insert(0, REPO)
from lib.sha256 import (  # noqa: E402
    MASK, K, Sigma0, Sigma1, Ch, Maj, add, precompute_state,
)

M0 = 0x17149975
FILL = 0xFFFFFFFF


def one_round(s, w, r):
    a, b, c, d, e, f, g, h = s
    T1 = add(h, Sigma1(e), Ch(e, f, g), K[r], w)
    T2 = add(Sigma0(a), Maj(a, b, c))
    return (add(T1, T2), a, b, c, add(d, T1), e, f, g)


def w2_for_zero_a(s1, s2, r, w1):
    base1 = add(s1[7], Sigma1(s1[4]), Ch(s1[4], s1[5], s1[6]))
    base2 = add(s2[7], Sigma1(s2[4]), Ch(s2[4], s2[5], s2[6]))
    T21 = add(Sigma0(s1[0]), Maj(s1[0], s1[1], s1[2]))
    T22 = add(Sigma0(s2[0]), Maj(s2[0], s2[1], s2[2]))
    return (w1 + base1 - base2 + T21 - T22) & MASK


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else (1 << 22)
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 42

    M1 = [M0] + [FILL] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1_init, _ = precompute_state(M1)
    s2_init, _ = precompute_state(M2)

    rng = random.Random(seed)
    seen = set()
    checkpoints = [1 << k for k in range(10, 26) if (1 << k) <= n]
    t0 = time.time()

    for i in range(1, n + 1):
        w1_57 = rng.getrandbits(32)
        w1_58 = rng.getrandbits(32)
        w2_57 = w2_for_zero_a(s1_init, s2_init, 57, w1_57)
        s1 = one_round(s1_init, w1_57, 57)
        s2 = one_round(s2_init, w2_57, 57)
        e57d = (s1[4] ^ s2[4]) & MASK            # h60 = e57
        w2_58 = w2_for_zero_a(s1, s2, 58, w1_58)
        s1b = one_round(s1, w1_58, 58)
        s2b = one_round(s2, w2_58, 58)
        e58d = (s1b[4] ^ s2b[4]) & MASK          # g60 = e58
        seen.add((e58d << 32) | e57d)
        if i in checkpoints:
            print(f"  samples={i:>10}  distinct_gh60={len(seen):>10}  "
                  f"ratio={len(seen)/i:.4f}  log2(distinct)={(len(seen)).bit_length()-1}")

    dt = time.time() - t0
    print(f"N=32 gh60 entropy: n={n} seed={seed} distinct={len(seen)} "
          f"({n/dt:.0f}/s) ratio={len(seen)/n:.4f}")
    print(f"VERDICT: log2(distinct) ~= {(len(seen)).bit_length()-1}; "
          f"{'SATURATING (residue ceiling visible)' if len(seen) < 0.9*n else 'NO ceiling (distinct ~ samples)'}")


if __name__ == "__main__":
    main()
