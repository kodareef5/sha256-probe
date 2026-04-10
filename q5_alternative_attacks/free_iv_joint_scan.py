#!/usr/bin/env python3
"""
free_iv_joint_scan.py — Joint (IV, M[0]) scan for free-IV sr=60.

Free IV gives 256 extra bits of freedom. The question: are there
(IV, M[0]) combinations where da[56]=0 AND the total state HW at
round 56 is much smaller than the default IV's HW=104?

If we find an IV that gives HW < 80 with da[56]=0, that's a
candidate where:
- The hard core (132 random bits) becomes smaller
- The cascade has fewer bits to zero
- sr=61 might become tractable

Approach: for each random IV, scan ~1000 M[0] values for da[56]=0.
Record any hits with their HW. Look for unusually low HW.
"""

import sys, os, time, random
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import K, MASK, sigma0, sigma1, Sigma0, Sigma1, Ch, Maj, hw, add


def precompute_state(M, IV):
    W = list(M) + [0] * 41
    for i in range(16, 57):
        W[i] = add(sigma1(W[i-2]), W[i-7], sigma0(W[i-15]), W[i-16])
    a, b, c, d, e, f, g, h = IV
    for i in range(57):
        T1 = add(h, Sigma1(e), Ch(e, f, g), K[i], W[i])
        T2 = add(Sigma0(a), Maj(a, b, c))
        h, g, f, e, d, c, b, a = g, f, e, add(d, T1), c, b, a, add(T1, T2)
    return (a, b, c, d, e, f, g, h)


def main():
    n_ivs = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    n_m0_per_iv = int(sys.argv[2]) if len(sys.argv) > 2 else 100000
    fill = 0xFFFFFFFF

    print(f"Joint (IV, M[0]) scan for free-IV sr=60")
    print(f"IVs: {n_ivs}, M[0] per IV: {n_m0_per_iv:,}")
    print(f"Total enumeration: {n_ivs * n_m0_per_iv:,} (M[0], IV) pairs")
    print()

    rng = random.Random(42)
    best_hw = 256
    best_combo = None
    da56_hits = []

    t0 = time.time()
    total_evaluated = 0

    for iv_idx in range(n_ivs):
        IV = [rng.randint(0, MASK) for _ in range(8)]
        iv_hits_for_this = 0
        iv_min_hw = 256

        for m0 in range(n_m0_per_iv):
            M1 = [m0] + [fill] * 15
            M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
            s1 = precompute_state(M1, IV)
            s2 = precompute_state(M2, IV)
            total_evaluated += 1

            if s1[0] == s2[0]:
                hw_total = sum(hw(s1[r] ^ s2[r]) for r in range(8))
                da56_hits.append((IV, m0, hw_total))
                iv_hits_for_this += 1
                if hw_total < iv_min_hw:
                    iv_min_hw = hw_total
                if hw_total < best_hw:
                    best_hw = hw_total
                    best_combo = (list(IV), m0, hw_total)
                    iv_hex = ' '.join(f'{w:08x}' for w in IV)
                    print(f"  [iv {iv_idx}, m0 0x{m0:08x}] NEW BEST HW={hw_total}", flush=True)
                    print(f"    IV: {iv_hex}", flush=True)

        if iv_idx % 10 == 9:
            elapsed = time.time() - t0
            rate = total_evaluated / elapsed
            print(f"  iv {iv_idx+1}/{n_ivs}: {iv_hits_for_this} hits, "
                  f"min HW {iv_min_hw}, {rate:.0f}/s", flush=True)

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.0f}s ({total_evaluated/elapsed:.0f}/s)")
    print(f"Total da[56]=0 hits: {len(da56_hits)}")
    print(f"Hit rate: {len(da56_hits)/total_evaluated * 100:.6f}% (expected ~{100/2**32*total_evaluated/total_evaluated*total_evaluated:.4f}%)")
    print()

    if da56_hits:
        hws = [h[2] for h in da56_hits]
        print(f"HW distribution of hits:")
        print(f"  min: {min(hws)}")
        print(f"  mean: {np.mean(hws):.1f}")
        print(f"  max: {max(hws)}")
        print()
        print(f"Default IV gives HW=104 for the published candidate.")
        print(f"Best free-IV HW: {min(hws)}")
        if min(hws) < 80:
            print(f"\n*** SIGNIFICANT: free-IV gives {104 - min(hws)} bit improvement ***")
            print(f"Best (IV, M[0]):")
            best = min(da56_hits, key=lambda x: x[2])
            iv_hex = ' '.join(f'{w:08x}' for w in best[0])
            print(f"  IV = {iv_hex}")
            print(f"  M[0] = 0x{best[1]:08x}")
            print(f"  HW = {best[2]}")


if __name__ == "__main__":
    main()
