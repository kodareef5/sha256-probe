#!/usr/bin/env python3
"""
forward_bounded_searcher.py — first prototype of the cascade-equation
searcher with per-round HW pruning.

Runs both compressions M and M' = M XOR dm step-by-step (round by
round), tracks HW(state_diff) at each round, and prunes the path early
if HW exceeds a per-round threshold curve. Logs per-round survival
counts.

Compared to bf_baseline.py (which always runs 64 rounds), this
searcher demonstrates the FIRST axis of value-add: forward-bound
pruning saves wall time when most dm patterns die early.

This is NOT yet the full searcher (no memoization, no failure-core
extraction beyond per-round survival). See SPEC.md for the full design.

Usage:
    # Constant threshold T at all rounds:
    python3 forward_bounded_searcher.py --N 8 --positions 0,9 \\
        --threshold 16

    # Per-round threshold curve:
    python3 forward_bounded_searcher.py --N 8 --positions 0,9 \\
        --threshold-curve "30:16,40:14,50:12,60:8"

    # Same input as bf_baseline for direct wall comparison:
    python3 forward_bounded_searcher.py --N 10 --positions 0,9 \\
        --threshold 32 --rounds 64
"""
import argparse
import json
import sys
import time
from collections import Counter

# Reuse mini-SHA primitives from bf_baseline
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from bf_baseline import (mini_sha_primitives, hw_state_diff,
                          K_FULL, IV_FULL)


def compress_pair_with_bound(M1, M2, N, num_rounds, threshold_curve):
    """
    Run both M1 and M2 compressions round-by-round at N-bit width.
    At each round, check HW(state_diff). If exceeds threshold for that
    round, return early with (round_died, hw_at_death).
    Otherwise return (num_rounds, final_hw).
    """
    MASK, ror, Sigma0, Sigma1, sigma0, sigma1, Ch, Maj = mini_sha_primitives(N)
    K_N = [k & MASK for k in K_FULL]
    IV_N = [iv & MASK for iv in IV_FULL]

    W1 = [0] * 64
    W2 = [0] * 64
    for i in range(16):
        W1[i] = M1[i] & MASK
        W2[i] = M2[i] & MASK
    for i in range(16, 64):
        W1[i] = (sigma1(W1[i-2]) + W1[i-7] + sigma0(W1[i-15]) + W1[i-16]) & MASK
        W2[i] = (sigma1(W2[i-2]) + W2[i-7] + sigma0(W2[i-15]) + W2[i-16]) & MASK

    a1, b1, c1, d1, e1, f1, g1, h1 = IV_N
    a2, b2, c2, d2, e2, f2, g2, h2 = IV_N

    for r in range(num_rounds):
        T1_1 = (h1 + Sigma1(e1) + Ch(e1, f1, g1) + K_N[r] + W1[r]) & MASK
        T2_1 = (Sigma0(a1) + Maj(a1, b1, c1)) & MASK
        h1 = g1; g1 = f1; f1 = e1
        e1 = (d1 + T1_1) & MASK
        d1 = c1; c1 = b1; b1 = a1
        a1 = (T1_1 + T2_1) & MASK

        T1_2 = (h2 + Sigma1(e2) + Ch(e2, f2, g2) + K_N[r] + W2[r]) & MASK
        T2_2 = (Sigma0(a2) + Maj(a2, b2, c2)) & MASK
        h2 = g2; g2 = f2; f2 = e2
        e2 = (d2 + T1_2) & MASK
        d2 = c2; c2 = b2; b2 = a2
        a2 = (T1_2 + T2_2) & MASK

        # Check threshold
        if r in threshold_curve:
            t = threshold_curve[r]
            hw = (bin(a1 ^ a2).count("1") + bin(b1 ^ b2).count("1") +
                  bin(c1 ^ c2).count("1") + bin(d1 ^ d2).count("1") +
                  bin(e1 ^ e2).count("1") + bin(f1 ^ f2).count("1") +
                  bin(g1 ^ g2).count("1") + bin(h1 ^ h2).count("1"))
            if hw > t:
                return (r + 1, hw, "PRUNED")

    final_hw = (bin(a1 ^ a2).count("1") + bin(b1 ^ b2).count("1") +
                bin(c1 ^ c2).count("1") + bin(d1 ^ d2).count("1") +
                bin(e1 ^ e2).count("1") + bin(f1 ^ f2).count("1") +
                bin(g1 ^ g2).count("1") + bin(h1 ^ h2).count("1"))
    return (num_rounds, final_hw, "SURVIVED")


def parse_threshold_curve(spec, num_rounds):
    """Parse 'r1:t1,r2:t2,...' into dict {r1: t1, r2: t2, ...}."""
    if not spec:
        return {}
    curve = {}
    for pair in spec.split(","):
        if ":" not in pair:
            continue
        r, t = pair.split(":")
        r = int(r)
        t = int(t)
        if 0 <= r < num_rounds:
            curve[r] = t
    return curve


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--N", type=int, required=True)
    ap.add_argument("--positions", default="0,9")
    ap.add_argument("--rounds", type=int, default=64)
    ap.add_argument("--m0", default="zero")
    ap.add_argument("--threshold", type=int, default=None,
                    help="Constant per-round threshold (applied at every round)")
    ap.add_argument("--threshold-curve", default=None,
                    help="Comma-separated round:threshold pairs, e.g. '30:16,40:14,50:12'")
    ap.add_argument("--trace", default=None,
                    help="Trace mode: hex dm tuple 'dm_p1,dm_p2'. Prints per-round HW trajectory.")
    ap.add_argument("--cascade-filter", default=None,
                    help="Cascade signature filter: 'register:round[,register:round...]'. "
                         "Reports dm patterns where HW(register, round) = 0. "
                         "Example: 'a:60' filters by cascade-1 a-zero at round 60. "
                         "Multiple constraints (e.g. 'a:60,b:61') AND together.")
    ap.add_argument("--out-json", default=None)
    args = ap.parse_args()

    if args.m0 == "zero":
        m0 = [0] * 16
    else:
        m0 = [int(x, 16) for x in args.m0.split(",")]

    positions = [int(p) for p in args.positions.split(",")]
    if len(positions) != 2:
        print("ERROR: this prototype handles exactly 2 dm positions",
              file=sys.stderr)
        sys.exit(2)

    if args.trace:
        # Trace mode: single dm, print HW per round
        d1, d2 = [int(x, 16) for x in args.trace.split(",")]
        p1, p2 = positions
        M2 = list(m0)
        M2[p1] = (m0[p1] ^ d1) & ((1 << args.N) - 1)
        M2[p2] = (m0[p2] ^ d2) & ((1 << args.N) - 1)

        MASK, ror, Sigma0, Sigma1, sigma0, sigma1, Ch, Maj = mini_sha_primitives(args.N)
        K_N = [k & MASK for k in K_FULL]
        IV_N = [iv & MASK for iv in IV_FULL]
        W1 = [0] * 64
        W2 = [0] * 64
        for i in range(16):
            W1[i] = m0[i] & MASK
            W2[i] = M2[i] & MASK
        for i in range(16, 64):
            W1[i] = (sigma1(W1[i-2]) + W1[i-7] + sigma0(W1[i-15]) + W1[i-16]) & MASK
            W2[i] = (sigma1(W2[i-2]) + W2[i-7] + sigma0(W2[i-15]) + W2[i-16]) & MASK

        a1, b1, c1, d1_, e1, f1, g1, h1 = IV_N
        a2, b2, c2, d2_, e2, f2, g2, h2 = IV_N

        print(f"[trace N={args.N}] dm=({hex(d1)},{hex(d2)}) at positions {positions}")
        print(f"  rnd  HW_state  HW_a HW_b HW_c HW_d HW_e HW_f HW_g HW_h")
        for r in range(args.rounds):
            T1_1 = (h1 + Sigma1(e1) + Ch(e1, f1, g1) + K_N[r] + W1[r]) & MASK
            T2_1 = (Sigma0(a1) + Maj(a1, b1, c1)) & MASK
            h1 = g1; g1 = f1; f1 = e1
            e1 = (d1_ + T1_1) & MASK
            d1_ = c1; c1 = b1; b1 = a1
            a1 = (T1_1 + T2_1) & MASK

            T1_2 = (h2 + Sigma1(e2) + Ch(e2, f2, g2) + K_N[r] + W2[r]) & MASK
            T2_2 = (Sigma0(a2) + Maj(a2, b2, c2)) & MASK
            h2 = g2; g2 = f2; f2 = e2
            e2 = (d2_ + T1_2) & MASK
            d2_ = c2; c2 = b2; b2 = a2
            a2 = (T1_2 + T2_2) & MASK

            ha = bin(a1 ^ a2).count("1")
            hb = bin(b1 ^ b2).count("1")
            hc = bin(c1 ^ c2).count("1")
            hd = bin(d1_ ^ d2_).count("1")
            he = bin(e1 ^ e2).count("1")
            hf = bin(f1 ^ f2).count("1")
            hg = bin(g1 ^ g2).count("1")
            hh = bin(h1 ^ h2).count("1")
            tot = ha+hb+hc+hd+he+hf+hg+hh
            print(f"  {r:>3}  {tot:>8}  {ha:>3}  {hb:>3}  {hc:>3}  {hd:>3}  {he:>3}  {hf:>3}  {hg:>3}  {hh:>3}")
        sys.exit(0)

    if args.cascade_filter:
        # Cascade signature filter: enumerate dm space, keep only patterns
        # where HW(register R, round r) = 0 for each (R, r) constraint.
        constraints = []
        for spec in args.cascade_filter.split(","):
            reg, rnd = spec.split(":")
            reg_idx = "abcdefgh".index(reg.strip())
            rnd_idx = int(rnd.strip())
            constraints.append((reg_idx, rnd_idx))

        MASK, ror, Sigma0, Sigma1, sigma0, sigma1, Ch, Maj = mini_sha_primitives(args.N)
        K_N = [k & MASK for k in K_FULL]
        IV_N = [iv & MASK for iv in IV_FULL]

        span = 1 << args.N
        p1, p2 = positions
        survivors = []  # (dm tuple, final_hw, traj_at_constraints)
        final_hw_distribution = Counter()
        max_round = max(r for _, r in constraints)

        print(f"[N={args.N}] Cascade-filter scan over {span*span} (m[{p1}], m[{p2}]) patterns; "
              f"constraints={constraints}", file=sys.stderr)
        t0 = time.time()
        for d1 in range(span):
            for d2 in range(span):
                M2 = list(m0)
                M2[p1] = (m0[p1] ^ d1) & ((1 << args.N) - 1)
                M2[p2] = (m0[p2] ^ d2) & ((1 << args.N) - 1)
                # Compute schedules
                W1 = [0]*64; W2 = [0]*64
                for i in range(16):
                    W1[i] = m0[i] & MASK
                    W2[i] = M2[i] & MASK
                for i in range(16, min(max_round + 1, 64)):
                    W1[i] = (sigma1(W1[i-2]) + W1[i-7] + sigma0(W1[i-15]) + W1[i-16]) & MASK
                    W2[i] = (sigma1(W2[i-2]) + W2[i-7] + sigma0(W2[i-15]) + W2[i-16]) & MASK
                # Forward simulation with per-round state recording (just at constraint rounds)
                a1,b1,c1,d1_,e1,f1,g1,h1 = IV_N
                a2,b2,c2,d2_,e2,f2,g2,h2 = IV_N
                round_states = {}  # round -> 8 register diffs
                for r in range(max_round + 1):
                    T1_1 = (h1 + Sigma1(e1) + Ch(e1,f1,g1) + K_N[r] + W1[r]) & MASK
                    T2_1 = (Sigma0(a1) + Maj(a1,b1,c1)) & MASK
                    h1=g1; g1=f1; f1=e1; e1=(d1_+T1_1)&MASK
                    d1_=c1; c1=b1; b1=a1; a1=(T1_1+T2_1)&MASK
                    T1_2 = (h2 + Sigma1(e2) + Ch(e2,f2,g2) + K_N[r] + W2[r]) & MASK
                    T2_2 = (Sigma0(a2) + Maj(a2,b2,c2)) & MASK
                    h2=g2; g2=f2; f2=e2; e2=(d2_+T1_2)&MASK
                    d2_=c2; c2=b2; b2=a2; a2=(T1_2+T2_2)&MASK
                    if any(r == cr for _, cr in constraints):
                        round_states[r] = (a1^a2, b1^b2, c1^c2, d1_^d2_,
                                           e1^e2, f1^f2, g1^g2, h1^h2)
                # Check constraints
                ok = True
                for reg_idx, rnd_idx in constraints:
                    if rnd_idx not in round_states:
                        ok = False; break
                    if round_states[rnd_idx][reg_idx] != 0:
                        ok = False; break
                if not ok:
                    continue
                # Survivor — finish forward to round 63
                for r in range(max_round + 1, args.rounds):
                    if r >= 16 and r < 64:
                        W1[r] = (sigma1(W1[r-2]) + W1[r-7] + sigma0(W1[r-15]) + W1[r-16]) & MASK
                        W2[r] = (sigma1(W2[r-2]) + W2[r-7] + sigma0(W2[r-15]) + W2[r-16]) & MASK
                    T1_1 = (h1 + Sigma1(e1) + Ch(e1,f1,g1) + K_N[r] + W1[r]) & MASK
                    T2_1 = (Sigma0(a1) + Maj(a1,b1,c1)) & MASK
                    h1=g1; g1=f1; f1=e1; e1=(d1_+T1_1)&MASK
                    d1_=c1; c1=b1; b1=a1; a1=(T1_1+T2_1)&MASK
                    T1_2 = (h2 + Sigma1(e2) + Ch(e2,f2,g2) + K_N[r] + W2[r]) & MASK
                    T2_2 = (Sigma0(a2) + Maj(a2,b2,c2)) & MASK
                    h2=g2; g2=f2; f2=e2; e2=(d2_+T1_2)&MASK
                    d2_=c2; c2=b2; b2=a2; a2=(T1_2+T2_2)&MASK
                # Final HW
                fhw = (bin(a1^a2).count("1") + bin(b1^b2).count("1") +
                       bin(c1^c2).count("1") + bin(d1_^d2_).count("1") +
                       bin(e1^e2).count("1") + bin(f1^f2).count("1") +
                       bin(g1^g2).count("1") + bin(h1^h2).count("1"))
                final_hw_distribution[fhw] += 1
                if d1 != 0 or d2 != 0:
                    survivors.append(((d1, d2), fhw))
        wall = time.time() - t0

        print(f"\n=== cascade-filter scan (N={args.N}, dm@{positions}, "
              f"constraints={constraints}) ===")
        print(f"Total patterns:      {span*span}")
        print(f"Filter survivors:    {len(survivors) + (1 if (0,0) in [s[0] for s in survivors] else (1 if any(0 == k for k in final_hw_distribution if k == 0) else 0))} "
              f"(includes trivial dm=0,0 which always passes)")
        print(f"Non-trivial survivors: {len(survivors)}")
        print(f"Wall:                {wall:.3f}s")
        if survivors:
            survivors.sort(key=lambda x: x[1])
            print(f"\nMin residual HW: {survivors[0][1]}, dm=({hex(survivors[0][0][0])}, {hex(survivors[0][0][1])})")
            print(f"\nFinal HW histogram (filter survivors):")
            for hw, c in sorted(final_hw_distribution.items())[:12]:
                print(f"  HW={hw:>3}: {c}")
            print(f"\nTop-20 lowest-HW survivors:")
            for (dm, hw) in survivors[:20]:
                print(f"  HW={hw:>3}  dm=({hex(dm[0])}, {hex(dm[1])})")
        else:
            print("No non-trivial dm patterns satisfy these constraints.")
        sys.exit(0)

    if args.threshold is not None:
        threshold_curve = {r: args.threshold for r in range(args.rounds)}
    elif args.threshold_curve:
        threshold_curve = parse_threshold_curve(args.threshold_curve, args.rounds)
    else:
        # No threshold = brute force equivalent (everything survives)
        threshold_curve = {}

    span = 1 << args.N
    p1, p2 = positions
    survival_per_round = Counter()  # round -> count of patterns dying at that round
    final_hw_distribution = Counter()
    survived_count = 0
    pruned_count = 0
    min_final_hw = None
    best_dm = None

    print(f"[N={args.N}] Forward-bounded search over {span * span} (m[{p1}], m[{p2}]) patterns, "
          f"threshold curve has {len(threshold_curve)} round-thresholds",
          file=sys.stderr)
    t0 = time.time()
    for d1 in range(span):
        for d2 in range(span):
            M2 = list(m0)
            M2[p1] = (m0[p1] ^ d1) & ((1 << args.N) - 1)
            M2[p2] = (m0[p2] ^ d2) & ((1 << args.N) - 1)
            died_round, hw, status = compress_pair_with_bound(
                m0, M2, args.N, args.rounds, threshold_curve,
            )
            if status == "PRUNED":
                pruned_count += 1
                survival_per_round[died_round] += 1
            else:
                survived_count += 1
                final_hw_distribution[hw] += 1
                if d1 != 0 or d2 != 0:
                    if min_final_hw is None or hw < min_final_hw:
                        min_final_hw = hw
                        best_dm = (d1, d2)
    wall = time.time() - t0
    total_patterns = span * span

    print(f"\n=== forward_bounded_searcher (N={args.N}, dm@{positions}, "
          f"rounds={args.rounds}, threshold-curve={len(threshold_curve)} rounds) ===")
    print(f"Total patterns:      {total_patterns}")
    print(f"Pruned:              {pruned_count} ({100*pruned_count/total_patterns:.2f}%)")
    print(f"Survived to {args.rounds}: {survived_count} ({100*survived_count/total_patterns:.2f}%)")
    print(f"Wall:                {wall:.3f}s")
    print(f"Min final HW (excl 0,0): {min_final_hw}  best dm: "
          f"({hex(best_dm[0]) if best_dm else '-'}, {hex(best_dm[1]) if best_dm else '-'})")

    if survival_per_round:
        print(f"\nPer-round death (threshold pruning):")
        for rr in sorted(survival_per_round.keys()):
            cnt = survival_per_round[rr]
            print(f"  round {rr:>3}: {cnt:>10} died ({100*cnt/total_patterns:.2f}%)")

    print(f"\nFinal HW histogram (survivors only, low end):")
    for hw, c in sorted(final_hw_distribution.items())[:8]:
        print(f"  HW={hw:>3}: {c}")

    if args.out_json:
        with open(args.out_json, "w") as f:
            json.dump({
                "N": args.N,
                "positions": positions,
                "rounds": args.rounds,
                "threshold_curve": {str(k): v for k, v in threshold_curve.items()},
                "total_patterns": total_patterns,
                "pruned_count": pruned_count,
                "survived_count": survived_count,
                "wall_seconds": round(wall, 3),
                "survival_per_round": dict(survival_per_round),
                "final_hw_distribution": dict(final_hw_distribution),
                "min_final_hw": min_final_hw,
                "best_dm": list(best_dm) if best_dm else None,
            }, f, indent=2)


if __name__ == "__main__":
    main()
