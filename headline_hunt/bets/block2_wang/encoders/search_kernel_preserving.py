#!/usr/bin/env python3
"""
search_kernel_preserving.py — F321 structural fix to F315-F319.

F315-F319 mutated M2 freely on active words, allowing M2 to drift away from
the cascade-1 kernel pattern (bit-31 on M[0] and M[9] only). For a TRUE
cascade-1 collision attack, we must keep M2 = M1 ^ kernel rigid and mutate
M1 instead.

This script:
  - Loads (M1_init, kernel_diff) from yale F358-style init JSON.
  - Mutates M1 on active words (1, 2, 3, ..., not 0/9 which are kernel-pinned).
  - Each step: compute M2 = M1 ^ kernel_diff; evaluate atlas score.
  - Compare to F319's drift-allowed result.

Usage:
    python3 search_kernel_preserving.py --init-json yale_F358.json \
        --active-m1-words 1,2,3,8 \
        --restarts 8 --iterations 20000
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

from lib.sha256 import MASK
from headline_hunt.bets.block2_wang.encoders.search_schedule_space import (
    atlas_evaluate, atlas_score, parse_active_words
)


def mutate_M1_kernel_preserving(M1, kernel_diff, rng, active_m1_words,
                                 multibit_prob):
    """Mutate M1 on active_m1_words; M2 will be derived as M1 ^ kernel_diff."""
    M1_new = list(M1)
    use_multibit = rng.random() < multibit_prob
    idx = active_m1_words[rng.randrange(len(active_m1_words))]
    if not use_multibit:
        mode = rng.randrange(10)
        if mode < 5:
            M1_new[idx] ^= 1 << rng.randrange(32)
        elif mode < 8:
            M1_new[idx] ^= rng.getrandbits(32)
        else:
            M1_new[idx] = rng.getrandbits(32) & MASK
    else:
        mode = rng.randrange(20)
        if mode < 10:
            b1 = rng.randrange(32); b2 = rng.randrange(32)
            M1_new[idx] ^= (1 << b1) ^ (1 << b2)
        elif mode < 15:
            bits = rng.sample(range(32), 3)
            for b in bits:
                M1_new[idx] ^= 1 << b
        elif mode < 18:
            for _ in range(3):
                j = active_m1_words[rng.randrange(len(active_m1_words))]
                b = rng.randrange(32)
                M1_new[j] ^= 1 << b
        elif mode < 19:
            M1_new[idx] ^= rng.getrandbits(32)
        else:
            M1_new[idx] = rng.getrandbits(32) & MASK
    return M1_new


def compute_kernel_diff(M1_init, M2_init):
    """kernel_diff[i] = M1_init[i] ^ M2_init[i] for all i."""
    return [(m1 ^ m2) & MASK for m1, m2 in zip(M1_init, M2_init)]


def run_kernel_restart(M1_init, kernel_diff, active_m1_words, iterations, rng,
                        score_kwargs, anneal_floor=0.05, anneal_ceiling=0.8):
    M1 = list(M1_init)
    M2 = [(m1 ^ d) & MASK for m1, d in zip(M1, kernel_diff)]
    rec = atlas_evaluate(M1, M2)
    best_score = atlas_score(rec, **score_kwargs)
    best_rec = rec
    best_M1 = list(M1)
    cur_M1 = list(M1)
    cur_score = best_score
    accepts = 0
    chart_matches = 0
    chamber_hits = 0

    for it in range(iterations):
        prog = it / max(1, iterations - 1)
        multibit_prob = anneal_ceiling + (anneal_floor - anneal_ceiling) * prog

        cand_M1 = mutate_M1_kernel_preserving(cur_M1, kernel_diff, rng,
                                                active_m1_words, multibit_prob)
        cand_M2 = [(m1 ^ d) & MASK for m1, d in zip(cand_M1, kernel_diff)]
        cand_rec = atlas_evaluate(cand_M1, cand_M2)
        cand_score = atlas_score(cand_rec, **score_kwargs)
        accept = False
        if cand_score < cur_score:
            accept = True
        else:
            T = max(0.5, 5.0 * (1.0 - prog))
            delta = cand_score - cur_score
            if rng.random() < math.exp(-delta / T):
                accept = True
        if accept:
            cur_M1 = cand_M1
            cur_score = cand_score
            accepts += 1
            if cand_rec["chart_top2"] in (("dh","dCh"),("dCh","dh")):
                chart_matches += 1
            if (cand_rec["a57_xor_hw"] == 0 and
                cand_rec["D61_hw"] <= 4 and
                cand_rec["chart_top2"] in (("dh","dCh"),("dCh","dh"))):
                chamber_hits += 1
            if cand_score < best_score:
                best_score = cand_score
                best_rec = cand_rec
                best_M1 = list(cand_M1)
    best_M2 = [(m1 ^ d) & MASK for m1, d in zip(best_M1, kernel_diff)]
    return {
        "best_score": best_score,
        "best_rec": best_rec,
        "best_M1": [f"0x{w:08x}" for w in best_M1],
        "best_M2": [f"0x{w:08x}" for w in best_M2],
        "iterations": iterations,
        "accepts": accepts,
        "chart_matches": chart_matches,
        "chamber_hits": chamber_hits,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init-json", required=True)
    ap.add_argument("--restarts", type=int, default=8)
    ap.add_argument("--iterations", type=int, default=20000)
    ap.add_argument("--active-m1-words", default="1,2,3,4,5,6,7,8",
                    help="M1 word indices that can be mutated (avoid kernel "
                         "words 0 and 9 to preserve cascade-1 structure)")
    ap.add_argument("--seed", type=int, default=32100)
    ap.add_argument("--alpha", type=float, default=4.0)
    ap.add_argument("--beta", type=float, default=1.0)
    ap.add_argument("--gamma", type=float, default=8.0)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--anneal-ceiling", type=float, default=0.8)
    ap.add_argument("--anneal-floor",   type=float, default=0.05)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(args.init_json) as f:
        seed = json.load(f)
    M1_init = [int(x, 16) for x in seed["best"]["M1"]]
    M2_init = [int(x, 16) for x in seed["best"]["M2_kernel"]]
    kernel_diff = compute_kernel_diff(M1_init, M2_init)
    nonzero_kernel = [(i, f"0x{kernel_diff[i]:08x}") for i in range(16)
                      if kernel_diff[i] != 0]
    print(f"# kernel_diff nonzero words: {nonzero_kernel}")

    init_rec = atlas_evaluate(M1_init, M2_init)
    print(f"# kernel-preserving init: a57={init_rec['a57_xor_hw']} "
          f"D61={init_rec['D61_hw']} chart={init_rec['chart_top2']}")

    active_m1_words = parse_active_words(args.active_m1_words)
    # Sanity: ensure none of the active M1 words are kernel-diff words
    kernel_words = [i for i in range(16) if kernel_diff[i] != 0]
    overlap = set(active_m1_words) & set(kernel_words)
    if overlap:
        print(f"# WARNING: active_m1_words {sorted(overlap)} overlap kernel_words "
              f"{kernel_words}; mutating M1 there changes M2 too (still cascade-1 "
              f"compatible since kernel is XOR-symmetric)")

    rng = random.Random(args.seed)
    score_kwargs = dict(atlas_alpha=args.alpha, atlas_beta=args.beta,
                         atlas_gamma=args.gamma, atlas_delta=args.delta)

    t0 = time.time()
    results = []
    for r in range(args.restarts):
        # Each restart starts from a slightly perturbed M1
        M1_pert = list(M1_init)
        for _ in range(rng.randint(1, 3)):
            idx = active_m1_words[rng.randrange(len(active_m1_words))]
            M1_pert[idx] ^= 1 << rng.randrange(32)
        rs = run_kernel_restart(M1_pert, kernel_diff, active_m1_words,
                                 args.iterations, rng, score_kwargs,
                                 args.anneal_floor, args.anneal_ceiling)
        rs["restart"] = r
        results.append(rs)
        rec = rs["best_rec"]
        print(f"  restart {r}: best_score={rs['best_score']:.2f} "
              f"a57={rec['a57_xor_hw']} D61={rec['D61_hw']} "
              f"chart={rec['chart_top2']} tail63={rec['tail63_state_diff_hw']} "
              f"accepts={rs['accepts']} chart_matches={rs['chart_matches']} "
              f"chamber_hits={rs['chamber_hits']}")

    elapsed = time.time() - t0
    print(f"# wall: {elapsed:.1f}s")
    summary = {
        "args": vars(args),
        "kernel_diff_words": kernel_words,
        "init_rec": init_rec,
        "active_m1_words": active_m1_words,
        "wall_seconds": elapsed,
        "restarts": results,
        "best_overall_score": min(r["best_score"] for r in results),
        "best_overall_a57": min(r["best_rec"]["a57_xor_hw"] for r in results),
        "best_overall_D61": min(r["best_rec"]["D61_hw"] for r in results),
        "any_chamber_hit": any(r["chamber_hits"] > 0 for r in results),
    }
    with open(args.out, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"# wrote {args.out}")


if __name__ == "__main__":
    main()
