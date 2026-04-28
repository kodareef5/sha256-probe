#!/usr/bin/env python3
"""
resample_fixed_diff_absorber.py - common-mode resampling for absorbers.

Local bit probes showed the score-86 absorber is isolated under small moves.
This tool keeps a saved candidate's message XOR difference fixed while
resampling absolute block-2 message words. That tests whether the useful
object is mainly the M1/M2 difference pattern, or the exact absolute words.

Modes:
- active: resample M1 only at active difference words.
- all:    resample all 16 M1 words; M2 is always M1 xor saved_diff.

Example:
    PYTHONPATH=. python3 resample_fixed_diff_absorber.py bundle.json \
      --init-json results/search_artifacts/score86.json \
      --samples 100000 --mode all --out-json fixed_diff_resample.json
"""
import argparse
import json
import os
import random
import sys
import time
from collections import Counter


REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)

from headline_hunt.bets.block2_wang.encoders.search_block2_absorption import (
    build_schedule,
    block2_context,
    compress,
    hex_tuple,
    hw_tuple,
    load_init_pair,
    message_stats,
    parse_active_words,
    parse_target,
    xor_tuple,
)


def score_pair(M1, M2, chain1_out, chain2_out, target_diff):
    _, chain1_after2 = compress(M1, chain1_out)
    _, chain2_after2 = compress(M2, chain2_out)
    final_diff = xor_tuple(chain1_after2, chain2_after2)
    return hw_tuple(d ^ t for d, t in zip(final_diff, target_diff)), final_diff


def schedule_diff_count(M1, M2):
    W1 = build_schedule(M1)
    W2 = build_schedule(M2)
    return sum(1 for a, b in zip(W1, W2) if a != b)


def active_words_from_diff(diffs):
    return [i for i, d in enumerate(diffs) if d]


def make_candidate(base_M1, diffs, rng, mode, active_words):
    M1 = list(base_M1)
    if mode == "all":
        words = range(16)
    else:
        words = active_words
    for word in words:
        M1[word] = rng.getrandbits(32)
    M2 = [(m1 ^ d) & 0xFFFFFFFF for m1, d in zip(M1, diffs)]
    return M1, M2


def describe(M1, M2, chain1_out, chain2_out, target_diff, base_score):
    score, final_diff = score_pair(M1, M2, chain1_out, chain2_out, target_diff)
    msg_hw, msg_words = message_stats(M1, M2)
    return {
        "score": score,
        "delta_score": score - base_score,
        "message_diff_hw": msg_hw,
        "nonzero_message_words": msg_words,
        "nonzero_schedule_words": schedule_diff_count(M1, M2),
        "final_diff": hex_tuple(final_diff),
        "M1": [f"0x{x:08x}" for x in M1],
        "M2": [f"0x{x:08x}" for x in M2],
    }


def rank_key(candidate):
    return (
        candidate["score"],
        candidate["message_diff_hw"],
        candidate["nonzero_schedule_words"],
    )


def keep_top(top, candidate, top_n):
    top.append(candidate)
    top.sort(key=rank_key)
    if len(top) > top_n:
        top.pop()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bundle", help="2blockcertpin/v1 trail bundle JSON")
    ap.add_argument("--init-json", required=True)
    ap.add_argument("--active-words", default=None,
                    help="Optional compatible active words for loading candidate")
    ap.add_argument("--mode", choices=["active", "all"], default="all")
    ap.add_argument("--samples", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--out-json", default=None)
    args = ap.parse_args()

    if args.samples < 1:
        raise SystemExit("--samples must be positive")
    if args.top < 1:
        raise SystemExit("--top must be positive")

    requested_active = (parse_active_words(args.active_words)
                        if args.active_words else None)
    base_M1, base_M2, init_score, init_obj = load_init_pair(
        args.init_json, requested_active
    )
    diffs = [a ^ b for a, b in zip(base_M1, base_M2)]
    active_words = active_words_from_diff(diffs)

    with open(args.bundle) as f:
        bundle = json.load(f)
    chain1_out, chain2_out, working_diff, chain_diff = block2_context(bundle)
    target_diff = parse_target(bundle)
    base = describe(base_M1, base_M2, chain1_out, chain2_out, target_diff,
                    init_score)
    base_score = base["score"]

    rng = random.Random(args.seed)
    hist = Counter()
    top = [base]
    improved = 0
    t0 = time.time()
    for _ in range(args.samples):
        M1, M2 = make_candidate(base_M1, diffs, rng, args.mode, active_words)
        candidate = describe(M1, M2, chain1_out, chain2_out, target_diff,
                             base_score)
        hist[candidate["score"]] += 1
        if candidate["score"] < base_score:
            improved += 1
        keep_top(top, candidate, args.top)

    print("=== fixed-diff absorber resampling ===")
    print(f"Bundle:              {args.bundle}")
    print(f"Init JSON:           {args.init_json}")
    print(f"Mode:                {args.mode}")
    print(f"Active diff words:   {','.join(str(w) for w in active_words)}")
    print(f"Samples:             {args.samples}")
    print(f"Runtime seconds:     {time.time() - t0:.3f}")
    print(f"Base score:          {base_score}")
    print(f"Base msg diff HW:    {base['message_diff_hw']}")
    print(f"Improving samples:   {improved}")
    print()
    print("Best candidates:")
    print("rank  score  delta  msgHW  words  sched")
    for i, candidate in enumerate(top, 1):
        print(f"{i:>4}  {candidate['score']:>5}  "
              f"{candidate['delta_score']:>5}  "
              f"{candidate['message_diff_hw']:>5}  "
              f"{candidate['nonzero_message_words']:>5}  "
              f"{candidate['nonzero_schedule_words']:>5}")
    print()
    print("Best score counts:")
    for score, count in sorted(hist.items())[:12]:
        print(f"  score {score:>3}: {count}")

    if args.out_json:
        with open(args.out_json, "w") as f:
            json.dump({
                "bundle": args.bundle,
                "init_json": args.init_json,
                "init_score": init_score,
                "init_objective": init_obj,
                "mode": args.mode,
                "samples": args.samples,
                "seed": args.seed,
                "active_words": active_words,
                "message_diffs": [f"0x{x:08x}" for x in diffs],
                "working_hw": hw_tuple(working_diff),
                "chain_input_hw": hw_tuple(chain_diff),
                "improving_samples": improved,
                "score_histogram": {
                    str(score): count for score, count in sorted(hist.items())
                },
                "base": base,
                "top": top,
            }, f, indent=2)
        print(f"\nFull JSON: {args.out_json}", file=sys.stderr)


if __name__ == "__main__":
    main()
