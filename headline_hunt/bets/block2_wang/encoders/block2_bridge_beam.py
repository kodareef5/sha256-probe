#!/usr/bin/env python3
"""
block2_bridge_beam.py — bridge-guided W-space hillclimb for cascade-1 cands.

Per user direction 2026-04-30: combine F374 + yale F378-F384 into a
bridge-guided block2_wang search. Searches in (W57, W58, W59, W60)
W-space (128-bit), using build_corpus.py's cascade-1 forward primitives
and bridge_score.py's selector.

Cands:
  bit3_m33ec77ca   F374 deep-tail dominator
  bit2_ma896ee41   F374 deep-tail dominator
  bit28_md1acca79  F374 deep-tail dominator
  bit13_m916a56aa  Control — F378's surprise top-1 (NOT in F374 dominators)

Search:
  Per cand: precompute (s1_init, s2_init, W1_pre, W2_pre) once via
  precompute_state. Then iterate:
    seed: random (w1_57, w1_58, w1_59, w1_60)
    mutation: flip 1-3 random bits across the 128 W-bits
    accept if bridge_score improves; greedy hillclimb

  F408 extension:
    optionally use simulated annealing over the same W-space. Worse moves
    are accepted with Metropolis probability exp(delta_score / T), with
    geometric cooling from --temp-start to --temp-end. --seeds acts as
    independent restarts.

Discipline:
  - 0 solver runs; pure cascade-1 forward simulation
  - Search is in W-space (128-bit) per cand, not message-space
  - Filtering enforces cascade-1 invariants (run_full returns None if violated)
"""
import argparse
from collections import deque
import json
import math
import os
import random
import sys
import time

sys.path.insert(0, "/Users/mac/Desktop/sha256_review")
from lib.sha256 import (K, IV, MASK, sigma0, sigma1, Sigma0, Sigma1,
                        Ch, Maj, add, precompute_state)
sys.path.insert(0, "/Users/mac/Desktop/sha256_review/headline_hunt/bets/mitm_residue/prototypes")
from forward_table_builder import cascade_step_offset, cascade2_offset, apply_round

sys.path.insert(0, "/Users/mac/Desktop/sha256_review/headline_hunt/bets/block2_wang/encoders")
from bridge_score import bridge_score


def run_full(s1_init, s2_init, W1_pre, W2_pre, w1_57, w1_58, w1_59, w1_60):
    """Run cascade-1 trajectory from round 57 through 63. Returns None if
    cascade-1 invariants are violated; record dict otherwise."""
    cw57 = cascade_step_offset(s1_init, s2_init, 57)
    w2_57 = (w1_57 + cw57) & MASK
    s1_57 = apply_round(s1_init, w1_57, 57)
    s2_57 = apply_round(s2_init, w2_57, 57)

    cw58 = cascade_step_offset(s1_57, s2_57, 58)
    w2_58 = (w1_58 + cw58) & MASK
    s1_58 = apply_round(s1_57, w1_58, 58)
    s2_58 = apply_round(s2_57, w2_58, 58)

    cw59 = cascade_step_offset(s1_58, s2_58, 59)
    w2_59 = (w1_59 + cw59) & MASK
    s1_59 = apply_round(s1_58, w1_59, 59)
    s2_59 = apply_round(s2_58, w2_59, 59)

    if (s1_59[1] ^ s2_59[1]) or (s1_59[2] ^ s2_59[2]) or (s1_59[3] ^ s2_59[3]):
        return None

    cw60 = cascade2_offset(s1_59, s2_59)
    w2_60 = (w1_60 + cw60) & MASK
    s1_60 = apply_round(s1_59, w1_60, 60)
    s2_60 = apply_round(s2_59, w2_60, 60)

    if (s1_60[4] ^ s2_60[4]):
        return None

    W1 = list(W1_pre[:57]) + [w1_57, w1_58, w1_59, w1_60]
    W2 = list(W2_pre[:57]) + [w2_57, w2_58, w2_59, w2_60]
    for r in range(61, 64):
        W1.append(add(sigma1(W1[r-2]), W1[r-7], sigma0(W1[r-15]), W1[r-16]))
        W2.append(add(sigma1(W2[r-2]), W2[r-7], sigma0(W2[r-15]), W2[r-16]))

    s1, s2 = s1_60, s2_60
    for r in range(61, 64):
        s1 = apply_round(s1, W1[r], r)
        s2 = apply_round(s2, W2[r], r)
    return {
        "state1_63": s1, "state2_63": s2,
        "diff63": tuple(s1[i] ^ s2[i] for i in range(8)),
        "w_ms": (w1_57, w1_58, w1_59, w1_60),
        "w_ms_2": (w2_57, w2_58, w2_59, w2_60),
    }


def evaluate(s1_init, s2_init, W1_pre, W2_pre, m0, fill, kbit,
             w1_57, w1_58, w1_59, w1_60):
    r = run_full(s1_init, s2_init, W1_pre, W2_pre, w1_57, w1_58, w1_59, w1_60)
    if r is None:
        return None  # cascade-1 invariant violated
    diff = r["diff63"]
    hw63 = [bin(d).count("1") for d in diff]
    REG = ["a","b","c","d","e","f","g","h"]
    active = sorted([REG[i] for i in range(8) if diff[i] != 0])
    return {
        "candidate": {"m0": f"0x{m0:08x}", "fill": f"0x{fill:08x}", "kernel_bit": kbit},
        "w1_57": f"0x{r['w_ms'][0]:08x}", "w1_58": f"0x{r['w_ms'][1]:08x}",
        "w1_59": f"0x{r['w_ms'][2]:08x}", "w1_60": f"0x{r['w_ms'][3]:08x}",
        "w2_57": f"0x{r['w_ms_2'][0]:08x}", "w2_58": f"0x{r['w_ms_2'][1]:08x}",
        "w2_59": f"0x{r['w_ms_2'][2]:08x}", "w2_60": f"0x{r['w_ms_2'][3]:08x}",
        "iv1_63": [f"0x{x:08x}" for x in r["state1_63"]],
        "iv2_63": [f"0x{x:08x}" for x in r["state2_63"]],
        "diff63": [f"0x{d:08x}" for d in diff],
        "hw63": hw63,
        "hw_total": sum(hw63),
        "active_regs": active,
        "da_eq_de": diff[0] == diff[4],
    }


CANDS = [
    # (short, m0_hex, fill_hex, kbit)
    ("bit3_m33ec77ca",   0x33ec77ca, 0xffffffff,  3),
    ("bit2_ma896ee41",   0xa896ee41, 0xffffffff,  2),
    ("bit24_mdc27e18c",  0xdc27e18c, 0xffffffff, 24),
    ("bit28_md1acca79",  0xd1acca79, 0xffffffff, 28),
    ("bit13_m916a56aa",  0x916a56aa, 0xffffffff, 13),  # F378 surprise top-1 control
]


def setup_cand(m0, fill, kbit):
    """Precompute (s1_init, s2_init, W1_pre, W2_pre) for a cand. Returns
    None if not cascade-eligible."""
    diff = 1 << kbit
    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= diff; M2[9] ^= diff
    s1_init, W1_pre = precompute_state(M1)
    s2_init, W2_pre = precompute_state(M2)
    if s1_init[0] != s2_init[0]:
        return None
    return s1_init, s2_init, W1_pre, W2_pre


def mutate_w(rng, cur_W, max_flips):
    """Flip 1..max_flips random bits across the 128-bit W vector."""
    n_flips = rng.randint(1, max_flips)
    new_W = list(cur_W)
    for _ in range(n_flips):
        slot = rng.randrange(4)
        bit = rng.randrange(32)
        new_W[slot] ^= (1 << bit)
    return tuple(new_W), n_flips


def anneal_temperature(i, iterations, temp_start, temp_end):
    if iterations <= 1:
        return temp_end
    progress = i / (iterations - 1)
    return temp_start * ((temp_end / temp_start) ** progress)


def hillclimb(short, m0, fill, kbit, iterations, seed=0, verbose=False,
              method="greedy", temp_start=2.0, temp_end=0.1,
              max_flips=3, tabu_size=0):
    setup = setup_cand(m0, fill, kbit)
    if setup is None:
        return {"cand": short, "error": "not cascade-eligible"}
    s1_init, s2_init, W1_pre, W2_pre = setup

    rng = random.Random(seed)

    # Random initial W
    def rand_W():
        return tuple(rng.getrandbits(32) for _ in range(4))

    # Find an initial W that lands in cascade-1
    cur_W = None
    cur_rec = None
    cur_score = -1e9
    for _ in range(2000):
        w = rand_W()
        rec = evaluate(s1_init, s2_init, W1_pre, W2_pre, m0, fill, kbit, *w)
        if rec is None:
            continue
        sc = bridge_score(rec, kbit)
        if sc["score"] is not None:
            cur_W = w
            cur_rec = rec
            cur_score = sc["score"]
            break
    if cur_W is None:
        return {"cand": short, "error": "no cascade-1 + bridge-passing seed found in 2000 attempts"}

    accepts = 0
    accepted_worse = 0
    cascade_rejects = 0
    bridge_rejects = 0
    tabu_rejects = 0
    total_flips = 0
    tabu = deque(maxlen=tabu_size)
    tabu_set = set()

    best_score = cur_score
    best_W = cur_W
    best_rec = cur_rec
    best_iter = 0

    for i in range(iterations):
        new_W, n_flips = mutate_w(rng, cur_W, max_flips)
        total_flips += n_flips
        if tabu_size and new_W in tabu_set:
            tabu_rejects += 1
            continue
        rec = evaluate(s1_init, s2_init, W1_pre, W2_pre, m0, fill, kbit, *new_W)
        if rec is None:
            cascade_rejects += 1
            continue
        sc = bridge_score(rec, kbit)
        if sc["score"] is None:
            bridge_rejects += 1
            continue
        delta = sc["score"] - cur_score
        accept = delta > 0
        if method == "anneal" and not accept:
            T = max(anneal_temperature(i, iterations, temp_start, temp_end), 1e-9)
            accept = rng.random() < math.exp(delta / T)
            if accept:
                accepted_worse += 1
        if accept:
            cur_W = new_W
            cur_rec = rec
            cur_score = sc["score"]
            accepts += 1
            if tabu_size:
                if len(tabu) == tabu.maxlen:
                    old = tabu.popleft()
                    tabu_set.discard(old)
                tabu.append(cur_W)
                tabu_set.add(cur_W)
            if cur_score > best_score:
                best_score = cur_score
                best_W = cur_W
                best_rec = cur_rec
                best_iter = i
            if verbose:
                print(f"    iter {i:7d}: accept score={cur_score:.2f} best={best_score:.2f} hw={rec['hw_total']:3d}")

    return {
        "cand": short, "m0": f"0x{m0:08x}", "fill": f"0x{fill:08x}", "kernel_bit": kbit,
        "iterations": iterations, "seed": seed, "method": method,
        "temp_start": temp_start if method == "anneal" else None,
        "temp_end": temp_end if method == "anneal" else None,
        "max_flips": max_flips, "tabu_size": tabu_size,
        "accepts": accepts, "accepted_worse": accepted_worse,
        "cascade_rejects": cascade_rejects, "bridge_rejects": bridge_rejects,
        "tabu_rejects": tabu_rejects,
        "mean_flips": round(total_flips / iterations, 3) if iterations else 0,
        "best_score": best_score,
        "best_iter": best_iter,
        "best_record": best_rec,
        "best_W": [f"0x{w:08x}" for w in best_W],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip(), formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--iterations", type=int, default=2000)
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--method", choices=["greedy", "anneal"], default="greedy")
    ap.add_argument("--temp-start", type=float, default=2.0)
    ap.add_argument("--temp-end", type=float, default=0.1)
    ap.add_argument("--max-flips", type=int, default=3)
    ap.add_argument("--tabu-size", type=int, default=0)
    ap.add_argument("--candidates", default=None,
                    help="Comma-separated candidate shorts. Default: Path C panel bit2,bit3,bit24,bit28.")
    ap.add_argument("--out", default=None)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    if args.max_flips < 1:
        raise SystemExit("--max-flips must be >= 1")

    default_panel = {"bit2_ma896ee41", "bit3_m33ec77ca", "bit24_mdc27e18c", "bit28_md1acca79"}
    requested = set(args.candidates.split(",")) if args.candidates else default_panel
    selected = [c for c in CANDS if c[0] in requested]
    missing = requested - {c[0] for c in selected}
    if missing:
        raise SystemExit(f"unknown candidate(s): {', '.join(sorted(missing))}")

    print(
        f"=== block2_bridge_beam.py: {args.method} {args.iterations} iters × "
        f"{args.seeds} seeds × {len(selected)} cands ==="
    )
    if args.method == "anneal":
        print(f"    temp {args.temp_start} -> {args.temp_end}, max_flips={args.max_flips}, tabu={args.tabu_size}")
    print()
    t0 = time.time()
    all_runs = []
    for short, m0, fill, kbit in selected:
        for seed in range(args.seeds):
            print(f"  {short} seed={seed} ...")
            r = hillclimb(short, m0, fill, kbit, args.iterations, seed=seed,
                          verbose=args.verbose, method=args.method,
                          temp_start=args.temp_start, temp_end=args.temp_end,
                          max_flips=args.max_flips, tabu_size=args.tabu_size)
            if "error" in r:
                print(f"    ERROR: {r['error']}")
            else:
                rec = r["best_record"]
                print(f"    best score={r['best_score']:.2f}  hw={rec['hw_total']:3d}  "
                      f"best_iter={r['best_iter']:7d}  accepts={r['accepts']:5d}  "
                      f"worse={r['accepted_worse']:5d}  cascade_rej={r['cascade_rejects']:5d}  "
                      f"bridge_rej={r['bridge_rejects']:5d}")
            all_runs.append(r)
    wall = time.time() - t0
    print(f"\nTotal wall: {wall:.1f}s")

    # Aggregate per cand
    by_cand = {}
    for r in all_runs:
        if "error" in r: continue
        c = r["cand"]
        if c not in by_cand or r["best_score"] > by_cand[c]["best_score"]:
            by_cand[c] = r

    print(f"\n=== Per-cand best across seeds (vs corpus best) ===")
    # Load corpus best per cand from F374 stratification (if we have it)
    print(f"{'cand':22s} {'beam best score':>15s} {'beam hw':>8s} {'corpus best hw':>15s}")
    corpus_best_hw = {  # from F374/F378 known top entries
        "bit3_m33ec77ca": 55,
        "bit2_ma896ee41": 57,
        "bit24_mdc27e18c": 57,
        "bit28_md1acca79": 59,
        "bit13_m916a56aa": 59,  # F378 top-1
    }
    for c, r in by_cand.items():
        rec = r["best_record"]
        corpus_hw = corpus_best_hw.get(c, "?")
        print(f"  {c:22s} {r['best_score']:>15.2f} {rec['hw_total']:>8d} {corpus_hw:>15}")

    # Save
    out_path = args.out or "headline_hunt/bets/block2_wang/results/search_artifacts/20260430_F408_bridge_beam_anneal.json"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump({
            "description": "F408: bridge-guided W-space search with optional simulated annealing",
            "method": args.method,
            "iterations": args.iterations, "seeds": args.seeds,
            "temp_start": args.temp_start if args.method == "anneal" else None,
            "temp_end": args.temp_end if args.method == "anneal" else None,
            "max_flips": args.max_flips,
            "tabu_size": args.tabu_size,
            "wall_seconds": round(wall, 2),
            "all_runs": all_runs,
            "best_per_cand": {c: r for c, r in by_cand.items()},
        }, f, indent=2)
    print(f"\nwrote {out_path}")


if __name__ == "__main__":
    main()
