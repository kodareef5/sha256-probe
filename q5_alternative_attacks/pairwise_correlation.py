#!/usr/bin/env python3
"""
pairwise_correlation.py — Measure higher-order (pair-flip) correlations
in the cascade-constrained sr=60 landscape.

The single-bit diff-linear matrix (Issue #14) found 35-dim low-rank
structure but plateaued at HW~74. The round-by-round profile showed
the cert uses specific W[58]/W[59] patterns that random can't match.

Hypothesis: some PAIRS of input bits flip together to cancel carry
chains. The diff-linear matrix misses these by measuring only
single-bit effects.

For each pair of input bits (i, j), measure:
- P(output bit k flips | input bit i flips alone)
- P(output bit k flips | input bit j flips alone)
- P(output bit k flips | both i and j flip together)

If the third is STRICTLY LESS than XOR of the first two, there's
a pairwise interaction (carry cancellation).

With 256 input bits, there are ~32K pairs. Too many for exhaustive
enumeration at 10K samples each. So we sample a subset and look for
bits-with-strong-pairwise-coupling.

Usage: python3 pairwise_correlation.py [n_pairs] [n_samples_per_pair]
"""

import sys, os, time, random
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')
from lib.sha256 import *


def eval_tail_diff(state1, state2, W1_pre, W2_pre, w1_free, w2_free):
    """Run 7 tail rounds for both messages, return 256-bit output XOR."""
    W1_tail = build_schedule_tail(W1_pre, w1_free)
    W2_tail = build_schedule_tail(W2_pre, w2_free)
    trace1 = run_tail_rounds(state1, W1_tail)
    trace2 = run_tail_rounds(state2, W2_tail)
    final1 = trace1[-1]
    final2 = trace2[-1]
    bits = []
    for w in [final1[i] ^ final2[i] for i in range(8)]:
        for b in range(31, -1, -1):
            bits.append((w >> b) & 1)
    return np.array(bits, dtype=np.uint8)


def flip_bit(w1_words, w2_words, bit_idx):
    """Return new (w1, w2) with the given input bit flipped.
    bit_idx: 0-127 = M1 W[57..60], 128-255 = M2 W[57..60]."""
    if bit_idx < 128:
        w_idx = bit_idx // 32
        bp = 31 - (bit_idx % 32)
        new_w1 = list(w1_words); new_w1[w_idx] ^= (1 << bp)
        return new_w1, w2_words
    else:
        idx = bit_idx - 128
        w_idx = idx // 32
        bp = 31 - (idx % 32)
        new_w2 = list(w2_words); new_w2[w_idx] ^= (1 << bp)
        return w1_words, new_w2


def measure_pairwise(m0=0x17149975, fill=0xFFFFFFFF, n_pairs=100, n_samples=2000):
    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= 0x80000000; M2[9] ^= 0x80000000
    s1, W1_pre = precompute_state(M1)
    s2, W2_pre = precompute_state(M2)

    rng = np.random.RandomState(42)

    # Focus pairs: the W[58] bits, which we know from the profile
    # are where the cert differs from random the most
    # W[58] bits in M1: indices 32-63; in M2: indices 160-191
    candidate_bits = list(range(32, 64)) + list(range(160, 192))  # 64 W[58] bits

    # Sample n_pairs pairs from W[58] bits
    pair_sample = []
    for _ in range(n_pairs):
        i, j = rng.choice(candidate_bits, 2, replace=False)
        pair_sample.append((i, j))

    print(f"Measuring {n_pairs} pairs over {n_samples} base samples each")
    print(f"Candidate bits: {len(candidate_bits)} (W[58] in both messages)")
    print()

    pair_results = []
    t0 = time.time()

    for pair_idx, (bit_i, bit_j) in enumerate(pair_sample):
        # Measure single and joint flip effects on output bits
        base_output_diffs = np.zeros((n_samples, 256), dtype=np.uint8)
        i_flip_diffs = np.zeros((n_samples, 256), dtype=np.uint8)
        j_flip_diffs = np.zeros((n_samples, 256), dtype=np.uint8)
        ij_flip_diffs = np.zeros((n_samples, 256), dtype=np.uint8)

        for s in range(n_samples):
            w1 = [int(rng.randint(0, 0x100000000)) for _ in range(4)]
            w2 = [int(rng.randint(0, 0x100000000)) for _ in range(4)]
            base_output_diffs[s] = eval_tail_diff(s1, s2, W1_pre, W2_pre, w1, w2)

            # Flip bit i
            wi1, wi2 = flip_bit(w1, w2, bit_i)
            i_flip_diffs[s] = eval_tail_diff(s1, s2, W1_pre, W2_pre, wi1, wi2)

            # Flip bit j
            wj1, wj2 = flip_bit(w1, w2, bit_j)
            j_flip_diffs[s] = eval_tail_diff(s1, s2, W1_pre, W2_pre, wj1, wj2)

            # Flip both
            wij1, wij2 = flip_bit(wi1, wi2, bit_j)
            ij_flip_diffs[s] = eval_tail_diff(s1, s2, W1_pre, W2_pre, wij1, wij2)

        # Per-output-bit XOR frequencies
        p_i = np.mean(base_output_diffs ^ i_flip_diffs, axis=0)  # P(bit k flips | i flipped)
        p_j = np.mean(base_output_diffs ^ j_flip_diffs, axis=0)
        p_ij = np.mean(base_output_diffs ^ ij_flip_diffs, axis=0)

        # Expected under independence: p_ij_exp = p_i + p_j - 2*p_i*p_j (XOR probability)
        p_ij_exp = p_i + p_j - 2 * p_i * p_j

        # Interaction signal: |p_ij - p_ij_exp|
        interaction = np.abs(p_ij - p_ij_exp)
        max_interaction = interaction.max()

        pair_results.append({
            'bits': (bit_i, bit_j),
            'max_interaction': max_interaction,
            'n_strong_interactions': np.sum(interaction > 0.1),
            'mean_interaction': interaction.mean(),
        })

        if pair_idx < 5 or pair_idx % 20 == 0:
            print(f"  pair {pair_idx}: bits ({bit_i}, {bit_j}) "
                  f"max_int={max_interaction:.3f}, "
                  f"strong={np.sum(interaction > 0.1)}, "
                  f"mean={interaction.mean():.4f}", flush=True)

    print(f"\nTotal time: {time.time()-t0:.1f}s")

    # Aggregate stats
    max_interactions = [r['max_interaction'] for r in pair_results]
    print(f"\nMax interaction across {n_pairs} pairs:")
    print(f"  mean: {np.mean(max_interactions):.4f}")
    print(f"  max: {np.max(max_interactions):.4f}")
    print(f"  >0.1: {sum(1 for m in max_interactions if m > 0.1)}")
    print(f"  >0.2: {sum(1 for m in max_interactions if m > 0.2)}")
    print(f"  >0.4: {sum(1 for m in max_interactions if m > 0.4)}")

    # Top pairs by interaction
    sorted_pairs = sorted(pair_results, key=lambda r: -r['max_interaction'])
    print(f"\nTop 10 pairs by max interaction:")
    for p in sorted_pairs[:10]:
        i, j = p['bits']
        msg_i = 'M1' if i < 128 else 'M2'
        bit_i_local = (i - (128 if i >= 128 else 0)) % 32
        msg_j = 'M1' if j < 128 else 'M2'
        bit_j_local = (j - (128 if j >= 128 else 0)) % 32
        print(f"  ({msg_i}W[58] bit {31-bit_i_local}, {msg_j}W[58] bit {31-bit_j_local}): "
              f"max={p['max_interaction']:.4f}, strong={p['n_strong_interactions']}")


def main():
    n_pairs = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    n_samples = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
    measure_pairwise(n_pairs=n_pairs, n_samples=n_samples)


if __name__ == "__main__":
    main()
