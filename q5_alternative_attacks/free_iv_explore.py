#!/usr/bin/env python3
"""
free_iv_explore.py — Issue #21: Free-IV exploration prototype.

Question: does changing the IV change the structural difficulty of sr=60/sr=61?

We've assumed the standard SHA-256 IV throughout. But cryptanalytically,
the IV is just a 256-bit constant — the attack works for any IV. Free-IV
gives the attacker 256 extra bits of freedom.

Cheap test: for many random IVs, measure
1. How rare is da[56]=0 (for a fixed candidate M[0]=0x17149975, fill=0xff)
2. Total state diff HW at round 56 (when da[56]=0 candidates exist)
3. The 'hard core' size — output diffs that have no deterministic control

If different IVs give dramatically different candidate density or hard
core size, free-IV is a productive attack vector.
"""

import sys, os, time, random
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
import lib.sha256 as sha
from lib.sha256 import K, MASK, sigma0, sigma1, Sigma0, Sigma1, Ch, Maj, hw, add


def precompute_state_with_iv(M, IV):
    """Run 57 rounds of SHA-256 compression on message M with given IV."""
    W = list(M) + [0] * 41
    for i in range(16, 57):
        W[i] = add(sigma1(W[i-2]), W[i-7], sigma0(W[i-15]), W[i-16])

    a, b, c, d, e, f, g, h = IV
    for i in range(57):
        T1 = add(h, Sigma1(e), Ch(e, f, g), K[i], W[i])
        T2 = add(Sigma0(a), Maj(a, b, c))
        h, g, f, e, d, c, b, a = g, f, e, add(d, T1), c, b, a, add(T1, T2)

    return (a, b, c, d, e, f, g, h), W


def test_iv(IV, m0=0x17149975, fill=0xFFFFFFFF):
    """Test a single IV: does the candidate still have da[56]=0?
    Returns (has_da56_zero, total_state_diff_HW)."""
    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000

    s1, _ = precompute_state_with_iv(M1, IV)
    s2, _ = precompute_state_with_iv(M2, IV)

    if s1[0] == s2[0]:
        total_hw = sum(hw(s1[r] ^ s2[r]) for r in range(8))
        return True, total_hw
    return False, sum(hw(s1[r] ^ s2[r]) for r in range(8))


def scan_random_ivs(n_ivs=1000, m0=0x17149975, fill=0xFFFFFFFF):
    """For random IVs, measure da56 hit rate and HW distribution."""
    print(f"Scanning {n_ivs} random IVs for candidate M[0]=0x{m0:08x}, fill=0x{fill:08x}")
    print()

    rng = random.Random(42)
    da56_hits = 0
    hw_values = []
    da56_iv_examples = []

    for trial in range(n_ivs):
        IV = [rng.randint(0, MASK) for _ in range(8)]
        ok, hw_total = test_iv(IV, m0, fill)
        hw_values.append(hw_total)
        if ok:
            da56_hits += 1
            if len(da56_iv_examples) < 5:
                da56_iv_examples.append((IV, hw_total))

    print(f"da[56]=0 hit rate: {da56_hits}/{n_ivs} ({100*da56_hits/n_ivs:.2f}%)")
    print(f"Expected (random): 1/2^32 = {100*2**-32:.10f}%")
    print()

    if da56_hits > 0:
        print(f"Example da[56]=0 hits:")
        for iv, h in da56_iv_examples:
            iv_hex = ' '.join(f'{w:08x}' for w in iv)
            print(f"  IV={iv_hex} -> hw56={h}")
        print()

    print(f"State HW distribution at round 56:")
    print(f"  mean: {np.mean(hw_values):.1f}")
    print(f"  stdev: {np.std(hw_values):.1f}")
    print(f"  min: {min(hw_values)}")
    print(f"  max: {max(hw_values)}")
    print(f"  Default IV would give: ~104")


def find_low_hw_iv(n_ivs=10000, m0=0x17149975, fill=0xFFFFFFFF):
    """Search for IVs where the state diff HW at round 56 is unusually small."""
    print(f"\nSearching for low-HW IVs ({n_ivs} samples)")

    rng = random.Random(99)
    best_hw = 256
    best_iv = None
    best_da56 = False

    for trial in range(n_ivs):
        IV = [rng.randint(0, MASK) for _ in range(8)]
        ok, hw_total = test_iv(IV, m0, fill)
        if hw_total < best_hw:
            best_hw = hw_total
            best_iv = IV
            best_da56 = ok
            iv_hex = ' '.join(f'{w:08x}' for w in IV)
            print(f"  [{trial}] NEW BEST: HW={hw_total} da56={ok} IV={iv_hex}")

    print()
    print(f"Best IV: HW={best_hw}, da56={best_da56}")
    return best_iv, best_hw


def test_specific_iv_constraint():
    """Test: what if we ONLY require da56=0 (drop other 7 register constraints)?
    Then for any IV, we can compute what M[0] gives da56=0.
    Question: does da56=0 happen more often than 1/2^32?"""
    print("\nTesting: for fixed default IV, scan M[0] for da56=0")
    fill = 0xFFFFFFFF
    n_scan = 1000000
    hits = 0
    for m0 in range(n_scan):
        ok, _ = test_iv(list(sha.IV), m0, fill)
        if ok:
            hits += 1
    print(f"  Default IV: {hits}/{n_scan} = {100*hits/n_scan:.4f}% hit rate")
    print(f"  Expected if uniform: 1/2^32 = {100/2**32*1000000:.4f}% per million")


def main():
    n_ivs = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    print("=" * 60)
    print("Free-IV Exploration (Issue #21)")
    print("=" * 60)
    print()

    scan_random_ivs(n_ivs)
    find_low_hw_iv(n_ivs * 10)


if __name__ == "__main__":
    main()
