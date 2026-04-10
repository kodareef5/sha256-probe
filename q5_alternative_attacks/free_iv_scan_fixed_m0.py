#!/usr/bin/env python3
"""
free_iv_scan_fixed_m0.py — Search for IVs that give LOW state HW with the
fixed candidate M[0]=0x17149975, fill=0xff, regardless of da[56]=0.

Even if da[56]!=0, low state HW means a smaller hard core. Combined
with adjusted W[57..60], we might still find a collision.
"""

import sys, os, time, random
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
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
    m0 = 0x17149975
    fill = 0xFFFFFFFF

    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000

    rng = random.Random(42)
    best_hw = 256
    best_iv = None
    best_da56 = False
    da56_zero_iv = None
    da56_zero_hw = 256

    t0 = time.time()
    distribution = []

    for trial in range(n):
        IV = [rng.randint(0, MASK) for _ in range(8)]
        s1 = precompute_state(M1, IV)
        s2 = precompute_state(M2, IV)
        diff = [s1[r] ^ s2[r] for r in range(8)]
        total = sum(hw(d) for d in diff)
        distribution.append(total)

        if total < best_hw:
            best_hw = total
            best_iv = IV[:]
            best_da56 = (diff[0] == 0)
            print(f"  [{trial:>7}] HW={total} da56={'Y' if diff[0]==0 else 'N'}({hw(diff[0])})", flush=True)

        if diff[0] == 0 and total < da56_zero_hw:
            da56_zero_hw = total
            da56_zero_iv = IV[:]
            print(f"  [{trial:>7}] DA56=0 HW={total}", flush=True)

    elapsed = time.time() - t0
    print(f"\n{n:,} IVs in {elapsed:.0f}s ({n/elapsed:.0f}/s)")
    import statistics
    print(f"Distribution: mean={statistics.mean(distribution):.1f}, "
          f"min={min(distribution)}, max={max(distribution)}, "
          f"stdev={statistics.stdev(distribution):.1f}")
    print(f"Best overall HW: {best_hw} (vs default 104)")
    if best_iv:
        print(f"Best IV: {' '.join(f'{w:08x}' for w in best_iv)}")
        print(f"Best had da56=0: {best_da56}")
    if da56_zero_iv:
        print(f"\nBest da56=0 IV (HW={da56_zero_hw}):")
        print(f"  {' '.join(f'{w:08x}' for w in da56_zero_iv)}")


if __name__ == "__main__":
    main()
