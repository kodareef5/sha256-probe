#!/usr/bin/env python3
"""
SVD-projected hill climbing in cascade-constrained space.

Instead of flipping single bits (which empirically fails), flip
"principal direction" patterns extracted from the diff-linear
correlation matrix. The top-35 SVD components of that matrix
capture 90% of the linear structure in the 7-round tail.

Each perturbation flips a bit PATTERN (not a single bit) derived
from one of the 35 principal directions. The expectation is that
these are aligned with the actual problem geometry rather than
arbitrary coordinate axes.

Input basis: saved as /tmp/svd_basis_35.npy
Shape: (35, 256) where 256 = 2 msgs * 4 words * 32 bits
"""

import sys, os, time, random
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def precompute_offsets(m0, fill):
    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1, W1_pre = precompute_state(M1)
    s2, W2_pre = precompute_state(M2)

    dh = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    T2_1 = (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & MASK
    T2_2 = (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & MASK
    dT2 = (T2_1 - T2_2) & MASK
    C_w57 = (dh + dSig1 + dCh + dT2) & MASK

    return s1, s2, W1_pre, W2_pre, C_w57


def one_round(s, w, i):
    T1 = add(s[7], Sigma1(s[4]), Ch(s[4], s[5], s[6]), K[i], w)
    T2 = add(Sigma0(s[0]), Maj(s[0], s[1], s[2]))
    return (add(T1, T2), s[0], s[1], s[2], add(s[3], T1), s[4], s[5], s[6])


def bits256_to_words(bits):
    """Convert 256-bit flat array to (w1_57, w1_58, w1_59, w1_60, w2_57, ...) tuple."""
    # Indexing: 0-31 = M1 W[57], 32-63 = M1 W[58], ... 128-159 = M2 W[57], ...
    words = []
    for w in range(8):
        v = 0
        for b in range(32):
            if bits[w*32 + b]:
                v |= 1 << (31 - b)  # MSB first
        words.append(v)
    return words  # [w1_57, w1_58, w1_59, w1_60, w2_57, w2_58, w2_59, w2_60]


def words_to_bits256(words):
    bits = np.zeros(256, dtype=np.uint8)
    for w in range(8):
        for b in range(32):
            if (words[w] >> (31 - b)) & 1:
                bits[w*32 + b] = 1
    return bits


def evaluate_from_bits(s1_init, s2_init, W1_pre, W2_pre, C_w57, bits):
    """Evaluate a 256-bit configuration with cascade constraints."""
    words = bits256_to_words(bits)
    w1_57, w1_58, w1_59, w1_60, _, w2_58, w2_59, w2_60 = words
    # Override w2_57 with cascade 1 constraint
    w2_57 = (w1_57 + C_w57) & MASK

    s1 = one_round(s1_init, w1_57, 57)
    s2 = one_round(s2_init, w2_57, 57)
    s1 = one_round(s1, w1_58, 58)
    s2 = one_round(s2, w2_58, 58)
    s1 = one_round(s1, w1_59, 59)
    s2 = one_round(s2, w2_59, 59)

    # Cascade 2 constraint: override w2_60 to zero de60
    dh59 = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    C_w60 = (dh59 + dSig1 + dCh) & MASK
    w2_60 = (w1_60 + C_w60) & MASK

    W1_tail = build_schedule_tail(W1_pre, [w1_57, w1_58, w1_59, w1_60])
    W2_tail = build_schedule_tail(W2_pre, [w2_57, w2_58, w2_59, w2_60])
    t1 = run_tail_rounds(s1_init, W1_tail)
    t2 = run_tail_rounds(s2_init, W2_tail)
    f1, f2 = t1[-1], t2[-1]
    return sum(hw(f1[r] ^ f2[r]) for r in range(8))


def svd_perturbation(basis, direction_idx, threshold=0.05):
    """Convert a SVD direction to a 256-bit mask (bits with high |component|)."""
    direction = basis[direction_idx]
    # Take bits with absolute component above threshold
    mask = np.abs(direction) > threshold
    return mask.astype(np.uint8)


def hill_climb_svd(s1_init, s2_init, W1_pre, W2_pre, C_w57, basis,
                    max_steps, rng):
    """Hill climb using SVD direction flips."""
    # Random starting bits
    bits = np.array([rng.randint(0, 1) for _ in range(256)], dtype=np.uint8)
    best_hw = evaluate_from_bits(s1_init, s2_init, W1_pre, W2_pre, C_w57, bits)

    n_directions = len(basis)

    for step in range(max_steps):
        # Pick a random SVD direction and perturb along it
        dir_idx = rng.randint(0, n_directions - 1)
        threshold = rng.uniform(0.03, 0.15)
        mask = svd_perturbation(basis, dir_idx, threshold)

        # XOR the mask onto bits
        bits_new = bits ^ mask
        new_hw = evaluate_from_bits(s1_init, s2_init, W1_pre, W2_pre, C_w57, bits_new)

        if new_hw < best_hw:
            best_hw = new_hw
            bits = bits_new
            if new_hw == 0:
                return best_hw, bits, step

    return best_hw, bits, max_steps


def main():
    n_restarts = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    steps_per = int(sys.argv[2]) if len(sys.argv) > 2 else 3000

    basis = np.load('/tmp/svd_basis_35.npy')
    print(f"Loaded SVD basis: shape {basis.shape}")

    # Show typical mask sizes at various thresholds
    for t in [0.03, 0.05, 0.1, 0.15, 0.2]:
        sizes = [np.sum(np.abs(basis[i]) > t) for i in range(35)]
        print(f"  Threshold {t}: mask sizes mean={np.mean(sizes):.1f}, "
              f"min={np.min(sizes)}, max={np.max(sizes)}")

    m0 = 0x17149975
    fill = 0xFFFFFFFF
    s1, s2, W1_pre, W2_pre, C_w57 = precompute_offsets(m0, fill)

    print(f"\nSVD-projected hill climbing")
    print(f"Restarts: {n_restarts}, Steps per restart: {steps_per}")
    print(f"Total evaluations: ~{n_restarts * steps_per:,}\n")

    rng = random.Random(42)
    t0 = time.time()
    global_best = 256
    best_per_restart = []

    for r in range(n_restarts):
        best_hw, best_bits, steps = hill_climb_svd(
            s1, s2, W1_pre, W2_pre, C_w57, basis, steps_per, rng)
        best_per_restart.append(best_hw)
        if best_hw < global_best:
            global_best = best_hw
            print(f"  [restart {r:>3}] NEW GLOBAL BEST: HW={best_hw}", flush=True)
            if best_hw == 0:
                break
        elif r % 5 == 0:
            rate = (r + 1) * steps_per / (time.time() - t0)
            print(f"  [restart {r:>3}] best={best_hw}, global={global_best}, "
                  f"{rate:.0f} eval/s", flush=True)

    t1 = time.time() - t0
    print(f"\nDone in {t1:.1f}s")
    print(f"Global best HW: {global_best}")
    print(f"Mean: {np.mean(best_per_restart):.1f}")
    print(f"Min: {min(best_per_restart)}, Max: {max(best_per_restart)}")


if __name__ == "__main__":
    main()
