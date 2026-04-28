#!/usr/bin/env python3
"""
search_block2_absorption.py - stochastic search for block-2 message absorption.

This is intentionally broader than the exact_diff sweep/beam tools. Instead
of pinning a small number of W2 schedule words, it fixes one random block-2
message for side 1, then searches side 2's 16 message words to minimize the
final chain-output distance to the bundle target.

It is not a proof tool. It is a cheap design probe:
- If local search cannot beat random/no-diff baselines, simple block-2
  message freedom is not enough.
- If it repeatedly finds much lower target distances, those messages and
  induced W2 diffs become trail-design hints.

Usage:
    python3 search_block2_absorption.py bit3_HW55_naive_blocktwo.json
    python3 search_block2_absorption.py bundle.json --restarts 8 --iterations 20000
    python3 search_block2_absorption.py bundle.json --active-words 0,1,8,9
"""
import argparse
import json
import math
import os
import random
import sys
import time


REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)

from headline_hunt.bets.block2_wang.encoders.simulate_2block_absorption import (
    REGS,
    MASK,
    build_schedule,
    compress,
    hex_tuple,
    hw_tuple,
    reconstruct_block1,
    xor_tuple,
)


def parse_target(bundle):
    target = bundle["block2"].get("target_diff_at_round_N", {})
    return tuple(int(target.get(f"diff_{r}", "0x0"), 16) for r in REGS)


def block2_context(bundle):
    b1 = bundle["block1"]
    state1_63, state2_63, chain1_out, chain2_out = reconstruct_block1(b1)
    working_diff = xor_tuple(state1_63, state2_63)
    chain_diff = xor_tuple(chain1_out, chain2_out)
    return chain1_out, chain2_out, working_diff, chain_diff


def candidate_words(working_diff, chain_diff):
    words = []
    for x in list(working_diff) + list(chain_diff):
        if x != 0 and x not in words:
            words.append(x)
    return words


def parse_active_words(spec):
    if spec == "all":
        return list(range(16))
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = [int(x) for x in part.split("-", 1)]
            out.extend(range(lo, hi + 1))
        else:
            out.append(int(part))
    out = sorted(set(out))
    if not out or any(i < 0 or i > 15 for i in out):
        raise ValueError("--active-words must name message word indices in [0,15]")
    return out


def enforce_active_words(M1, M2, active_words):
    active = set(active_words)
    M2 = list(M2)
    for i in range(16):
        if i not in active:
            M2[i] = M1[i]
    return M2


def rand_block(rng):
    return [rng.getrandbits(32) for _ in range(16)]


def score_message(M2, fixed_chain1_after2, chain2_out, target_diff):
    _, chain2_after2 = compress(M2, chain2_out)
    diff = xor_tuple(fixed_chain1_after2, chain2_after2)
    return hw_tuple(d ^ t for d, t in zip(diff, target_diff)), diff


def message_stats(M1, M2):
    diffs = [m1 ^ m2 for m1, m2 in zip(M1, M2)]
    return hw_tuple(diffs), sum(1 for d in diffs if d)


def objective(target_distance, M1, M2, args):
    msg_hw, active_words = message_stats(M1, M2)
    return (target_distance
            + args.hw_penalty * msg_hw
            + args.word_penalty * active_words)


def mutate_message(M, rng, hints, active_words):
    M2 = list(M)
    mode = rng.randrange(10)
    idx = active_words[rng.randrange(len(active_words))]
    if mode < 5:
        bit = rng.randrange(32)
        M2[idx] ^= 1 << bit
    elif mode < 7 and hints:
        M2[idx] ^= hints[rng.randrange(len(hints))]
    elif mode < 9:
        mask = rng.getrandbits(32)
        M2[idx] ^= mask
    else:
        M2[idx] = rng.getrandbits(32)
    M2[idx] &= MASK
    return M2


def polish_message(M, fixed_chain1_after2, chain2_out, target_diff, active_words):
    best = list(M)
    best_score, best_diff = score_message(best, fixed_chain1_after2, chain2_out,
                                          target_diff)
    improved = True
    while improved:
        improved = False
        for idx in active_words:
            for bit in range(32):
                trial = list(best)
                trial[idx] ^= 1 << bit
                s, d = score_message(trial, fixed_chain1_after2, chain2_out,
                                     target_diff)
                if s < best_score:
                    best = trial
                    best_score = s
                    best_diff = d
                    improved = True
    return best, best_score, best_diff


def active_words_in_result(result):
    M1 = [int(x, 16) for x in result["M1"]]
    M2 = [int(x, 16) for x in result["M2"]]
    return {i for i, (a, b) in enumerate(zip(M1, M2)) if a != b}


def load_init_pair(path, active_words=None):
    with open(path) as f:
        data = json.load(f)
    results = list(data.get("results", []))
    results.extend(subset["best"] for subset in data.get("subsets", []))
    if active_words is not None:
        active = set(active_words)
        compatible = [
            result for result in results
            if active_words_in_result(result).issubset(active)
        ]
        if compatible:
            results = compatible
    if not results:
        raise ValueError(f"no results in {path}")
    results = sorted(results, key=lambda r: r.get("objective", r["score"]))
    best = results[0]
    return (
        [int(x, 16) for x in best["M1"]],
        [int(x, 16) for x in best["M2"]],
        best.get("score"),
        best.get("objective", best.get("score")),
    )


def run_restart(bundle, restart_idx, args, hints, active_words, init_pair=None):
    rng = random.Random(args.seed + restart_idx)
    chain1_out, chain2_out, working_diff, chain_diff = block2_context(bundle)
    target_diff = parse_target(bundle)

    if init_pair is not None:
        M1 = list(init_pair[0])
        current = enforce_active_words(M1, init_pair[1], active_words)
        for _ in range(args.init_kicks):
            current = mutate_message(current, rng, hints, active_words)
    elif args.anchor == "zero":
        M1 = [0] * 16
    else:
        M1 = rand_block(rng)
    _, fixed_chain1_after2 = compress(M1, chain1_out)

    if init_pair is None:
        if args.start == "same":
            current = list(M1)
        elif args.start == "zero":
            current = [0] * 16
        else:
            current = rand_block(rng)
        current = enforce_active_words(M1, current, active_words)

    current_score, current_diff = score_message(current, fixed_chain1_after2,
                                                chain2_out, target_diff)
    current_obj = objective(current_score, M1, current, args)
    best = list(current)
    best_score = current_score
    best_diff = current_diff
    best_obj = current_obj

    t0 = time.time()
    for i in range(args.iterations):
        temp_frac = i / max(1, args.iterations - 1)
        temp = args.temp_start * ((args.temp_end / args.temp_start) ** temp_frac)
        trial = mutate_message(current, rng, hints, active_words)
        trial_score, trial_diff = score_message(trial, fixed_chain1_after2,
                                                chain2_out, target_diff)
        trial_obj = objective(trial_score, M1, trial, args)
        accept = trial_obj <= current_obj
        if not accept and temp > 0:
            accept = rng.random() < math.exp((current_obj - trial_obj) / temp)
        if accept:
            current = trial
            current_score = trial_score
            current_diff = trial_diff
            current_obj = trial_obj
        if trial_obj < best_obj:
            best = trial
            best_score = trial_score
            best_diff = trial_diff
            best_obj = trial_obj
        if args.progress and (i + 1) % args.progress == 0:
            print(f"restart={restart_idx} iter={i + 1} current={current_score} "
                  f"current_obj={current_obj:.3f} best={best_score} "
                  f"best_obj={best_obj:.3f}", file=sys.stderr)

    if args.polish:
        best, best_score, best_diff = polish_message(best, fixed_chain1_after2,
                                                     chain2_out, target_diff,
                                                     active_words)
        best_obj = objective(best_score, M1, best, args)

    W1 = build_schedule(M1)
    W2 = build_schedule(best)
    dw_nonzero = [
        {"round": i, "diff": f"0x{W1[i] ^ W2[i]:08x}"}
        for i in range(64) if (W1[i] ^ W2[i]) != 0
    ]

    return {
        "restart": restart_idx,
        "score": best_score,
        "objective": round(best_obj, 6),
        "final_diff": hex_tuple(best_diff),
        "M1": [f"0x{x:08x}" for x in M1],
        "M2": [f"0x{x:08x}" for x in best],
        "message_diff_hw": hw_tuple(m1 ^ m2 for m1, m2 in zip(M1, best)),
        "nonzero_message_words": sum(1 for m1, m2 in zip(M1, best) if m1 != m2),
        "nonzero_schedule_words": len(dw_nonzero),
        "schedule_diffs": dw_nonzero,
        "wall_seconds": round(time.time() - t0, 3),
        "working_hw": hw_tuple(working_diff),
        "chain_input_hw": hw_tuple(chain_diff),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bundle", help="2blockcertpin/v1 trail bundle JSON")
    ap.add_argument("--restarts", type=int, default=4)
    ap.add_argument("--iterations", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--anchor", choices=["random", "zero"], default="random",
                    help="How to choose side-1 block-2 message")
    ap.add_argument("--start", choices=["same", "random", "zero"], default="same",
                    help="Initial side-2 block-2 message")
    ap.add_argument("--temp-start", type=float, default=2.5)
    ap.add_argument("--temp-end", type=float, default=0.05)
    ap.add_argument("--hw-penalty", type=float, default=0.0,
                    help="Objective penalty per active message-diff bit")
    ap.add_argument("--word-penalty", type=float, default=0.0,
                    help="Objective penalty per active message word")
    ap.add_argument("--polish", action="store_true",
                    help="Run greedy single-bit descent after each restart")
    ap.add_argument("--progress", type=int, default=0,
                    help="Print progress every N iterations per restart")
    ap.add_argument("--out-json", default=None)
    ap.add_argument("--init-json", default=None,
                    help="Use the best result from a previous search JSON as restart 0")
    ap.add_argument("--init-use", choices=["first", "all"], default="first",
                    help="Use --init-json for only restart 0, or for every restart")
    ap.add_argument("--init-kicks", type=int, default=0,
                    help="Apply this many random mutations to each seeded restart")
    ap.add_argument("--active-words", default="all",
                    help="Comma/range list of side-2 message words allowed to differ, or 'all'")
    args = ap.parse_args()

    with open(args.bundle) as f:
        bundle = json.load(f)

    chain1_out, chain2_out, working_diff, chain_diff = block2_context(bundle)
    target_diff = parse_target(bundle)
    hints = candidate_words(working_diff, chain_diff)
    active_words = parse_active_words(args.active_words)
    init_pair = load_init_pair(args.init_json, active_words) if args.init_json else None
    if init_pair:
        print(f"loaded init candidate: score={init_pair[2]} "
              f"objective={init_pair[3]}", file=sys.stderr)

    zero_M = [0] * 16
    _, zero_chain1_after2 = compress(zero_M, chain1_out)
    zero_score, _ = score_message(zero_M, zero_chain1_after2, chain2_out,
                                  target_diff)

    results = []
    for r in range(args.restarts):
        this_init = init_pair if (r == 0 or args.init_use == "all") else None
        this_result = run_restart(bundle, r, args, hints, active_words,
                                  init_pair=this_init)
        results.append(this_result)
        results.sort(key=lambda x: x["objective"])
        print(f"restart {r}: best_score={results[0]['score']} "
              f"best_obj={results[0]['objective']:.3f} "
              f"this_score={this_result['score']} "
              f"this_obj={this_result['objective']:.3f}", file=sys.stderr)

    best = results[0]

    print("=== block-2 absorption local search ===")
    print(f"Bundle:              {args.bundle}")
    print(f"Restarts:            {args.restarts}")
    print(f"Iterations/restart:  {args.iterations}")
    print(f"Anchor/start:        {args.anchor}/{args.start}")
    print(f"Active words:        {','.join(str(i) for i in active_words)}")
    print(f"Penalties hw/word:   {args.hw_penalty}/{args.word_penalty}")
    print(f"Block1 working HW:   {hw_tuple(working_diff)}")
    print(f"Block2 chain HW:     {hw_tuple(chain_diff)}")
    print(f"Zero/zero baseline:  {zero_score}")
    print(f"Best objective:      {best['objective']:.3f}")
    print(f"Best target distance:{best['score']}")
    print(f"Best msg diff HW:    {best['message_diff_hw']}")
    print(f"Nonzero msg words:   {best['nonzero_message_words']}")
    print(f"Nonzero W diffs:     {best['nonzero_schedule_words']}")
    print()
    print("Top schedule diffs:")
    for entry in best["schedule_diffs"][:20]:
        print(f"  W[{entry['round']:02d}] diff {entry['diff']}")

    if args.out_json:
        with open(args.out_json, "w") as f:
            json.dump({
                "bundle": args.bundle,
                "args": vars(args),
                "active_words": active_words,
                "zero_baseline_score": zero_score,
                "results": results,
            }, f, indent=2)
        print(f"\nFull JSON: {args.out_json}", file=sys.stderr)


if __name__ == "__main__":
    main()
