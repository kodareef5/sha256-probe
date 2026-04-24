#!/usr/bin/env python3
"""
hard_residue_analyzer.py — Identify the empirical "hard residue" bits.

The bet hypothesis: 232/256 bits at round 63 are "almost free" (fully
randomized by cascade structure), and only 24 bits constitute a structural
hard residue. This script tests that empirically by:

1. Sampling N random (W[57], W[58], W[59]) triples with cascade-driven W[60].
2. For each of 256 bits at round 63 (8 regs × 32 bits), counting how often
   it is 1 vs 0 in the difference vector.
3. Reporting per-bit deviation from 50% — bits near 50% are "free", bits
   far from 50% are "structured".
4. Ranking the top-K most-biased bits — these are the empirical hard residue.

If exactly ~24 bits are structurally biased (and the other 232 are uniform),
the bet hypothesis is empirically supported. If the number is much larger
(say 60+) or much smaller (say 4), the hypothesis needs revision.

Usage:
    python3 hard_residue_analyzer.py --m0 0x17149975 --fill 0xffffffff \
        --kernel-bit 31 --samples 1000000 --threshold 0.05 --out report.md
"""
import argparse
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
from lib.sha256 import (K, MASK, sigma0, sigma1, Sigma0, Sigma1, Ch, Maj, hw,
                        add, precompute_state)
# Reuse the cascade machinery
sys.path.insert(0, HERE)
from forward_table_builder import (cascade_step_offset, cascade2_offset,
                                    apply_round, run_one)

REG_NAMES = "abcdefgh"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m0", default="0x17149975")
    ap.add_argument("--fill", default="0xffffffff")
    ap.add_argument("--kernel-bit", type=int, default=31)
    ap.add_argument("--samples", type=int, default=1_000_000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--w1-60", default="0xb6befe82")
    ap.add_argument("--threshold", type=float, default=0.05,
                    help="Bits with |freq-0.5| > threshold are 'structured'. "
                         "Default 0.05 (95%% CI at 1M samples ≈ ±0.001, so 0.05 is "
                         "well outside noise).")
    ap.add_argument("--out", default=None,
                    help="Write markdown report to this path (default: stdout)")
    args = ap.parse_args()

    m0 = int(args.m0, 16)
    fill = int(args.fill, 16)
    diff = 1 << args.kernel_bit
    w1_60_anchor = int(args.w1_60, 16)

    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= diff; M2[9] ^= diff
    s1, W1p = precompute_state(M1)
    s2, W2p = precompute_state(M2)
    if s1[0] != s2[0]:
        print(f"ERROR: candidate not cascade-eligible (da[56] != 0)", file=sys.stderr)
        sys.exit(2)

    # Per-bit counters at BOTH round 60 (where MITM should split per bet hypothesis)
    # and round 63 (the collision boundary).
    bit_one_count_60 = [[0] * 32 for _ in range(8)]
    bit_one_count_63 = [[0] * 32 for _ in range(8)]
    n_kept = 0
    n_attempted = 0

    rng = random.Random(args.seed)
    cert = {"w57": 0x9ccfa55e, "w58": 0xd9d64416, "w59": 0x9e3ffb08, "w60": 0xb6befe82}

    t0 = time.time()
    for trial in range(args.samples):
        n_attempted += 1
        if trial == 0:
            w1_57, w1_58, w1_59, w1_60 = cert["w57"], cert["w58"], cert["w59"], cert["w60"]
        else:
            w1_57 = rng.getrandbits(32)
            w1_58 = rng.getrandbits(32)
            w1_59 = rng.getrandbits(32)
            w1_60 = w1_60_anchor
        result = run_one(s1, s2, W1p, W2p, w1_57, w1_58, w1_59, w1_60,
                          return_intermediate=True)
        if result is None:
            continue
        n_kept += 1
        d60 = result["diff60"]
        d63 = result["diff63"]
        for r in range(8):
            v60, v63 = d60[r], d63[r]
            for b in range(32):
                if (v60 >> b) & 1: bit_one_count_60[r][b] += 1
                if (v63 >> b) & 1: bit_one_count_63[r][b] += 1

    elapsed = time.time() - t0
    rate = n_attempted / elapsed if elapsed else 0

    # Compute frequencies and biases
    if n_kept == 0:
        print("ERROR: no cascade-held samples", file=sys.stderr)
        sys.exit(2)

    def analyze(counts, label):
        bit_freq = [[counts[r][b] / n_kept for b in range(32)] for r in range(8)]
        bit_bias = [[abs(f - 0.5) for f in row] for row in bit_freq]
        all_bits = [{"reg": REG_NAMES[r], "bit": b,
                     "freq_one": bit_freq[r][b], "bias": bit_bias[r][b]}
                    for r in range(8) for b in range(32)]
        all_bits.sort(key=lambda x: -x["bias"])
        structured = [bb for bb in all_bits if bb["bias"] > args.threshold]

        lines = []
        lines.append(f"## Round-{label} analysis")
        lines.append("")
        lines.append(f"- Structured bits (|freq-0.5| > {args.threshold}): "
                     f"**{len(structured)} of 256**")
        lines.append("")
        lines.append("Per-register summary:")
        lines.append("")
        lines.append("| Reg | Structured | Bias-mean | Bias-max | freq=0 bits | freq=1 bits |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for r in range(8):
            struct_in_reg = sum(1 for b in range(32) if bit_bias[r][b] > args.threshold)
            bmean = sum(bit_bias[r]) / 32
            bmax = max(bit_bias[r])
            zero_bits = sum(1 for b in range(32) if bit_freq[r][b] < 0.001)
            one_bits = sum(1 for b in range(32) if bit_freq[r][b] > 0.999)
            lines.append(f"| {REG_NAMES[r]} | {struct_in_reg} | {bmean:.4f} | {bmax:.4f} | "
                         f"{zero_bits} | {one_bits} |")
        lines.append("")
        # Top biased bits (skip pure-zero bits — those are cascade-guaranteed and uninformative)
        non_zero_struct = [bb for bb in structured if bb["freq_one"] > 0.001]
        lines.append("Top biased bits (excluding cascade-guaranteed zero bits):")
        lines.append("")
        if non_zero_struct:
            lines.append("| Rank | Reg | Bit | freq(=1) | bias |")
            lines.append("|---:|---|---:|---:|---:|")
            for i, bb in enumerate(non_zero_struct[:30], 1):
                lines.append(f"| {i} | {bb['reg']} | {bb['bit']} | "
                             f"{bb['freq_one']:.4f} | {bb['bias']:.4f} |")
        else:
            lines.append("(none — all structured bits are pure zeros)")
        lines.append("")
        lines.append("Per-register bit-by-bit frequency of 1 (low bit on left):")
        lines.append("")
        lines.append("```")
        for r in range(8):
            row = " ".join(f"{bit_freq[r][b]:.3f}" for b in range(32))
            lines.append(f"{REG_NAMES[r]}: {row}")
        lines.append("```")
        lines.append("")
        return lines

    # Build report
    lines = []
    lines.append(f"# Hard-residue bit identification — {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
    lines.append("")
    lines.append(f"- Candidate: m0={args.m0}, fill={args.fill}, kernel_bit={args.kernel_bit}")
    lines.append(f"- Samples attempted: {n_attempted}")
    lines.append(f"- Samples cascade-held: {n_kept}")
    lines.append(f"- Throughput: {rate:.0f} samples/sec ({elapsed:.1f}s)")
    lines.append(f"- Bias threshold: {args.threshold} (bit is 'structured' if |freq(=1) - 0.5| > threshold)")
    lines.append("")
    lines.append("Note: 'structured bits' include both *cascade-guaranteed-zero* bits "
                 "(freq=0.000) and *biased-but-non-zero* bits. The top-biased table below "
                 "excludes the cascade-zero set because those are theoretically expected "
                 "by the cascade structure (Theorems 1-3 of the boundary proof).")
    lines.append("")
    # Round 60 first — that's where the bet's MITM split is supposed to happen
    lines.extend(analyze(bit_one_count_60, "60"))
    # Round 63 — the collision boundary
    lines.extend(analyze(bit_one_count_63, "63"))

    out_text = "\n".join(lines)
    if args.out is None:
        print(out_text)
    else:
        with open(args.out, "w") as f:
            f.write(out_text + "\n")
        print(f"Wrote report to {args.out}", file=sys.stderr)
        # Compute round-60 and round-63 structured-bit counts for stderr summary
        for label, counts in (("60", bit_one_count_60), ("63", bit_one_count_63)):
            n_struct = sum(1 for r in range(8) for b in range(32)
                            if abs(counts[r][b]/n_kept - 0.5) > args.threshold)
            print(f"  Round {label}: {n_struct}/256 structured", file=sys.stderr)


if __name__ == "__main__":
    main()
