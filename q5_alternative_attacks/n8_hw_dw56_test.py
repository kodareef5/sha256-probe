#!/usr/bin/env python3
"""
n8_hw_dw56_test.py — Enumerate all N=8 da[56]=0 candidates and their hw_dW56_mini.

At N=8 there are only 256 m0 values × small number of fills, so we can
enumerate all da[56]=0 candidates and characterize the distribution of
hw_dW56_mini for each fill.

If the hw_dW56 hypothesis holds at N=8, candidates with low hw_dW56_mini
should solve sr=60 faster.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
import importlib.util
spec = importlib.util.spec_from_file_location('precision', '/root/sha256_probe/50_precision_homotopy.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
MiniSHA256 = mod.MiniSHA256


def enumerate_candidates(N=8):
    """Enumerate all (m0, fill) with da[56]=0 at given N."""
    sha = MiniSHA256(N)
    MASK = sha.MASK
    MSB = sha.MSB
    K = sha.K
    IV = sha.IV

    rS0 = sha.r_Sig0
    rS1 = sha.r_Sig1
    rs0 = sha.r_sig0
    ss0 = sha.s_sig0
    rs1 = sha.r_sig1
    ss1 = sha.s_sig1

    def step_full(m0, fill):
        """Compute state after 57 rounds and W[0..56] for both messages."""
        M1 = [m0] + [fill] * 15
        M2 = [m0 ^ MSB] + [fill] * 15
        M2[9] ^= MSB
        # Schedule
        W1 = list(M1) + [0] * 48
        W2 = list(M2) + [0] * 48
        for i in range(16, 57):
            for W in [W1, W2]:
                x = W[i-2]
                s1v = (((x >> rs1[0]) | (x << (N - rs1[0]))) & MASK) ^ \
                      (((x >> rs1[1]) | (x << (N - rs1[1]))) & MASK) ^ \
                      ((x >> ss1) & MASK)
                y = W[i-15]
                s0v = (((y >> rs0[0]) | (y << (N - rs0[0]))) & MASK) ^ \
                      (((y >> rs0[1]) | (y << (N - rs0[1]))) & MASK) ^ \
                      ((y >> ss0) & MASK)
                W[i] = (s1v + W[i-7] + s0v + W[i-16]) & MASK
        # Compression
        states = []
        for W, M in [(W1, M1), (W2, M2)]:
            a, b, c, d, e, f, g, h = IV
            for i in range(57):
                T1v = (((e >> rS1[0]) | (e << (N - rS1[0]))) & MASK) ^ \
                      (((e >> rS1[1]) | (e << (N - rS1[1]))) & MASK) ^ \
                      (((e >> rS1[2]) | (e << (N - rS1[2]))) & MASK)
                Chv = ((e & f) ^ ((~e & MASK) & g)) & MASK
                T1 = (h + T1v + Chv + K[i] + W[i]) & MASK
                T2v = (((a >> rS0[0]) | (a << (N - rS0[0]))) & MASK) ^ \
                      (((a >> rS0[1]) | (a << (N - rS0[1]))) & MASK) ^ \
                      (((a >> rS0[2]) | (a << (N - rS0[2]))) & MASK)
                Mjv = ((a & b) ^ (a & c) ^ (b & c)) & MASK
                T2 = (T2v + Mjv) & MASK
                h, g, f, e, d, c, b, a = g, f, e, (d + T1) & MASK, c, b, a, (T1 + T2) & MASK
            states.append((a, b, c, d, e, f, g, h))
        return states[0], states[1], W1, W2

    def hw(x):
        return bin(x & MASK).count('1')

    cands = []
    for fill in range(1 << N):
        for m0 in range(1 << N):
            s1, s2, W1, W2 = step_full(m0, fill)
            if s1[0] == s2[0]:  # da[56] = 0
                hw_dw56 = hw(W1[56] ^ W2[56])
                cands.append({
                    'm0': m0, 'fill': fill,
                    'hw_dw56': hw_dw56,
                    'da56': 0,
                    'state_diffs': sum(1 for r in range(8) if s1[r] != s2[r]),
                })
    return cands


def main():
    print("Enumerating N=8 da[56]=0 candidates...")
    cands = enumerate_candidates(N=8)
    print(f"Found {len(cands)} da[56]=0 candidates")

    if not cands:
        return

    # Sort by hw_dw56
    cands.sort(key=lambda c: c['hw_dw56'])

    print(f"\n{'rank':<5} {'m0':<6} {'fill':<6} {'hw_dW56':<8} {'state_diffs':<11}")
    for i, c in enumerate(cands[:30]):
        print(f"{i+1:<5} 0x{c['m0']:02x}   0x{c['fill']:02x}   {c['hw_dw56']:<8} {c['state_diffs']:<11}")
    if len(cands) > 30:
        print(f"... ({len(cands) - 30} more)")
        print(f"\nLast 5 (highest hw):")
        for i, c in enumerate(cands[-5:]):
            print(f"  0x{c['m0']:02x}   0x{c['fill']:02x}   {c['hw_dw56']:<8}")

    # Distribution
    from collections import Counter
    hist = Counter(c['hw_dw56'] for c in cands)
    print(f"\nDistribution of hw_dW56_mini at N=8:")
    for k in sorted(hist):
        bar = '#' * hist[k]
        print(f"  hw={k}: {hist[k]:4d} {bar}")

    print(f"\nMin hw_dW56_mini: {min(c['hw_dw56'] for c in cands)}")
    print(f"Max hw_dW56_mini: {max(c['hw_dw56'] for c in cands)}")


if __name__ == "__main__":
    main()
