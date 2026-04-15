#!/usr/bin/env python3
"""
Rank-Defect Critical Pair Predictor

For each kernel bit at N=8, compute the linearized schedule-cascade bridge
matrix and identify which W[60] bit pairs reduce its rank enough to make
sr=61 satisfiable.

The hypothesis: critical pairs correspond to rank-deficient submatrices
of the bridge between sigma1(schedule) and cascade offset constraints.

This predicts critical pairs WITHOUT running Kissat.
"""
import sys, os
import numpy as np
from itertools import combinations

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

N = int(sys.argv[1]) if len(sys.argv) > 1 else 8

# Import SHA-256 primitives
spec = __import__('50_precision_homotopy')
sha = spec.MiniSHA256(N)
MASK = sha.MASK
KT = [k & MASK for k in spec.K32]

print(f"=== Rank-Defect Critical Pair Predictor, N={N} ===\n")

def test_kernel(kbit):
    """For a given kernel bit, compute the schedule-cascade mismatch structure."""
    delta = 1 << kbit

    # Find valid candidate
    for m0 in range(1 << N):
        M1 = [m0] + [MASK] * 15
        M2 = list(M1); M2[0] ^= delta; M2[9] = MASK ^ delta
        s1, W1p = sha.compress(M1)
        s2, W2p = sha.compress(M2)
        if (s1[0] - s2[0]) % (1 << N) == 0:
            break
    else:
        return None  # No valid candidate

    # For a sample of (w57, w58, w59) triples, compute the W2[60] mismatch
    # at each bit position. The mismatch is:
    #   mismatch = schedule_W2[60] XOR cascade_W2[60]
    # When bits (i,j) are freed, the mismatch at those bits doesn't matter.

    # Build a "mismatch profile" matrix M:
    # M[sample][bit] = 1 if mismatch at that bit for that sample
    # A critical pair (i,j) must cover the mismatch in enough samples.

    def sha_round_concrete(s, k, w):
        T1 = (s[7] + sha.Sigma1(s[4]) + sha.ch(s[4], s[5], s[6]) + k + w) & MASK
        T2 = (sha.Sigma0(s[0]) + sha.maj(s[0], s[1], s[2])) & MASK
        return [(T1 + T2) & MASK, s[0], s[1], s[2], (s[3] + T1) & MASK, s[4], s[5], s[6]]

    def find_w2_val(sa, sb, rnd, w1):
        r1 = (sa[7] + sha.Sigma1(sa[4]) + sha.ch(sa[4], sa[5], sa[6]) + KT[rnd]) & MASK
        r2 = (sb[7] + sha.Sigma1(sb[4]) + sha.ch(sb[4], sb[5], sb[6]) + KT[rnd]) & MASK
        T21 = (sha.Sigma0(sa[0]) + sha.maj(sa[0], sa[1], sa[2])) & MASK
        T22 = (sha.Sigma0(sb[0]) + sha.maj(sb[0], sb[1], sb[2])) & MASK
        return (w1 + r1 - r2 + T21 - T22) & MASK

    # Sample mismatches
    n_samples = min(256, (1 << N))
    mismatch_bits = np.zeros((n_samples * n_samples, N), dtype=np.int32)
    idx = 0

    for w57 in range(n_samples):
        sa, sb = list(s1), list(s2)
        w57b = find_w2_val(sa, sb, 57, w57)
        sa = sha_round_concrete(sa, KT[57], w57)
        sb = sha_round_concrete(sb, KT[57], w57b)

        for w58 in range(n_samples):
            s2a, s2b = list(sa), list(sb)
            w58b = find_w2_val(s2a, s2b, 58, w58)
            s2a = sha_round_concrete(s2a, KT[58], w58)
            s2b = sha_round_concrete(s2b, KT[58], w58b)

            # For w59=0: compute the cascade offset at round 60
            s3a, s3b = list(s2a), list(s2b)
            w59 = 0
            w59b = find_w2_val(s3a, s3b, 59, w59)
            s3a = sha_round_concrete(s3a, KT[59], w59)
            s3b = sha_round_concrete(s3b, KT[59], w59b)

            cascade_off = find_w2_val(s3a, s3b, 60, 0)

            # Schedule W[60] = sigma1(W[58]) + W[53] + sigma0(W[45]) + W[44]
            sched_w1_60 = (sha.sigma1(w58) + W1p[53] + sha.sigma0(W1p[45]) + W1p[44]) & MASK
            sched_w2_60 = (sha.sigma1(w58b) + W2p[53] + sha.sigma0(W2p[45]) + W2p[44]) & MASK

            # Cascade W2[60] = sched_w1_60 + cascade_off
            cascade_w2_60 = (sched_w1_60 + cascade_off) & MASK

            # Mismatch: where schedule and cascade disagree for path 2
            mismatch = sched_w2_60 ^ cascade_w2_60

            for bit in range(N):
                mismatch_bits[idx][bit] = (mismatch >> bit) & 1
            idx += 1

    mismatch_bits = mismatch_bits[:idx]

    # For each bit: what fraction of samples have mismatch?
    bit_mismatch_freq = np.mean(mismatch_bits, axis=0)

    # For each pair (i,j): if we free bits i and j, we eliminate the mismatch
    # at those positions. The remaining mismatch must be zero for sr=61 to be SAT.
    # A pair is "promising" if freeing those 2 bits leaves many samples with
    # zero remaining mismatch.

    pair_scores = {}
    for i, j in combinations(range(N), 2):
        # Remaining mismatch: all bits except i and j
        remaining = np.copy(mismatch_bits)
        remaining[:, i] = 0
        remaining[:, j] = 0
        # Count samples where remaining mismatch is all zero
        zero_remaining = np.sum(np.all(remaining == 0, axis=1))
        pair_scores[(i, j)] = zero_remaining / idx

    return {
        'kbit': kbit,
        'm0': m0,
        'bit_mismatch_freq': bit_mismatch_freq,
        'pair_scores': pair_scores,
        'n_samples': idx,
    }


# Test all kernel bits
print(f"Testing kernel bits 0..{N-1}:\n")
all_results = {}

for kbit in range(N):
    result = test_kernel(kbit)
    if result is None:
        print(f"  Kernel bit {kbit}: no valid candidate")
        continue

    all_results[kbit] = result

    # Find best pairs
    top_pairs = sorted(result['pair_scores'].items(), key=lambda x: -x[1])[:5]
    best_pair, best_score = top_pairs[0]

    print(f"  Kernel bit {kbit} (M[0]=0x{result['m0']:02x}):")
    print(f"    Mismatch freq: {' '.join(f'{f:.2f}' for f in result['bit_mismatch_freq'])}")
    print(f"    Top pairs by zero-remaining-mismatch score:")
    for pair, score in top_pairs:
        marker = " *** PREDICTED CRITICAL" if score > 0 else ""
        print(f"      ({pair[0]},{pair[1]}): {score:.4f} ({int(score*result['n_samples'])}/{result['n_samples']}){marker}")
    print()

# Validate against known results
print("=" * 60)
print("VALIDATION against known Kissat results:")
print("=" * 60)
known = {
    7: [(4, 5)],       # MSB kernel: pair (4,5) only
    6: [(1, 2), (1, 4), (3, 7)],  # bit-6: three pairs
}

for kbit, known_pairs in known.items():
    if kbit not in all_results:
        continue
    result = all_results[kbit]
    predicted = [p for p, s in result['pair_scores'].items() if s > 0]
    predicted_set = set(predicted)
    known_set = set(known_pairs)

    print(f"\n  Kernel bit {kbit}:")
    print(f"    Known critical pairs (Kissat): {sorted(known_set)}")
    print(f"    Predicted (score > 0):         {sorted(predicted_set)}")
    if known_set == predicted_set:
        print(f"    *** PERFECT MATCH ***")
    elif known_set.issubset(predicted_set):
        print(f"    Known is subset of predicted (overprediction)")
    elif predicted_set.issubset(known_set):
        print(f"    Predicted is subset of known (underprediction)")
    else:
        overlap = known_set & predicted_set
        print(f"    Overlap: {sorted(overlap)}, missed: {sorted(known_set - predicted_set)}, extra: {sorted(predicted_set - known_set)}")
