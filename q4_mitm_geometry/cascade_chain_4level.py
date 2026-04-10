#!/usr/bin/env python3
"""
cascade_chain_4level.py — 4-level cascade chain extension at N=32.

Extends macbook's 2-level cascade chain (dW[57], dW[58]) to 4 levels
(dW[57], dW[58], dW[59], dW[60]).

Each level: for the given (W1[57..k]), compute the unique dW[k+1] that
maintains da[k+1]=0 (cascade-1 propagation).

This reduces the search from 2^256 to 2^128 at N=32 — still hard but
half the exponent, and AT EACH LEVEL we get a verified cascade state.

The remaining freedom (4 free W1 words = 128 bits) needs to additionally
satisfy de63=0 (cascade-2 endpoint) and the resulting cascade-2 propagation.

Tested initially at N=4 (verified) and N=8.
"""

import sys, os, time, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import K, MASK, sigma0, sigma1, Sigma0, Sigma1, Ch, Maj, hw, add, IV, precompute_state


def cascade_dw(s1, s2):
    """Compute the dW value that gives da=0 at the next round."""
    dh = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    T2_1 = (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & MASK
    T2_2 = (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & MASK
    dT2 = (T2_1 - T2_2) & MASK
    return (dh + dSig1 + dCh + dT2) & MASK


def one_round(s, w, i):
    T1 = add(s[7], Sigma1(s[4]), Ch(s[4], s[5], s[6]), K[i], w)
    T2 = add(Sigma0(s[0]), Maj(s[0], s[1], s[2]))
    return (add(T1, T2), s[0], s[1], s[2], add(s[3], T1), s[4], s[5], s[6])


def cascade_chain_at_n32(m0=0x17149975, fill=0xFFFFFFFF, n_samples=1000):
    """At N=32, sample (W1[57..60]) tuples that satisfy the 4-level cascade."""
    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1, _ = precompute_state(M1)
    s2, _ = precompute_state(M2)

    # Level 1: dW[57] is constant
    C57 = cascade_dw(s1, s2)
    print(f"Level 1: dW[57] = 0x{C57:08x} (constant)")

    rng = random.Random(42)
    print(f"\nSampling {n_samples} 4-level cascade tuples at N=32:")
    print(f"{'idx':<6} {'W1_57':<10} {'C58':<10} {'C59':<10} {'C60':<10}")
    print("-" * 50)

    for trial in range(min(n_samples, 10)):
        # Random W1[57]
        w1_57 = rng.getrandbits(32)
        w2_57 = (w1_57 + C57) & MASK

        s1_57 = one_round(s1, w1_57, 57)
        s2_57 = one_round(s2, w2_57, 57)
        # Verify da57 = 0
        if s1_57[0] != s2_57[0]:
            print(f"  trial {trial}: da57 != 0 — BUG")
            continue

        C58 = cascade_dw(s1_57, s2_57)

        # Random W1[58]
        w1_58 = rng.getrandbits(32)
        w2_58 = (w1_58 + C58) & MASK
        s1_58 = one_round(s1_57, w1_58, 58)
        s2_58 = one_round(s2_57, w2_58, 58)
        if s1_58[0] != s2_58[0]:
            print(f"  trial {trial}: da58 != 0")
            continue

        C59 = cascade_dw(s1_58, s2_58)

        # Random W1[59]
        w1_59 = rng.getrandbits(32)
        w2_59 = (w1_59 + C59) & MASK
        s1_59 = one_round(s1_58, w1_59, 59)
        s2_59 = one_round(s2_58, w2_59, 59)
        if s1_59[0] != s2_59[0]:
            print(f"  trial {trial}: da59 != 0")
            continue

        C60 = cascade_dw(s1_59, s2_59)

        # Verify the cascade propagation at round 59
        d_state = [s1_59[r] ^ s2_59[r] for r in range(8)]
        # Should have da=db=dc=dd = 0 at round 59 (cascade 1 complete)
        cascade_ok = all(d_state[r] == 0 for r in range(4))

        print(f"{trial:<6} 0x{w1_57:08x} 0x{C58:08x} 0x{C59:08x} 0x{C60:08x} cascade1={cascade_ok}")

    # Now do a STATISTICAL test: how often does cascade 1 hold?
    print(f"\nStatistical test ({n_samples} random 4-level cascade tuples):")
    cascade1_ok = 0
    for trial in range(n_samples):
        w1_57 = rng.getrandbits(32); w2_57 = (w1_57 + C57) & MASK
        s1a = one_round(s1, w1_57, 57); s2a = one_round(s2, w2_57, 57)
        C58_v = cascade_dw(s1a, s2a)

        w1_58 = rng.getrandbits(32); w2_58 = (w1_58 + C58_v) & MASK
        s1b = one_round(s1a, w1_58, 58); s2b = one_round(s2a, w2_58, 58)
        C59_v = cascade_dw(s1b, s2b)

        w1_59 = rng.getrandbits(32); w2_59 = (w1_59 + C59_v) & MASK
        s1c = one_round(s1b, w1_59, 59); s2c = one_round(s2b, w2_59, 59)

        # Check cascade 1 at round 59
        if all(s1c[r] == s2c[r] for r in range(4)):
            cascade1_ok += 1

    print(f"  Cascade 1 (da=db=dc=dd=0 at round 59): {cascade1_ok}/{n_samples} ({100*cascade1_ok/n_samples:.1f}%)")
    if cascade1_ok == n_samples:
        print(f"  *** PERFECT — cascade chain is deterministic at N=32 ***")
    else:
        print(f"  *** PARTIAL — cascade depends on additional conditions ***")


if __name__ == "__main__":
    cascade_chain_at_n32()
