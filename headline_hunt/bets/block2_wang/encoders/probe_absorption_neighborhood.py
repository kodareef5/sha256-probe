#!/usr/bin/env python3
"""
probe_absorption_neighborhood.py - deterministic local probes around absorbers.

The stochastic absorber search found compact block-2 message pairs. This
tool asks a narrower question: for a saved candidate, do nearby bit flips
improve the final chain-output target distance?

It exhaustively scans all one-bit moves, and optionally all two-bit moves,
over the chosen active message words. In the default `--side m2` mode this
is small for compact absorbers: 5 active words -> 160 single moves and
12,720 two-bit moves. `--side both` also probes matching M1 moves.
`--mode common` probes common-mode XOR moves, where each selected bit is
flipped in both M1 and M2. This preserves the message-word XOR difference
for W0..15 while still changing the absolute block-2 messages. `--mode
add_common` probes paired modular +/- 2^bit moves, which are closer to the
additive structure of the SHA-256 message schedule.

Example:
    PYTHONPATH=. python3 probe_absorption_neighborhood.py bundle.json \
      --init-json results/search_artifacts/score86.json \
      --active-words 0,1,2,8,9 --radius 2 --out-json neighborhood.json
"""
import argparse
import itertools
import json
import os
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
)


MASK32 = 0xFFFFFFFF


def active_words_from_pair(M1, M2):
    return [i for i, (a, b) in enumerate(zip(M1, M2)) if a != b]


def flip_pair(M1, M2, flips):
    out1 = list(M1)
    out2 = list(M2)
    for item in flips:
        side, word, bit = item[:3]
        if side == "m1":
            out1[word] = (out1[word] ^ (1 << bit)) & MASK32
        elif side == "both":
            out1[word] = (out1[word] ^ (1 << bit)) & MASK32
            out2[word] = (out2[word] ^ (1 << bit)) & MASK32
        elif side == "add_both":
            sign = item[3]
            delta = (1 << bit) * sign
            out1[word] = (out1[word] + delta) & MASK32
            out2[word] = (out2[word] + delta) & MASK32
        else:
            out2[word] = (out2[word] ^ (1 << bit)) & MASK32
    return out1, out2


def score_pair(M1, M2, chain1_out, chain2_out, target_diff):
    _, chain1_after2 = compress(M1, chain1_out)
    _, chain2_after2 = compress(M2, chain2_out)
    final_diff = tuple(a ^ b for a, b in zip(chain1_after2, chain2_after2))
    return hw_tuple(d ^ t for d, t in zip(final_diff, target_diff)), final_diff


def schedule_diff_count(M1, M2):
    W1 = build_schedule(M1)
    W2 = build_schedule(M2)
    return sum(1 for a, b in zip(W1, W2) if a != b)


def describe_candidate(M1, M2, chain1_out, chain2_out, target_diff, flips,
                       base_score):
    score, final_diff = score_pair(M1, M2, chain1_out, chain2_out, target_diff)
    msg_hw, msg_words = message_stats(M1, M2)
    return {
        "score": score,
        "delta_score": score - base_score,
        "message_diff_hw": msg_hw,
        "nonzero_message_words": msg_words,
        "nonzero_schedule_words": schedule_diff_count(M1, M2),
        "flips": [
            {"side": item[0], "word": item[1], "bit": item[2],
             **({"sign": item[3]} if len(item) > 3 else {})}
            for item in flips
        ],
        "final_diff": hex_tuple(final_diff),
        "M1": [f"0x{x:08x}" for x in M1],
        "M2": [f"0x{x:08x}" for x in M2],
    }


def rank_key(candidate):
    return (
        candidate["score"],
        candidate["message_diff_hw"],
        candidate["nonzero_message_words"],
        candidate["nonzero_schedule_words"],
        len(candidate["flips"]),
    )


def keep_top(top, candidate, top_n):
    top.append(candidate)
    top.sort(key=rank_key)
    if len(top) > top_n:
        top.pop()


def move_iter(positions, radius):
    for r in range(1, radius + 1):
        for flips in itertools.combinations(positions, r):
            yield flips


def move_is_noop(flips):
    deltas = Counter()
    saw_raw = False
    for item in flips:
        if item[0] == "add_both":
            deltas[item[:3]] += item[3]
        else:
            saw_raw = True
    return not saw_raw and deltas and all(delta == 0 for delta in deltas.values())


def position_list(active_words, side):
    sides = ["m2"] if side == "m2" else ["m1"] if side == "m1" else ["m1", "m2"]
    return [
        (this_side, word, bit)
        for this_side in sides
        for word in active_words
        for bit in range(32)
    ]


def common_mode_positions(active_words):
    return [("both", word, bit) for word in active_words for bit in range(32)]


def additive_common_positions(active_words):
    return [
        ("add_both", word, bit, sign)
        for word in active_words
        for bit in range(32)
        for sign in (1, -1)
    ]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bundle", help="2blockcertpin/v1 trail bundle JSON")
    ap.add_argument("--init-json", required=True,
                    help="Search/subset artifact containing the candidate to probe")
    ap.add_argument("--active-words", default=None,
                    help="Comma/range list to probe; default is actual active words")
    ap.add_argument("--radius", type=int, default=2,
                    help="Maximum number of bit flips per move; use 1 or 2")
    ap.add_argument("--side", choices=["m2", "m1", "both"], default="m2",
                    help="Which side(s) to perturb in raw mode")
    ap.add_argument("--mode", choices=["raw", "common", "add_common"],
                    default="raw",
                    help="Raw XOR flips, common XOR flips, or paired modular adds")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--out-json", default=None)
    args = ap.parse_args()

    if args.radius < 1 or args.radius > 2:
        raise SystemExit("--radius currently supports only 1 or 2")
    if args.top < 1:
        raise SystemExit("--top must be positive")

    with open(args.bundle) as f:
        bundle = json.load(f)

    requested_active = (parse_active_words(args.active_words)
                        if args.active_words else None)
    M1, M2, init_score, init_obj = load_init_pair(args.init_json, requested_active)
    active_words = requested_active or active_words_from_pair(M1, M2)
    if not active_words:
        raise SystemExit("candidate has no active message words")

    chain1_out, chain2_out, working_diff, chain_diff = block2_context(bundle)
    target_diff = parse_target(bundle)
    base_score, base_final_diff = score_pair(M1, M2, chain1_out, chain2_out,
                                             target_diff)
    base_msg_hw, base_msg_words = message_stats(M1, M2)
    base_sched_words = schedule_diff_count(M1, M2)

    if args.mode == "common":
        positions = common_mode_positions(active_words)
    elif args.mode == "add_common":
        positions = additive_common_positions(active_words)
    else:
        positions = position_list(active_words, args.side)
    hist = Counter()
    by_radius = Counter()
    top = []
    evaluated = 0
    skipped_noop = 0
    improved = 0
    t0 = time.time()

    for flips in move_iter(positions, args.radius):
        if move_is_noop(flips):
            skipped_noop += 1
            continue
        trial_M1, trial_M2 = flip_pair(M1, M2, flips)
        candidate = describe_candidate(trial_M1, trial_M2, chain1_out,
                                       chain2_out, target_diff, flips,
                                       base_score)
        evaluated += 1
        hist[candidate["score"]] += 1
        by_radius[len(flips)] += 1
        if candidate["score"] < base_score:
            improved += 1
        keep_top(top, candidate, args.top)

    print("=== absorption neighborhood probe ===")
    print(f"Bundle:              {args.bundle}")
    print(f"Init JSON:           {args.init_json}")
    print(f"Active words:        {','.join(str(w) for w in active_words)}")
    print(f"Mode:                {args.mode}")
    if args.mode == "raw":
        side_label = args.side
    elif args.mode == "common":
        side_label = "both/common-xor"
    else:
        side_label = "both/common-add"
    print(f"Perturbed side:      {side_label}")
    print(f"Radius:              {args.radius}")
    print(f"Positions:           {len(positions)}")
    print(f"Candidates:          {evaluated}")
    print(f"Skipped no-op moves: {skipped_noop}")
    print(f"Runtime seconds:     {time.time() - t0:.3f}")
    print(f"Base score:          {base_score}")
    print(f"Base msg diff HW:    {base_msg_hw}")
    print(f"Base message words:  {base_msg_words}")
    print(f"Base schedule words: {base_sched_words}")
    print(f"Improving moves:     {improved}")
    print()
    print("Best moves:")
    print("rank  score  delta  msgHW  words  sched  flips")
    for i, candidate in enumerate(top, 1):
        flips = ",".join(
            f"CMW{f['word']}b{f['bit']}"
            if f["side"] == "both"
            else f"ADW{f['word']}b{f['bit']}{'+' if f.get('sign', 1) > 0 else '-'}"
            if f["side"] == "add_both"
            else f"{f['side'].upper()}W{f['word']}b{f['bit']}"
            for f in candidate["flips"]
        )
        print(f"{i:>4}  {candidate['score']:>5}  "
              f"{candidate['delta_score']:>5}  "
              f"{candidate['message_diff_hw']:>5}  "
              f"{candidate['nonzero_message_words']:>5}  "
              f"{candidate['nonzero_schedule_words']:>5}  {flips}")
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
                "active_words": active_words,
                "radius": args.radius,
                "mode": args.mode,
                "side": args.side,
                "positions": len(positions),
                "evaluated": evaluated,
                "skipped_noop": skipped_noop,
                "by_radius": dict(by_radius),
                "improving_moves": improved,
                "base": {
                    "score": base_score,
                    "final_diff": hex_tuple(base_final_diff),
                    "M1": [f"0x{x:08x}" for x in M1],
                    "M2": [f"0x{x:08x}" for x in M2],
                    "message_diff_hw": base_msg_hw,
                    "nonzero_message_words": base_msg_words,
                    "nonzero_schedule_words": base_sched_words,
                    "working_hw": hw_tuple(working_diff),
                    "chain_input_hw": hw_tuple(chain_diff),
                },
                "score_histogram": {
                    str(score): count for score, count in sorted(hist.items())
                },
                "top": top,
            }, f, indent=2)
        print(f"\nFull JSON: {args.out_json}", file=sys.stderr)


if __name__ == "__main__":
    main()
