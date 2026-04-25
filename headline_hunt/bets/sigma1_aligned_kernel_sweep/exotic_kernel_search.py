#!/usr/bin/env python3
"""
exotic_kernel_search.py — search for cascade-eligible candidates with
non-(0,9) word-pair kernels.

Memory hint (from project_exotic_kernels.md): at N=8, non-(0,9) word pairs
yield collisions: (0,14)=500, (0,1)=477, single-word=321. Whether these
extend to N=32 cascade-eligibility is open.

A cascade-eligible candidate satisfies da[56] == 0 between the two
pre-images differing by `delta` at message-word positions {i, j} (or just
{i} for single-word kernels). Cascade-1 then zeros da[57] via W[57] offset.

Usage:
    python3 exotic_kernel_search.py --word-pair 0,1 --bit 31 --fill 0xffffffff --trials 1000000
    python3 exotic_kernel_search.py --word-pair 0,14 --bit 19 --fill 0x55555555 --trials 1000000
    python3 exotic_kernel_search.py --single-word 0 --bit 31 --fill 0xffffffff --trials 1000000

Output (JSON Lines):
    {"m0":"0x...","kernel":{"word_pair":[i,j],"bit":B},"a56_match":true,"hw_other_bits":N}

Prints a summary at end: trials, candidates found, ratio.
"""
import argparse
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
from lib.sha256 import precompute_state, MASK


def search(word_pair, bit, fill, trials, seed, m0_position=0):
    """word_pair: tuple (i, j) of word indices (j=None for single-word).
    bit: difference bit position (0..31).
    fill: word fill value for M[1..15] (excluding kernel positions).
    """
    rng = random.Random(seed)
    delta = 1 << bit
    found = []

    for trial in range(trials):
        m0 = rng.randrange(2**32)
        M1 = [fill] * 16
        M2 = list(M1)
        M1[m0_position] = m0
        M2[m0_position] = m0 ^ delta
        # Apply delta to second word of pair
        if word_pair[1] is not None:
            j = word_pair[1]
            M2[j] = M1[j] ^ delta

        s1, _ = precompute_state(M1)
        s2, _ = precompute_state(M2)
        if s1[0] == s2[0]:  # da[56] == 0 == cascade-eligible
            found.append({
                "m0": f"0x{m0:08x}",
                "kernel": {"word_pair": list(word_pair), "bit": bit, "fill": f"0x{fill:08x}"},
                "trial": trial,
                "a56": f"0x{s1[0]:08x}",
                "diff_other_regs_xor_hw": sum(bin(s1[i] ^ s2[i]).count("1") for i in range(1, 8)),
            })
    return found


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--word-pair", help="i,j (e.g., 0,1 or 0,14)")
    ap.add_argument("--single-word", type=int, help="single word index (e.g., 0)")
    ap.add_argument("--bit", type=int, default=31)
    ap.add_argument("--fill", default="0xffffffff")
    ap.add_argument("--trials", type=int, default=1000000)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    if args.word_pair:
        i, j = (int(x) for x in args.word_pair.split(","))
        wp = (i, j)
        label = f"({i},{j})"
    elif args.single_word is not None:
        wp = (args.single_word, None)
        label = f"single@{args.single_word}"
    else:
        print("ERROR: specify --word-pair or --single-word", file=sys.stderr)
        sys.exit(1)

    fill = int(args.fill, 16)

    print(f"Searching kernel={label} bit={args.bit} fill={args.fill} trials={args.trials}",
          file=sys.stderr)
    found = search(wp, args.bit, fill, args.trials, args.seed)
    print(f"Found {len(found)} cascade-eligible candidates", file=sys.stderr)
    if found:
        # Sort by smallest "other registers diff" (fewer ripple bits = simpler)
        found.sort(key=lambda f: f["diff_other_regs_xor_hw"])
        for c in found[:20]:
            print(json.dumps(c))
    return 0 if found else 1


if __name__ == "__main__":
    sys.exit(main())
