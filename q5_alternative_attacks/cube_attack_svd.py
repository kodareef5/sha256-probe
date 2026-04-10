#!/usr/bin/env python3
"""
cube_attack_svd.py — Issue #24: Cube attack with SVD-derived cube selection.

Standard cube attacks pick a cube of k input bits, sum the function over
all 2^k assignments to those bits, and check if the sum is zero (degree
< k) or random.

We have something better than random cube selection: the 35 SVD principal
directions from the 10K diff-linear correlation matrix. These directions
are 'maximally informative' — they capture the dominant correlations
between inputs and outputs.

For each SVD direction, we threshold to get a 5-15 bit cube. We then
compute the cube sum: f(x XOR cube_indicator * y) summed over y in {0,1}^k.

If the cube sum is zero, that means the polynomial restricted to the
non-cube variables has degree < k in the cube. This gives us a linear
equation we can use for collision search.

Usage: python3 cube_attack_svd.py [n_cubes] [target_bit]
"""

import sys, os, time, random
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import K, MASK, sigma0, sigma1, Sigma0, Sigma1, Ch, Maj, hw, add, IV, precompute_state, build_schedule_tail, run_tail_rounds


def eval_collision_bit(M0, fill, w1_free, w2_free, target_reg, target_bit):
    """Evaluate one bit of the collision diff for given (W[57..60])."""
    M1 = [M0] + [fill] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1, W1_pre = precompute_state(M1)
    s2, W2_pre = precompute_state(M2)
    W1_tail = build_schedule_tail(W1_pre, w1_free)
    W2_tail = build_schedule_tail(W2_pre, w2_free)
    t1 = run_tail_rounds(s1, W1_tail)
    t2 = run_tail_rounds(s2, W2_tail)
    diff = t1[-1][target_reg] ^ t2[-1][target_reg]
    return (diff >> target_bit) & 1


def bits_to_words(bit_array):
    """Convert 256-bit array to (W1[57..60], W2[57..60])."""
    words = []
    for w_idx in range(8):
        v = 0
        for b in range(32):
            if bit_array[w_idx * 32 + b]:
                v |= 1 << (31 - b)
        words.append(v)
    return words[:4], words[4:]


def compute_cube_sum(M0, fill, base_bits, cube_indices, target_reg, target_bit):
    """Sum f over all 2^|cube_indices| assignments to the cube bits.
    Other bits are fixed at base_bits.
    Returns the sum modulo 2."""
    k = len(cube_indices)
    sum_xor = 0
    for assignment in range(2 ** k):
        bits = base_bits.copy()
        for i, idx in enumerate(cube_indices):
            bits[idx] = (assignment >> i) & 1
        w1, w2 = bits_to_words(bits)
        v = eval_collision_bit(M0, fill, w1, w2, target_reg, target_bit)
        sum_xor ^= v
    return sum_xor


def main():
    n_cubes = int(sys.argv[1]) if len(sys.argv) > 1 else 35
    target_reg = int(sys.argv[2]) if len(sys.argv) > 2 else 7  # h
    target_bit = int(sys.argv[3]) if len(sys.argv) > 3 else 0  # bit 0

    # Load SVD basis
    corr = np.load('q5_alternative_attacks/results/20260410_difflinear_10k/correlation_matrix.npy')
    centered = corr - 0.5
    U, sv, Vt = np.linalg.svd(centered)
    basis = Vt[:n_cubes]  # 35 x 256

    print(f"Cube attack via SVD-derived cubes")
    print(f"Target: register {['a','b','c','d','e','f','g','h'][target_reg]}[63] bit {target_bit}")
    print(f"N cubes: {n_cubes}")
    print()

    M0 = 0x17149975
    fill = 0xFFFFFFFF
    rng = np.random.RandomState(42)

    # For each SVD direction, build a cube from its top components
    print(f"{'idx':<5} {'cube_size':<12} {'sum':<6} {'time'}")
    print("-" * 50)

    zero_cubes = 0
    results = []

    for c_idx in range(n_cubes):
        # Pick top 8-12 most prominent bits in this direction
        direction = basis[c_idx]
        abs_dir = np.abs(direction)
        threshold = np.sort(abs_dir)[-10]  # 10th largest
        cube_indices = [i for i in range(256) if abs_dir[i] >= threshold]
        cube_indices = cube_indices[:10]  # Cap at 10 to keep cube sum tractable

        # Random base assignment for non-cube bits
        base_bits = [rng.randint(0, 2) for _ in range(256)]

        t0 = time.time()
        cube_sum = compute_cube_sum(M0, fill, base_bits, cube_indices, target_reg, target_bit)
        elapsed = time.time() - t0

        if cube_sum == 0:
            zero_cubes += 1
            mark = " *** ZERO ***"
        else:
            mark = ""
        results.append((c_idx, len(cube_indices), cube_sum, elapsed))
        print(f"{c_idx:<5} {len(cube_indices):<12} {cube_sum:<6} {elapsed:.2f}s{mark}")

    print()
    print(f"Zero sums: {zero_cubes}/{n_cubes} ({100*zero_cubes/n_cubes:.1f}%)")
    print(f"Expected if random: 50%")
    print()

    if zero_cubes > n_cubes * 0.6 or zero_cubes < n_cubes * 0.4:
        print("*** SIGNIFICANT BIAS — algebraic structure detected ***")
    else:
        print("Cube sums look random — no exploitable structure at this cube size")


if __name__ == "__main__":
    main()
