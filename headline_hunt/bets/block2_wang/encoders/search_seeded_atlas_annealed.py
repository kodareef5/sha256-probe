#!/usr/bin/env python3
"""
search_seeded_atlas_annealed.py — F318 annealed mutator combining multibit
(escape) + 1-bit (fine descent) over the iteration timeline.

F317 showed multibit moves give 8/8 chamber-chart coverage (+73% chart
matches) but worse final a57 (6 vs F315's 4) because moves are too coarse
for fine descent. F315 (1-bit) had finer descent but stuck in non-chamber
chart pockets (5/8 chamber-chart).

This script anneals the mutator: probability of multibit moves decays from
1.0 at iteration 0 to 0.0 at iteration N. Early: multibit (escape pockets).
Late: 1-bit (fine descent). Best of both.
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


def mutate_M2_annealed(M1, M2, rng, active_words, multibit_prob):
    """Mutator with annealing knob: multibit_prob in [0.0, 1.0].
    multibit_prob=1.0 → mostly multibit. multibit_prob=0.0 → pure 1-bit."""
    M2_new = list(M2)
    use_multibit = rng.random() < multibit_prob
    idx = active_words[rng.randrange(len(active_words))]

    if not use_multibit:
        # 1-bit path with same fallback as F315: 50% 1-bit, 30% mask, 20% rand
        mode = rng.randrange(10)
        if mode < 5:
            M2_new[idx] ^= 1 << rng.randrange(32)
        elif mode < 8:
            M2_new[idx] ^= rng.getrandbits(32)
        else:
            M2_new[idx] = rng.getrandbits(32) & MASK
    else:
        # multibit path: 2-bit (50%) / 3-bit single (25%) / 3-bit cross (15%)
        # / mask / random
        mode = rng.randrange(20)
        if mode < 10:
            # 2-bit single-word
            b1 = rng.randrange(32); b2 = rng.randrange(32)
            M2_new[idx] ^= (1 << b1) ^ (1 << b2)
        elif mode < 15:
            # 3-bit single-word
            bits = rng.sample(range(32), 3)
            for b in bits:
                M2_new[idx] ^= 1 << b
        elif mode < 18:
            # 3-bit cross-word
            for _ in range(3):
                j = active_words[rng.randrange(len(active_words))]
                b = rng.randrange(32)
                M2_new[j] ^= 1 << b
        elif mode < 19:
            M2_new[idx] ^= rng.getrandbits(32)
        else:
            M2_new[idx] = rng.getrandbits(32) & MASK
    return M2_new


def run_seeded_restart_annealed(M1, M2_init, active_words, iterations, rng,
                                 score_kwargs, anneal_floor=0.0,
                                 anneal_ceiling=1.0):
    rec = atlas_evaluate(M1, M2_init)
    best_score = atlas_score(rec, **score_kwargs)
    best_rec = rec
    best_M2 = list(M2_init)
    cur_M2 = list(M2_init)
    cur_score = best_score
    accepts = 0
    chart_matches = 0
    chamber_hits = 0

    for it in range(iterations):
        # Linear anneal: multibit_prob = ceiling at it=0 → floor at it=iterations
        prog = it / max(1, iterations - 1)
        multibit_prob = anneal_ceiling + (anneal_floor - anneal_ceiling) * prog

        cand_M2 = mutate_M2_annealed(M1, cur_M2, rng, active_words,
                                      multibit_prob)
        cand_rec = atlas_evaluate(M1, cand_M2)
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
            cur_M2 = cand_M2
            cur_score = cand_score
            accepts += 1
            if cand_rec["chart_top2"] in (("dh", "dCh"), ("dCh", "dh")):
                chart_matches += 1
            if (cand_rec["a57_xor_hw"] == 0 and
                cand_rec["D61_hw"] <= 4 and
                cand_rec["chart_top2"] in (("dh","dCh"),("dCh","dh"))):
                chamber_hits += 1
            if cand_score < best_score:
                best_score = cand_score
                best_rec = cand_rec
                best_M2 = list(cand_M2)
    return {
        "best_score": best_score,
        "best_rec": best_rec,
        "best_M2": [f"0x{w:08x}" for w in best_M2],
        "M1": [f"0x{w:08x}" for w in M1],
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
    ap.add_argument("--active-words", default="0,1,2,8,9")
    ap.add_argument("--seed", type=int, default=31800)
    ap.add_argument("--alpha", type=float, default=4.0)
    ap.add_argument("--beta", type=float, default=1.0)
    ap.add_argument("--gamma", type=float, default=8.0)
    ap.add_argument("--delta", type=float, default=0.05)
    ap.add_argument("--anneal-ceiling", type=float, default=0.8,
                    help="multibit_prob at iter 0")
    ap.add_argument("--anneal-floor",   type=float, default=0.05,
                    help="multibit_prob at iter N")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    with open(args.init_json) as f:
        seed = json.load(f)
    M1 = [int(x, 16) for x in seed["best"]["M1"]]
    M2_init = [int(x, 16) for x in seed["best"]["M2_kernel"]]

    init_rec = atlas_evaluate(M1, M2_init)
    print(f"# annealed seeded init: a57={init_rec['a57_xor_hw']} "
          f"D61={init_rec['D61_hw']} chart={init_rec['chart_top2']}")
    print(f"# multibit_prob anneal: {args.anneal_ceiling:.2f} "
          f"→ {args.anneal_floor:.2f}")

    active_words = parse_active_words(args.active_words)
    rng = random.Random(args.seed)
    score_kwargs = dict(atlas_alpha=args.alpha, atlas_beta=args.beta,
                         atlas_gamma=args.gamma, atlas_delta=args.delta)

    t0 = time.time()
    results = []
    for r in range(args.restarts):
        M2_pert = list(M2_init)
        for _ in range(rng.randint(1, 3)):
            idx = active_words[rng.randrange(len(active_words))]
            M2_pert[idx] ^= 1 << rng.randrange(32)
        rs = run_seeded_restart_annealed(M1, M2_pert, active_words,
                                          args.iterations, rng, score_kwargs,
                                          args.anneal_floor,
                                          args.anneal_ceiling)
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
        "args": vars(args), "init_rec": init_rec,
        "active_words": active_words, "wall_seconds": elapsed,
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
