#!/usr/bin/env python3
"""block2_m2_pair_beam.py — multi-bit M2 pair beam (Yale F519 recommendation).

Analogous to pair_beam_search.py (W57..W60) but searches the 16-word M2
mask space (16 * 32 = 512 bits). Used for second-block absorber search:

  IV1 = standard SHA-256 IV
  IV2 = IV1 ^ block1_diff63   (block-1 residual feeds in via IV diff)
  M1  = zeros (16 words)
  M2  = free; starts from absorber_m2 init mask
  Run R rounds; objective = HW(state1, state2) over 8 32-bit lanes.

Pair beam: build a pool of strong 2-bit M2 flips (single-pair), rank by
the selected objective, then compose up to max_pairs of them; keep
beam-width best states at each composition depth. The objective can be
plain total HW, c/g-biased HW, or an explicit per-lane weighted score.

Inputs:
  --seed-jsonl  JSONL with block1_diff63 + absorber_m2 fields
                (matches F518 absorber_m2_late_round_seeds.jsonl format)
  --rank        Which seed index in JSONL to use (default 0)
  --init-M2     Optional explicit restart M2, used for HW86 deepening and
                cross-round continuation.

Search params (mirror pair_beam_search.py):
  --pair-pool   Top-K 2-bit deltas to keep (default 1024)
  --beam-width  Max kept states per depth (default 1024)
  --max-pairs   Max compositions (default 6)
  --max-radius  Max bits flipped (default 12)
  --rounds      Rounds to evaluate (default 24)
  --top-records Number of best records to retain (default 30)

Usage:
  python3 block2_m2_pair_beam.py \\
    --seed-jsonl headline_hunt/bets/block2_wang/results/search_artifacts/20260502_absorber_matrix_overnight/F518_absorber_m2_late_round_seeds.jsonl \\
    --rank 0 --rounds 24 --out search_artifacts/F534_bit13_rank36_m2_pair_beam.json
"""
import argparse
import itertools
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from lib.sha256 import K, IV, MASK, sigma0, sigma1, Sigma0, Sigma1, Ch, Maj, add


def expand_schedule(M):
    W = list(M)
    for r in range(16, 64):
        W.append(add(sigma1(W[r-2]), W[r-7], sigma0(W[r-15]), W[r-16]))
    return W


def apply_round(state, w, r):
    T1 = add(state[7], Sigma1(state[4]), Ch(state[4], state[5], state[6]), K[r], w)
    T2 = add(Sigma0(state[0]), Maj(state[0], state[1], state[2]))
    a = add(T1, T2)
    e = add(state[3], T1)
    return (a, state[0], state[1], state[2], e, state[4], state[5], state[6])


def eval_m2(iv1, iv2, m1_W, m2, rounds):
    """Evaluate HW(state1, state2) after `rounds` rounds.
    m1_W is precomputed schedule for M1 (zero); m2 is the M2 vector (16 words)."""
    W2 = expand_schedule(m2)
    s1 = tuple(iv1)
    s2 = tuple(iv2)
    for r in range(rounds):
        s1 = apply_round(s1, m1_W[r], r)
        s2 = apply_round(s2, W2[r], r)
    diff = tuple(s1[i] ^ s2[i] for i in range(8))
    hw_total = sum(bin(d).count("1") for d in diff)
    return hw_total, diff


def hw_per_lane(diff):
    return [bin(d).count("1") for d in diff]


def parse_w_arr(parts):
    return [int(p, 16) & MASK for p in parts]


def parse_m2_override(raw):
    parts = [p.strip() for p in raw.replace(" ", ",").split(",") if p.strip()]
    if len(parts) != 16:
        raise SystemExit(f"--init-M2 needs 16 hex words, got {len(parts)}")
    return parse_w_arr(parts)


def parse_lane_weights(raw):
    if not raw:
        return [1.0] * 8
    parts = [float(p.strip()) for p in raw.split(",") if p.strip()]
    if len(parts) != 8:
        raise SystemExit(f"--lane-weights needs 8 numeric weights, got {len(parts)}")
    return parts


def objective_value(hw_total, lane_hw, objective, lane_weights, cg_weight):
    if objective == "hw":
        return float(hw_total)
    if objective == "cg":
        return float(hw_total) + cg_weight * float(lane_hw[2] + lane_hw[6])
    if objective == "weighted":
        return sum(w * h for w, h in zip(lane_weights, lane_hw))
    raise ValueError(objective)


def record_sort_key(record):
    return (record["hw"], record.get("objective", record["hw"]), record.get("depth", 0), record["bits"])


def load_seed(path, rank):
    """Load seed JSONL and extract entry at given rank index."""
    seeds = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line: continue
            seeds.append(json.loads(line))
    if rank >= len(seeds):
        raise SystemExit(f"rank {rank} out of range (only {len(seeds)} seeds)")
    return seeds[rank], len(seeds)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed-jsonl", required=True)
    ap.add_argument("--rank", type=int, default=0)
    ap.add_argument("--rounds", type=int, default=24)
    ap.add_argument("--pair-pool", type=int, default=1024)
    ap.add_argument("--objective", choices=["hw", "cg", "weighted"], default="hw",
                    help="Beam objective: total HW, total HW plus c/g penalty, or weighted lane HW.")
    ap.add_argument("--pair-rank", choices=["hw", "cg", "weighted"], default=None,
                    help="Pair-pool ranking objective; default matches --objective.")
    ap.add_argument("--lane-weights", default="",
                    help="Eight comma-separated weights for --objective weighted.")
    ap.add_argument("--cg-weight", type=float, default=1.0,
                    help="Penalty multiplier on c+g lane HW for --objective cg.")
    ap.add_argument("--beam-width", type=int, default=1024)
    ap.add_argument("--max-pairs", type=int, default=6)
    ap.add_argument("--max-radius", type=int, default=12)
    ap.add_argument("--top-records", type=int, default=30)
    ap.add_argument("--init-M2", default=None,
                    help="Optional 16-word M2 override, comma/space-separated hex. "
                         "Uses seed diff63 but starts beam from this M2.")
    ap.add_argument("--init-hw", type=int, default=None,
                    help="Optional expected HW for --init-M2 validation.")
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()
    if args.pair_rank is None:
        args.pair_rank = args.objective
    lane_weights = parse_lane_weights(args.lane_weights)

    seed, total = load_seed(args.seed_jsonl, args.rank)
    print(f"Loaded seed rank={args.rank} of {total} from {args.seed_jsonl}")

    # Parse fields
    diff63 = parse_w_arr(seed["block1_diff63"])
    seed_m2 = parse_w_arr(seed["absorber_m2"])
    m2_init = parse_m2_override(args.init_M2) if args.init_M2 else seed_m2
    absorber_best_hw = seed.get("absorber_best_hw")

    # IV1 = standard SHA-256 IV; IV2 = IV1 ^ diff63
    iv1 = list(IV)
    iv2 = [iv1[i] ^ diff63[i] for i in range(8)]
    M1 = [0] * 16
    m1_W = expand_schedule(M1)

    # Verify init
    init_hw, init_diff = eval_m2(iv1, iv2, m1_W, m2_init, args.rounds)
    print(f"Init M2 HW={init_hw} (seed claimed absorber_best_hw={absorber_best_hw}, diff range expected at rounds={args.rounds})")
    if args.init_hw is not None and init_hw != args.init_hw:
        raise SystemExit(f"--init-hw mismatch: expected {args.init_hw}, evaluated {init_hw}")
    init_lane_hw = hw_per_lane(init_diff)
    init_objective = objective_value(init_hw, init_lane_hw, args.objective, lane_weights, args.cg_weight)
    print(f"Init lane HW: {init_lane_hw} (sum={init_hw})")
    print(f"Init objective ({args.objective})={init_objective:.3f}")
    if args.init_M2:
        print("Init M2 source: explicit --init-M2 override")

    print(f"=== block2_m2_pair_beam.py: rank={args.rank} rounds={args.rounds} pool={args.pair_pool} beam={args.beam_width} max_pairs={args.max_pairs} max_radius={args.max_radius} ===")

    t0 = time.time()
    base_M2 = list(m2_init)
    bit_domain = list(range(16 * 32))  # 512 bits

    # Step 1: build pair pool (single 2-bit deltas from base)
    print("[1] Building pair pool...")
    all_pairs = []
    for i, j in itertools.combinations(bit_domain, 2):
        m2 = list(base_M2)
        for b in (i, j):
            slot = b // 32
            bit = b % 32
            m2[slot] ^= (1 << bit)
        hw, diff = eval_m2(iv1, iv2, m1_W, m2, args.rounds)
        lane_hw = hw_per_lane(diff)
        pair_objective = objective_value(hw, lane_hw, args.pair_rank, lane_weights, args.cg_weight)
        all_pairs.append({
            "bit_indices": [i, j],
            "hw_total": hw,
            "lane_hw": lane_hw,
            "objective": round(pair_objective, 6),
        })
    all_pairs.sort(key=lambda p: (p["objective"], p["hw_total"]))
    top_pairs = all_pairs[:args.pair_pool]
    pool_hw_min = top_pairs[0]["hw_total"]
    pool_hw_max = top_pairs[-1]["hw_total"]
    print(f"  pair pool: {len(all_pairs)} -> top {len(top_pairs)} (HW range {pool_hw_min}..{pool_hw_max})")

    # Step 2: beam search composing top pairs
    # State = (frozenset of bit indices flipped, hw)
    print("[2] Beam search...")
    initial = {
        "bits": frozenset(),
        "hw": init_hw,
        "lane_hw": init_lane_hw,
        "objective": init_objective,
        "depth": 0,
        "M2": tuple(base_M2),
    }
    beam = [initial]
    n_new_records = 0
    top_records = []
    seen_states = {frozenset(): True}

    for depth in range(1, args.max_pairs + 1):
        next_beam = []
        for state in beam:
            cur_bits = state["bits"]
            cur_M2 = state["M2"]
            cur_radius = len(cur_bits)
            for pair in top_pairs:
                pair_bits = frozenset(pair["bit_indices"])
                new_bits = cur_bits ^ pair_bits  # XOR = symmetric diff
                if len(new_bits) > args.max_radius:
                    continue
                # Re-evaluate with M2 updated
                new_M2 = list(cur_M2)
                for b in pair["bit_indices"]:
                    slot = b // 32
                    bit = b % 32
                    new_M2[slot] ^= (1 << bit)
                hw, diff = eval_m2(iv1, iv2, m1_W, tuple(new_M2), args.rounds)
                lane_hw = hw_per_lane(diff)
                state_objective = objective_value(hw, lane_hw, args.objective, lane_weights, args.cg_weight)
                key = new_bits
                if key in seen_states:
                    continue
                seen_states[key] = True
                next_beam.append({
                    "bits": key,
                    "hw": hw,
                    "lane_hw": lane_hw,
                    "objective": state_objective,
                    "depth": depth,
                    "M2": tuple(new_M2),
                })
                if hw < init_hw:
                    n_new_records += 1
                    record = {
                        "hw": hw,
                        "lane_hw": lane_hw,
                        "objective": round(state_objective, 6),
                        "M2": [f"0x{w:08x}" for w in new_M2],
                        "bits": sorted(new_bits),
                        "depth": depth,
                    }
                    if len(top_records) < args.top_records:
                        top_records.append(record)
                        top_records.sort(key=record_sort_key)
                    elif record_sort_key(record) < record_sort_key(top_records[-1]):
                        top_records[-1] = record
                        top_records.sort(key=record_sort_key)
        next_beam.sort(key=lambda s: (s["objective"], s["hw"]))
        beam = next_beam[:args.beam_width]
        if beam:
            best_hw_at_depth = min(s["hw"] for s in beam)
            print(
                f"  depth {depth}: kept={len(beam)} "
                f"best_hw={best_hw_at_depth} best_obj={beam[0]['objective']:.3f}"
            )
        else:
            print(f"  depth {depth}: empty beam, stopping")
            break

    wall = time.time() - t0
    print(f"\nTotal wall: {wall:.1f}s")

    top_records.sort(key=record_sort_key)
    # Best seen across the seed, the final beam, and all records observed
    # during earlier depths. Earlier-depth records can fall out of the final
    # beam, so they must still be considered for the summary.
    best_seen_hw = initial["hw"]
    best_seen_m2 = [f"0x{w:08x}" for w in initial["M2"]]
    best_seen_lane_hw = initial["lane_hw"]
    best_seen_depth = initial["depth"]
    best_seen_source = "init"
    if beam:
        beam_best = min(beam, key=lambda s: s["hw"])
        if beam_best["hw"] < best_seen_hw:
            best_seen_hw = beam_best["hw"]
            best_seen_m2 = [f"0x{w:08x}" for w in beam_best["M2"]]
            best_seen_lane_hw = beam_best["lane_hw"]
            best_seen_depth = beam_best["depth"]
            best_seen_source = "final_beam"
    if top_records and top_records[0]["hw"] < best_seen_hw:
        best_seen_hw = top_records[0]["hw"]
        best_seen_m2 = top_records[0]["M2"]
        best_seen_lane_hw = top_records[0]["lane_hw"]
        best_seen_depth = top_records[0]["depth"]
        best_seen_source = "new_records"
    print(f"best seen HW={best_seen_hw} source={best_seen_source}")
    if n_new_records:
        print(f"new records (HW < init {init_hw}): {n_new_records}; best HW={top_records[0]['hw']}")

    out = {
        "description": "F534+ block2 M2 pair beam — Yale F519 recommended next operator",
        "label": args.label,
        "seed_jsonl": args.seed_jsonl,
        "seed_rank": args.rank,
        "rounds": args.rounds,
        "pair_pool": args.pair_pool,
        "objective": args.objective,
        "pair_rank": args.pair_rank,
        "lane_weights": lane_weights,
        "cg_weight": args.cg_weight,
        "beam_width": args.beam_width,
        "max_pairs": args.max_pairs,
        "max_radius": args.max_radius,
        "init_M2": [f"0x{w:08x}" for w in m2_init],
        "seed_M2": [f"0x{w:08x}" for w in seed_m2],
        "init_M2_overridden": bool(args.init_M2),
        "init_hw": init_hw,
        "absorber_best_hw_claimed": absorber_best_hw,
        "best_seen_hw": best_seen_hw,
        "best_seen_M2": best_seen_m2,
        "best_seen_lane_hw": best_seen_lane_hw,
        "best_seen_depth": best_seen_depth,
        "best_seen_source": best_seen_source,
        "n_new_records": n_new_records,
        "top_records": top_records,
        "wall_seconds": round(wall, 2),
    }
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
