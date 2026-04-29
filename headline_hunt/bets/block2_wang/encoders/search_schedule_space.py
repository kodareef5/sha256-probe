#!/usr/bin/env python3
"""
search_schedule_space.py — Tool 2 (truncated, atlas-loss variant).

Pivot from the original plan: the linear preimage lift in preimage_lift.py
is mathematically clean but produces HIGH-HW dM (mean ~113 bits) even for
LOW-HW dW targets, because the schedule recurrence's GF(2) inverse is dense.
That makes "search in dW[16..23] space, lift back to dM" structurally
unproductive for finding sparse dM.

What IS productive (per F311 carry-chart atlas):
  - Block2_wang's existing search mutates dM in active-word slots and scores
    by chain-output diff. F311 showed this finds points in chart (dSig1,dCh)
    or (dCh,dT2) with a57_xor != 0 — wrong half-plane vs the (dh,dCh) +
    a57_xor=0 chamber attractor.
  - Replacing the chain-output score with a CARRY-CHART-ATLAS LOSS adds the
    cascade-1-hardlock and chart-membership signals to the optimization.

This script:
  1. Loads a starting M1 (random or from a bundle).
  2. Mutates dM[active_words] via bit-flips / random words.
  3. Scores each candidate via the carry-chart atlas:
        score = atlas_alpha   * a57_xor_hw       (cascade-1 hardlock)
              + atlas_beta    * D61_hw           (chamber-defect floor)
              + atlas_gamma   * (1 - dh_dCh_indicator)  (chart membership)
              + atlas_delta   * tail63_state_diff_hw    (full-state divergence)
  4. Tracks best per-restart, and the chart-conditional best.

Usage:
    python3 search_schedule_space.py --pilot          # 4 restarts × 2000 iters
    python3 search_schedule_space.py --restarts 8 --iterations 5000
    python3 search_schedule_space.py --active-words 0,1,2,8,9
"""
import argparse
import json
import os
import random
import sys
import time

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)

from lib.sha256 import MASK, precompute_state, K, sigma0, sigma1, Sigma0, Sigma1, Ch, Maj, add, hw

# Reuse atlas primitives directly (avoid path gymnastics by reimplementing here).

# ---------------------------------------------------------------------------
# Cascade-1 / atlas primitives (mirror carry_chart_atlas.py)
# ---------------------------------------------------------------------------

def cascade1_offset_parts(s1, s2):
    dh    = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh   = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    dT2   = ((Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2]))
             - (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2]))) & MASK
    parts = [dh, dSig1, dCh, dT2]
    sums = [(parts[0] + parts[1]) & MASK]
    sums.append((sums[0] + parts[2]) & MASK)
    sums.append((sums[1] + parts[3]) & MASK)
    return parts, sums[2]


def apply_round(s, w, r):
    a, b, c, d, e, f, g, h = s
    T1 = add(h, Sigma1(e), Ch(e, f, g), K[r], w)
    T2 = add(Sigma0(a), Maj(a, b, c))
    return (
        add(T1, T2), a, b, c, add(d, T1), e, f, g,
    )


def expand_schedule(M):
    W = list(M) + [0] * 48
    for i in range(16, 64):
        W[i] = add(sigma1(W[i-2]), W[i-7], sigma0(W[i-15]), W[i-16])
    return W


def atlas_evaluate(M1, M2):
    """
    Compute (a57_xor_hw, D61_hw, dom_chart_top2, tail63_state_diff_hw) for the
    pair (M1, M2). Mirrors carry_chart_atlas.py decompose_point but returns only
    the score-relevant fields.
    """
    s1, _ = precompute_state(M1)
    s2, _ = precompute_state(M2)
    a57_xor = (s1[0] ^ s2[0]) & MASK
    a57_xor_hw = hw(a57_xor)

    W1 = expand_schedule(M1)
    W2 = expand_schedule(M2)

    # Walk rounds 57..63 to find round-61 parts and final state diff.
    parts61 = None
    s1_cur, s2_cur = s1, s2
    D61 = 0
    for r in range(57, 64):
        if r == 61:
            parts, _offset = cascade1_offset_parts(s1_cur, s2_cur)
            parts61 = parts
            offset_r = sum(parts) & MASK
            D61 = ((W2[r] - W1[r]) - offset_r) & MASK
        s1_cur = apply_round(s1_cur, W1[r], r)
        s2_cur = apply_round(s2_cur, W2[r], r)

    # State diff after round 63
    state_diff_hw = sum(hw((s1_cur[i] ^ s2_cur[i]) & MASK) for i in range(8))

    # Chart classification: top 2 dominant parts at round 61
    if parts61 is None:
        chart_top2 = ("?", "?")
    else:
        names = ["dh", "dSig1", "dCh", "dT2"]
        ranked = sorted(zip(names, [hw(p) for p in parts61]), key=lambda kv: -kv[1])
        chart_top2 = (ranked[0][0], ranked[1][0])

    return {
        "a57_xor_hw": a57_xor_hw,
        "D61_hw": hw(D61),
        "chart_top2": chart_top2,
        "tail63_state_diff_hw": state_diff_hw,
    }


def atlas_score(rec, atlas_alpha=4.0, atlas_beta=1.0, atlas_gamma=8.0,
                atlas_delta=0.05):
    """
    Lower is better. Strongly penalizes a57_xor (cascade-1 hardlock violation),
    moderately penalizes D61_hw, gives a bonus for chart=(dh, dCh).
    """
    chart_match = (rec["chart_top2"] == ("dh", "dCh") or
                   rec["chart_top2"] == ("dCh", "dh"))
    return (
        atlas_alpha * rec["a57_xor_hw"]
        + atlas_beta * rec["D61_hw"]
        + atlas_gamma * (0.0 if chart_match else 1.0)
        + atlas_delta * rec["tail63_state_diff_hw"]
    )


# ---------------------------------------------------------------------------
# Search loop
# ---------------------------------------------------------------------------

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
    return sorted(set(out))


def mutate_M2(M1, M2, rng, active_words):
    M2_new = list(M2)
    mode = rng.randrange(10)
    idx = active_words[rng.randrange(len(active_words))]
    if mode < 5:
        bit = rng.randrange(32)
        M2_new[idx] ^= 1 << bit
    elif mode < 8:
        mask = rng.getrandbits(32)
        M2_new[idx] ^= mask
    else:
        M2_new[idx] = rng.getrandbits(32) & MASK
    return M2_new


def random_M1(rng):
    return [rng.getrandbits(32) & MASK for _ in range(16)]


def run_restart(M1, active_words, iterations, rng, score_kwargs):
    M2 = list(M1)
    # Initialize M2 by perturbing a few active-word bits.
    for _ in range(rng.randint(3, 8)):
        idx = active_words[rng.randrange(len(active_words))]
        M2[idx] ^= 1 << rng.randrange(32)
    rec = atlas_evaluate(M1, M2)
    best_score = atlas_score(rec, **score_kwargs)
    best_rec = rec
    best_M2 = list(M2)

    history = {"score_curve": [best_score], "best_recs": [best_rec]}
    accept_count = 0
    chart_match_count = 0

    cur_M2 = list(M2)
    cur_score = best_score
    for it in range(iterations):
        cand_M2 = mutate_M2(M1, cur_M2, rng, active_words)
        cand_rec = atlas_evaluate(M1, cand_M2)
        cand_score = atlas_score(cand_rec, **score_kwargs)
        # Greedy + occasional uphill (simulated annealing-ish)
        accept = False
        if cand_score < cur_score:
            accept = True
        else:
            T = max(0.5, 5.0 * (1.0 - it / max(1, iterations)))
            delta = cand_score - cur_score
            import math
            if rng.random() < math.exp(-delta / T):
                accept = True
        if accept:
            cur_M2 = cand_M2
            cur_score = cand_score
            accept_count += 1
            if cand_rec["chart_top2"] in (("dh", "dCh"), ("dCh", "dh")):
                chart_match_count += 1
            if cand_score < best_score:
                best_score = cand_score
                best_rec = cand_rec
                best_M2 = list(cand_M2)
                history["score_curve"].append(best_score)
                history["best_recs"].append(best_rec)
    return {
        "best_score": best_score,
        "best_rec": best_rec,
        "best_M2": [f"0x{w:08x}" for w in best_M2],
        "M1": [f"0x{w:08x}" for w in M1],
        "iterations": iterations,
        "accepts": accept_count,
        "chart_matches": chart_match_count,
        "score_curve_tail": history["score_curve"][-10:],
        "best_recs_tail": history["best_recs"][-5:],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot", action="store_true",
                    help="quick pilot: 4 restarts × 2000 iters")
    ap.add_argument("--restarts", type=int, default=4)
    ap.add_argument("--iterations", type=int, default=2000)
    ap.add_argument("--active-words", default="0,1,2,8,9",
                    help="comma-separated active word indices")
    ap.add_argument("--seed", type=int, default=2026)
    ap.add_argument("--alpha", type=float, default=4.0,
                    help="weight on a57_xor_hw")
    ap.add_argument("--beta", type=float, default=1.0,
                    help="weight on D61_hw")
    ap.add_argument("--gamma", type=float, default=8.0,
                    help="penalty for chart != (dh, dCh)")
    ap.add_argument("--delta", type=float, default=0.05,
                    help="weight on tail63_state_diff_hw")
    ap.add_argument("--out", default=None,
                    help="output JSON path")
    args = ap.parse_args()

    if args.pilot:
        args.restarts = 4
        args.iterations = 2000

    active_words = parse_active_words(args.active_words)
    score_kwargs = dict(atlas_alpha=args.alpha, atlas_beta=args.beta,
                         atlas_gamma=args.gamma, atlas_delta=args.delta)

    rng = random.Random(args.seed)
    t0 = time.time()
    results = []
    print(f"# search_schedule_space (atlas-loss): {args.restarts} restarts × "
          f"{args.iterations} iters | active_words={active_words}")
    print(f"# loss = {args.alpha}*a57_xor_hw + {args.beta}*D61_hw + "
          f"{args.gamma}*(chart_not_dhCh) + {args.delta}*tail63_hw")

    for r in range(args.restarts):
        M1 = random_M1(rng)
        rs = run_restart(M1, active_words, args.iterations, rng, score_kwargs)
        rs["restart"] = r
        results.append(rs)
        rec = rs["best_rec"]
        print(f"  restart {r}: best_score={rs['best_score']:.2f} "
              f"a57={rec['a57_xor_hw']} D61={rec['D61_hw']} "
              f"chart={rec['chart_top2']} tail63={rec['tail63_state_diff_hw']} "
              f"accepts={rs['accepts']} chart_matches={rs['chart_matches']}")

    elapsed = time.time() - t0
    print(f"# wall: {elapsed:.1f}s")

    summary = {
        "args": vars(args),
        "active_words": active_words,
        "wall_seconds": elapsed,
        "restarts": results,
        "best_overall_score": min(r["best_score"] for r in results),
        "any_chart_match_best": any(
            r["best_rec"]["chart_top2"] in (("dh","dCh"),("dCh","dh"))
            for r in results
        ),
        "any_a57_zero_best": any(r["best_rec"]["a57_xor_hw"] == 0 for r in results),
    }

    out_path = args.out or os.path.join(
        REPO,
        "headline_hunt/bets/block2_wang/results/search_artifacts/"
        f"20260429_F312_schedule_space_atlas_loss_pilot.json"
    )
    with open(out_path, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"# wrote {out_path}")


if __name__ == "__main__":
    main()
