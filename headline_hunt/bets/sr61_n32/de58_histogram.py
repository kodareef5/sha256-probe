#!/usr/bin/env python3
"""
de58_histogram.py — Per-candidate de58 distribution at N=32.

The apath_first_n8 finding (commit 8040b34) showed at N=8, de58 classes
have 4x non-uniform collision density. de58 depends ONLY on W57 (not
W58/W59/W60), so a per-candidate de58 histogram is computable in O(2^32)
time without running the full cascade-DP.

Hypothesis: candidates with non-uniform de58 distributions concentrate
collisions in a few classes — making them MORE PROMISING for sr=61
than candidates with uniform distributions.

This is a candidate predictor for sr=61, addressing the BET.yaml gap:
"no structural predictor identified that distinguishes promising from
hopeless candidates."

Method (per candidate):
  1. Compute state56 from M[0], fill, kernel-bit (precompute_state).
  2. For each W57 in [0, 2^32):
     a. Apply round 57 with W1[57] and cascade-1 offset for W2[57].
     b. Skip if cascade-1 fails (da_57 != 0 modular).
     c. Compute de58 = (e1_58 - e2_58) mod 2^32.
     d. Increment histogram[de58].
  3. Report: number of distinct de58 values, top 10 counts, entropy of
     distribution.

Output: JSONL with one record per candidate.

Runtime estimate: 2^32 trials × ~100ns Python = ~7 min/candidate.
For 9 candidates: ~1 hour. Too slow in pure Python.

Compromise: sample 2^20 random W57 values per candidate to estimate
the distribution. ~5 sec/candidate, total ~45 sec for 9.
"""
import argparse
import json
import os
import random
import sys
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
from lib.sha256 import (K, MASK, Sigma0, Sigma1, Ch, Maj, add, precompute_state)


def cascade1_offset(s1, s2):
    dh = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    T2_1 = (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & MASK
    T2_2 = (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & MASK
    return (dh + dSig1 + dCh + T2_1 - T2_2) & MASK


def apply_round(state, w, r):
    T1 = add(state[7], Sigma1(state[4]), Ch(state[4], state[5], state[6]), K[r], w)
    T2 = add(Sigma0(state[0]), Maj(state[0], state[1], state[2]))
    a = add(T1, T2)
    e = add(state[3], T1)
    return (a, state[0], state[1], state[2], e, state[4], state[5], state[6])


def candidate_de58_histogram(m0, fill, kernel_bit, n_samples=1<<20, seed=42):
    """Sample n_samples random W57 values, compute de58 for each.
    Returns Counter of de58 values."""
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= (1 << kernel_bit)
    M2[9] ^= (1 << kernel_bit)
    s1, _ = precompute_state(M1)
    s2, _ = precompute_state(M2)
    if s1[0] != s2[0]:
        return None  # not cascade-eligible

    cw57 = cascade1_offset(s1, s2)
    rng = random.Random(seed)
    counts = Counter()
    n_held = 0
    for _ in range(n_samples):
        w1_57 = rng.randrange(1 << 32)
        w2_57 = (w1_57 + cw57) & MASK
        s1_57 = apply_round(s1, w1_57, 57)
        s2_57 = apply_round(s2, w2_57, 57)
        # cascade-1 should hold by construction
        if (s1_57[0] - s2_57[0]) & MASK != 0:
            continue
        n_held += 1
        # Compute de58 — depends on s1_57, s2_57 + W58 schedule, but we can
        # extract it as the de57 contribution to round 58 IF we apply round 58
        # with the cascade-extending W58. Cascade extends → da_58=0.
        cw58 = cascade1_offset(s1_57, s2_57)
        # We need w58 value. To match apath_first_n8's notion of "de58 depends
        # only on W57", we use w58=0 (a fixed canonical choice). The structure
        # claim is that de58_distribution-mod-W58 depends only on W57.
        # Actually re-reading: de58 means de at ROUND 58 = e_diff after round 58.
        # Apply round 58 with w1=0, w2=cw58:
        s1_58 = apply_round(s1_57, 0, 58)
        s2_58 = apply_round(s2_57, cw58, 58)
        de58 = (s1_58[4] - s2_58[4]) & MASK
        counts[de58] += 1
    return counts, n_held


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", type=int, default=1<<14, help="W57 samples per candidate")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    # Candidates from registry (one per kernel family)
    candidates = [
        ("0x17149975", "0xffffffff", 31, "MSB"),
        ("0x8299b36f", "0x80000000", 0,  "bit-0"),
        ("0x024723f3", "0x7fffffff", 6,  "bit-6"),
        ("0x3304caa0", "0x80000000", 10, "bit-10 sigma1"),
        ("0x45b0a5f6", "0x00000000", 11, "bit-11 sigma1"),
        ("0x4d9f691c", "0x55555555", 13, "bit-13"),
        ("0x427c281d", "0x80000000", 17, "bit-17"),
        ("0x51ca0b34", "0x55555555", 19, "bit-19"),
        ("0x09990bd2", "0x80000000", 25, "bit-25"),
    ]

    print(f"# de58 histograms at N=32, {args.samples} samples per candidate", file=sys.stderr)
    print(f"# tag,m0,bit,distinct,top1_pct,top10_pct,entropy_bits", file=sys.stderr)

    for m0_hex, fill_hex, bit, tag in candidates:
        m0 = int(m0_hex, 16)
        fill = int(fill_hex, 16)
        t0 = time.time()
        result = candidate_de58_histogram(m0, fill, bit, n_samples=args.samples, seed=args.seed)
        elapsed = time.time() - t0
        if result is None:
            print(json.dumps({"tag": tag, "error": "not cascade-eligible"}))
            continue
        counts, n_held = result
        n = sum(counts.values())
        distinct = len(counts)
        top10 = counts.most_common(10)
        top1_pct = top10[0][1] / n * 100 if top10 else 0
        top10_pct = sum(c for _, c in top10) / n * 100
        # Shannon entropy in bits
        import math
        entropy = -sum((c/n) * math.log2(c/n) for c in counts.values() if c > 0)
        rec = {
            "tag": tag, "m0": m0_hex, "fill": fill_hex, "bit": bit,
            "n_samples": n_held, "distinct": distinct,
            "top1_pct": round(top1_pct, 2),
            "top10_pct": round(top10_pct, 2),
            "entropy_bits": round(entropy, 2),
            "max_entropy": round(math.log2(n) if n > 0 else 0, 2),
            "elapsed_s": round(elapsed, 2),
        }
        print(json.dumps(rec))
        sys.stdout.flush()


if __name__ == "__main__":
    main()
