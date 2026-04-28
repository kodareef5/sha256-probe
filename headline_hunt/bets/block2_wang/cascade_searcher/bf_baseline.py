#!/usr/bin/env python3
"""
bf_baseline.py — brute-force enumerator at mini-SHA-256 small N.

Establishes the benchmark the custom cascade-equation searcher must
beat (or match while providing structural insight). See SPEC.md.

For each (N, dm-pattern), enumerates the full dm space restricted to
two cascade-driving positions (default dm[0] and dm[9]), computes
mini-SHA-256(M) and mini-SHA-256(M XOR dm), tallies the residual
state-diff HW at round 63.

Reports:
  - Collision count (residual HW = 0)
  - Near-residual HW histogram
  - Wall time
  - Top-K dm-patterns by smallest residual HW
"""
import argparse
import json
import sys
import time
from collections import Counter


# Mini-SHA-256 primitives parameterized by N
def mini_sha_primitives(N):
    MASK = (1 << N) - 1

    def ror(x, k):
        return ((x >> k) | (x << (N - k))) & MASK

    # SHA-256 standard rotation amounts. At small N, some collide
    # (e.g., N=8: ror by 18 mod 8 = 2 etc.), which is the standard
    # mini-SHA convention used elsewhere in the project.
    def Sigma0(a):
        return ror(a, 2 % N) ^ ror(a, 13 % N) ^ ror(a, 22 % N)

    def Sigma1(e):
        return ror(e, 6 % N) ^ ror(e, 11 % N) ^ ror(e, 25 % N)

    def sigma0(x):
        # rotate by 7, 18; shift by 3
        return ror(x, 7 % N) ^ ror(x, 18 % N) ^ ((x >> (3 % N)) & MASK)

    def sigma1(x):
        return ror(x, 17 % N) ^ ror(x, 19 % N) ^ ((x >> (10 % N)) & MASK)

    def Ch(e, f, g):
        return ((e & f) ^ ((~e) & g)) & MASK

    def Maj(a, b, c):
        return ((a & b) ^ (a & c) ^ (b & c)) & MASK

    return MASK, ror, Sigma0, Sigma1, sigma0, sigma1, Ch, Maj


# SHA-256 round constants K (truncated to N bits)
K_FULL = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
]

IV_FULL = [
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
]


def compress_to_round(M, N, num_rounds=64):
    """Run mini-SHA at N-bit width through num_rounds rounds. Returns final state."""
    MASK, ror, Sigma0, Sigma1, sigma0, sigma1, Ch, Maj = mini_sha_primitives(N)

    K_N = [k & MASK for k in K_FULL]
    IV_N = [iv & MASK for iv in IV_FULL]

    W = [0] * 64
    for i in range(16):
        W[i] = M[i] & MASK
    for i in range(16, 64):
        W[i] = (sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]) & MASK

    a, b, c, d, e, f, g, h = IV_N
    for r in range(num_rounds):
        T1 = (h + Sigma1(e) + Ch(e, f, g) + K_N[r] + W[r]) & MASK
        T2 = (Sigma0(a) + Maj(a, b, c)) & MASK
        h = g; g = f; f = e
        e = (d + T1) & MASK
        d = c; c = b; b = a
        a = (T1 + T2) & MASK

    return (a, b, c, d, e, f, g, h)


def hw_state_diff(s1, s2):
    """Sum of Hamming weights of XOR-diffs across the 8 register state."""
    return sum(bin(a ^ b).count('1') for a, b in zip(s1, s2))


def enumerate_baseline(N, m0_anchor, dm_positions, num_rounds=64,
                        top_k=20, sample_progress=False):
    """
    Enumerate dm restricted to positions in dm_positions (typically [0, 9]
    for cascade-1). For each dm pattern, compute residual HW at round
    num_rounds. Returns histogram + top-K results + collision count.
    """
    if len(dm_positions) > 2:
        raise ValueError("baseline restricted to ≤2 dm positions for tractability")

    span = (1 << N)
    total_patterns = span ** len(dm_positions)
    print(f"[N={N}] Enumerating {total_patterns} dm patterns "
          f"(positions={dm_positions}, rounds={num_rounds})...",
          file=sys.stderr)

    M = [m0_anchor[i] for i in range(16)]

    histogram = Counter()
    collision_count = 0
    top_results = []  # (hw, dm_tuple)

    t0 = time.time()
    progress_step = max(1, total_patterns // 20)

    if len(dm_positions) == 1:
        p = dm_positions[0]
        for d0 in range(span):
            M2 = list(M); M2[p] = (M[p] ^ d0) & ((1 << N) - 1)
            s1 = compress_to_round(M, N, num_rounds)
            s2 = compress_to_round(M2, N, num_rounds)
            h = hw_state_diff(s1, s2)
            histogram[h] += 1
            if h == 0 and d0 != 0:
                collision_count += 1
            if d0 != 0:
                top_results.append((h, (d0,)))
                top_results.sort()
                top_results = top_results[:top_k]
    elif len(dm_positions) == 2:
        p1, p2 = dm_positions
        n_done = 0
        for d1 in range(span):
            for d2 in range(span):
                M2 = list(M)
                M2[p1] = (M[p1] ^ d1) & ((1 << N) - 1)
                M2[p2] = (M[p2] ^ d2) & ((1 << N) - 1)
                s1 = compress_to_round(M, N, num_rounds)
                s2 = compress_to_round(M2, N, num_rounds)
                h = hw_state_diff(s1, s2)
                histogram[h] += 1
                if h == 0 and (d1 != 0 or d2 != 0):
                    collision_count += 1
                if d1 != 0 or d2 != 0:
                    top_results.append((h, (d1, d2)))
                    if len(top_results) > top_k * 4:
                        top_results.sort()
                        top_results = top_results[:top_k]
                n_done += 1
                if sample_progress and n_done % progress_step == 0:
                    print(f"  {n_done}/{total_patterns} "
                          f"({100*n_done/total_patterns:.0f}%) "
                          f"min HW so far={min(histogram.keys()) if histogram else '?'}",
                          file=sys.stderr)
        top_results.sort()
        top_results = top_results[:top_k]
    wall = time.time() - t0

    return {
        "N": N,
        "dm_positions": dm_positions,
        "num_rounds": num_rounds,
        "total_patterns": total_patterns,
        "wall_seconds": round(wall, 3),
        "collision_count": collision_count,
        "histogram": dict(sorted(histogram.items())),
        "top_k_smallest_residual": [
            {"residual_hw": h, "dm": list(d)} for h, d in top_results
        ],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--N", type=int, required=True, help="Mini-SHA bit width")
    ap.add_argument("--positions", default="0,9",
                    help="Comma-separated dm positions to enumerate (default 0,9)")
    ap.add_argument("--rounds", type=int, default=64,
                    help="Number of rounds (default 64 = full SHA-256)")
    ap.add_argument("--m0", default="zero",
                    help="m0 anchor: 'zero' or comma-separated 16 hex words")
    ap.add_argument("--top-k", type=int, default=20)
    ap.add_argument("--progress", action="store_true",
                    help="Print progress every 5%")
    ap.add_argument("--out-json", default=None,
                    help="Write full result to this JSON file")
    args = ap.parse_args()

    if args.m0 == "zero":
        m0 = [0] * 16
    else:
        m0 = [int(x, 16) for x in args.m0.split(",")]
        if len(m0) != 16:
            print(f"ERROR: --m0 must be 16 hex words, got {len(m0)}", file=sys.stderr)
            sys.exit(2)

    positions = [int(p) for p in args.positions.split(",")]
    if any(p < 0 or p > 15 for p in positions):
        print(f"ERROR: positions must be in [0,15]", file=sys.stderr)
        sys.exit(2)

    result = enumerate_baseline(
        args.N, m0, positions, num_rounds=args.rounds,
        top_k=args.top_k, sample_progress=args.progress,
    )

    print(f"\n=== bf_baseline (N={result['N']}, "
          f"dm@{result['dm_positions']}, rounds={result['num_rounds']}) ===")
    print(f"Total patterns:     {result['total_patterns']}")
    print(f"Wall:               {result['wall_seconds']}s")
    print(f"Collisions (HW=0):  {result['collision_count']}")
    print(f"\nResidual HW histogram (top 12 buckets):")
    for h, c in list(result["histogram"].items())[:12]:
        bar = "#" * min(60, max(1, int(60 * c / result['total_patterns'])))
        print(f"  HW={h:>3}: {c:>10}  {bar}")
    print(f"\nTop-{args.top_k} smallest residuals:")
    for entry in result["top_k_smallest_residual"][:args.top_k]:
        dm_hex = ",".join(f"0x{d:x}" for d in entry["dm"])
        print(f"  HW={entry['residual_hw']:>3}  dm=({dm_hex})")

    if args.out_json:
        with open(args.out_json, "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nFull result: {args.out_json}", file=sys.stderr)


if __name__ == "__main__":
    main()
