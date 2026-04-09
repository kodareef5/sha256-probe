#!/usr/bin/env python3
"""
difflinear_matrix.py — Differential-linear correlation matrix (Issue #14)

For the 7-round SHA-256 tail, measure the correlation between each
free input bit flip and each output difference bit, over N random
evaluations.

Produces a (n_free_bits × n_output_bits) correlation matrix.
The RANK of this matrix reveals how much linear structure exists
in the collision problem.

CPU version (GPU version would use CUDA for SHA-256 evaluation).

Usage: python3 difflinear_matrix.py [n_samples] [candidate_m0] [candidate_fill]
"""

import sys, os, time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def eval_tail_diff(state1, state2, W1_pre, W2_pre, w1_free, w2_free):
    """Run 7 tail rounds for both messages, return output XOR diff (256 bits)."""
    W1_tail = build_schedule_tail(W1_pre, w1_free)
    W2_tail = build_schedule_tail(W2_pre, w2_free)
    trace1 = run_tail_rounds(state1, W1_tail)
    trace2 = run_tail_rounds(state2, W2_tail)
    final1 = trace1[-1]
    final2 = trace2[-1]
    # Output diff: 8 × 32-bit words = 256 bits
    diff = [final1[i] ^ final2[i] for i in range(8)]
    return diff


def words_to_bits(words, n_bits=32):
    """Convert list of 32-bit words to flat bit array (MSB first)."""
    bits = []
    for w in words:
        for b in range(n_bits - 1, -1, -1):
            bits.append((w >> b) & 1)
    return np.array(bits, dtype=np.int8)


def bits_to_words(bits, n_bits=32):
    """Convert flat bit array back to list of 32-bit words."""
    words = []
    idx = 0
    while idx < len(bits):
        w = 0
        for b in range(n_bits - 1, -1, -1):
            w |= int(bits[idx]) << b
            idx += 1
        words.append(w)
    return words


def build_correlation_matrix(m0=0x17149975, fill=0xFFFFFFFF, n_samples=100000):
    """
    Build the differential-linear correlation matrix.

    For each of 256 free input bits (4 words × 32 bits × 2 messages):
      - Sample n_samples random base points
      - Flip that one bit
      - Measure which output diff bits change

    Returns: (256 × 256) correlation matrix
    """
    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000

    s1, W1_pre = precompute_state(M1)
    s2, W2_pre = precompute_state(M2)

    n_free = 4  # W[57..60] per message
    n_free_bits = n_free * 32 * 2  # 256 bits total (both messages)
    n_out_bits = 8 * 32  # 256 output diff bits

    print(f"Building {n_free_bits}×{n_out_bits} correlation matrix")
    print(f"Samples per bit: {n_samples}")
    print(f"Candidate: M[0]=0x{m0:08x}, fill=0x{fill:08x}")
    print(f"Total evaluations: {n_free_bits * n_samples * 2:,}")
    print()

    # For efficiency, we'll sample a smaller set and reuse
    # Generate random base free words
    rng = np.random.RandomState(42)

    # Accumulate: for each input bit, count how often each output bit flips
    flip_counts = np.zeros((n_free_bits, n_out_bits), dtype=np.int64)

    t0 = time.time()
    for sample in range(n_samples):
        # Random free words for both messages
        w1_base = [int(rng.randint(0, 0x100000000)) for _ in range(n_free)]
        w2_base = [int(rng.randint(0, 0x100000000)) for _ in range(n_free)]

        # Compute base output diff
        base_diff = eval_tail_diff(s1, s2, W1_pre, W2_pre, w1_base, w2_base)
        base_bits = words_to_bits(base_diff)

        # For each free input bit, flip it and measure output change
        for bit_idx in range(n_free_bits):
            msg_idx = bit_idx // (n_free * 32)  # 0 = M1, 1 = M2
            word_idx = (bit_idx % (n_free * 32)) // 32  # which free word
            bit_pos = 31 - (bit_idx % 32)  # MSB first

            if msg_idx == 0:
                w1_flip = list(w1_base)
                w1_flip[word_idx] ^= (1 << bit_pos)
                w2_flip = w2_base
            else:
                w1_flip = w1_base
                w2_flip = list(w2_base)
                w2_flip[word_idx] ^= (1 << bit_pos)

            flip_diff = eval_tail_diff(s1, s2, W1_pre, W2_pre, w1_flip, w2_flip)
            flip_bits = words_to_bits(flip_diff)

            # Which output bits changed?
            changed = base_bits ^ flip_bits
            flip_counts[bit_idx] += changed

        if (sample + 1) % 100 == 0:
            elapsed = time.time() - t0
            rate = (sample + 1) / elapsed
            eta = (n_samples - sample - 1) / rate
            print(f"  {sample+1}/{n_samples} ({rate:.1f} samples/s, ETA {eta:.0f}s)", flush=True)

    # Convert to correlation: flip_counts / n_samples gives P(output bit flips | input bit flips)
    # Under null (random): each output bit flips with P=0.5
    corr = flip_counts.astype(float) / n_samples

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s")

    return corr


def analyze_matrix(corr):
    """Analyze the correlation matrix."""
    n_in, n_out = corr.shape
    print(f"\n=== Correlation Matrix Analysis ({n_in}×{n_out}) ===\n")

    # Center around 0.5 (null expectation)
    centered = corr - 0.5

    print(f"1. Bias from random (0.5)")
    print(f"   Mean correlation: {corr.mean():.6f} (expected 0.5)")
    print(f"   Max |bias|: {np.abs(centered).max():.6f}")
    print(f"   Entries with |bias| > 0.1: {np.sum(np.abs(centered) > 0.1)}")
    print(f"   Entries with |bias| > 0.05: {np.sum(np.abs(centered) > 0.05)}")

    # SVD of centered matrix
    U, sv, Vt = np.linalg.svd(centered, full_matrices=False)
    energy = np.cumsum(sv**2) / np.sum(sv**2)
    rank_90 = np.searchsorted(energy, 0.9) + 1
    rank_99 = np.searchsorted(energy, 0.99) + 1

    print(f"\n2. Singular Value Decomposition")
    print(f"   Top 10 singular values: {sv[:10]}")
    print(f"   Rank for 90% energy: {rank_90} of {min(n_in, n_out)}")
    print(f"   Rank for 99% energy: {rank_99} of {min(n_in, n_out)}")

    if rank_90 < min(n_in, n_out) * 0.5:
        print(f"   *** LOW RANK: correlation structure lives in {rank_90} dimensions ***")
    else:
        print(f"   Full rank — no exploitable linear structure detected")

    # Find strongest individual correlations
    print(f"\n3. Strongest Individual Correlations")
    flat = np.abs(centered).flatten()
    top_idx = np.argsort(flat)[-20:][::-1]
    for idx in top_idx:
        i, j = divmod(idx, n_out)
        msg = "M1" if i < 128 else "M2"
        word = (i % 128) // 32
        bit = i % 32
        out_reg = j // 32
        out_bit = j % 32
        regs = ['a','b','c','d','e','f','g','h']
        print(f"   {msg} W[{57+word}] bit {31-bit} -> d{regs[out_reg]}[63] bit {31-out_bit}: "
              f"{corr[i,j]:.4f} (bias {centered[i,j]:+.4f})")

    return {
        'rank_90': rank_90,
        'rank_99': rank_99,
        'max_bias': float(np.abs(centered).max()),
        'mean_corr': float(corr.mean()),
    }


def main():
    n_samples = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    m0 = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x17149975
    fill = int(sys.argv[3], 0) if len(sys.argv) > 3 else 0xFFFFFFFF

    corr = build_correlation_matrix(m0, fill, n_samples)
    results = analyze_matrix(corr)

    # Save matrix
    outpath = f"/tmp/difflinear_{m0:08x}_{n_samples}.npy"
    np.save(outpath, corr)
    print(f"\nMatrix saved to {outpath}")


if __name__ == "__main__":
    main()
