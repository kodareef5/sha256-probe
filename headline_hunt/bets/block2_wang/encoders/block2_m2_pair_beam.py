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


def cg_objective(diff, penalty_weight=2.0):
    """HW + penalty_weight * (lane_c_hw + lane_g_hw). Lower is better."""
    hw_total = sum(bin(d).count("1") for d in diff)
    lane_c = bin(diff[2]).count("1")
    lane_g = bin(diff[6]).count("1")
    return hw_total + penalty_weight * (lane_c + lane_g)


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


def parse_target_lane(raw):
    if not raw:
        return None
    parts = [int(p.strip()) for p in raw.split(",") if p.strip()]
    if len(parts) != 8:
        raise SystemExit(f"--target-lane needs 8 comma-separated integers, got {len(parts)}")
    return parts


def parse_word_caps(raw_caps):
    caps = {}
    for raw in raw_caps or []:
        word_raw, count_raw = raw.split(":", 1)
        word = int(word_raw)
        count = int(count_raw)
        if not 0 <= word < 16:
            raise SystemExit(f"word cap index must be 0..15: {raw}")
        if count < 0:
            raise SystemExit(f"word cap count must be non-negative: {raw}")
        caps[word] = count
    return caps


def added_bits_in_word(base_m2, m2, word_idx):
    return bin((~base_m2[word_idx]) & m2[word_idx] & MASK).count("1")


def passes_added_word_caps(base_m2, m2, caps):
    for word_idx, cap in caps.items():
        if added_bits_in_word(base_m2, m2, word_idx) > cap:
            return False
    return True


def target_l1(lane_hw, target_lane):
    return sum(abs(a - b) for a, b in zip(lane_hw, target_lane))


def m2_weight(m2):
    return sum(bin(word).count("1") for word in m2)


def m2_transition_counts(base_m2, m2):
    added = 0
    removed = 0
    for base_word, word in zip(base_m2, m2):
        added += bin((~base_word) & word & MASK).count("1")
        removed += bin(base_word & (~word) & MASK).count("1")
    return added, removed, added - removed


def shape_objective_adjustment(added, removed, net_add_penalty, removed_bonus):
    return net_add_penalty * float(max(0, added - removed)) - removed_bonus * float(removed)


def objective_value(
    hw_total,
    lane_hw,
    objective,
    lane_weights,
    cg_weight,
    target_lane=None,
    target_weight=1.0,
    m2_popcount=0,
    m2_weight_penalty=0.0,
):
    if objective == "hw":
        return float(hw_total)
    if objective == "cg":
        return float(hw_total) + cg_weight * float(lane_hw[2] + lane_hw[6])
    if objective == "sparse":
        return float(hw_total) + m2_weight_penalty * float(m2_popcount)
    if objective == "weighted":
        return sum(w * h for w, h in zip(lane_weights, lane_hw))
    if objective == "target":
        if target_lane is None:
            raise ValueError("target objective requires target_lane")
        return float(hw_total) + target_weight * float(target_l1(lane_hw, target_lane))
    if objective == "target_sparse":
        if target_lane is None:
            raise ValueError("target_sparse objective requires target_lane")
        return (
            float(hw_total)
            + target_weight * float(target_l1(lane_hw, target_lane))
            + m2_weight_penalty * float(m2_popcount)
        )
    if objective == "cg_target":
        if target_lane is None:
            raise ValueError("cg_target objective requires target_lane")
        return (
            float(hw_total)
            + cg_weight * float(lane_hw[2] + lane_hw[6])
            + target_weight * float(target_l1(lane_hw, target_lane))
        )
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
    objective_choices = ["hw", "cg", "sparse", "weighted", "target", "target_sparse", "cg_target"]
    ap.add_argument("--objective", choices=objective_choices, default="hw",
                    help="Beam objective: total HW, total HW plus c/g penalty, or weighted lane HW.")
    ap.add_argument("--pair-rank", choices=objective_choices, default=None,
                    help="Pair-pool ranking objective; default matches --objective.")
    ap.add_argument("--lane-weights", default="",
                    help="Eight comma-separated weights for --objective weighted.")
    ap.add_argument("--cg-weight", type=float, default=1.0,
                    help="Penalty multiplier on c+g lane HW for --objective cg.")
    ap.add_argument("--target-lane", default="",
                    help="Eight comma-separated lane HW target for target/cg_target objectives.")
    ap.add_argument("--target-weight", type=float, default=1.0,
                    help="Penalty multiplier on L1 distance to --target-lane.")
    ap.add_argument("--m2-weight-penalty", type=float, default=0.0,
                    help="Penalty multiplier on M2 popcount for sparse/target_sparse objectives.")
    ap.add_argument("--shape-net-add-penalty", type=float, default=0.0,
                    help="Extra objective penalty per net added M2 bit relative to init M2.")
    ap.add_argument("--shape-removed-bonus", type=float, default=0.0,
                    help="Extra objective bonus per removed init-M2 bit relative to init M2.")
    ap.add_argument("--min-m2-weight", type=int, default=None,
                    help="Reject pair/beam states with M2 popcount below this value.")
    ap.add_argument("--max-m2-weight", type=int, default=None,
                    help="Reject pair/beam states with M2 popcount above this value.")
    ap.add_argument("--max-added-word", action="append", default=[],
                    help="Reject states adding more than COUNT new bits to WORD relative to init M2. "
                         "Format WORD:COUNT; may be repeated.")
    ap.add_argument("--max-target-l1", type=int, default=None,
                    help="Reject beam states with L1(lane, target-lane) above this cap.")
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
    target_lane = parse_target_lane(args.target_lane)
    added_word_caps = parse_word_caps(args.max_added_word)
    target_objectives = ("target", "target_sparse", "cg_target")
    if (args.objective in target_objectives or args.pair_rank in target_objectives) and target_lane is None:
        raise SystemExit("--target-lane is required for target/target_sparse/cg_target objective or pair-rank")
    if args.max_target_l1 is not None and target_lane is None:
        raise SystemExit("--target-lane is required for --max-target-l1")

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
    init_m2_weight = m2_weight(m2_init)
    init_m2_added, init_m2_removed, init_m2_net_added = m2_transition_counts(m2_init, m2_init)
    init_objective = objective_value(
        init_hw,
        init_lane_hw,
        args.objective,
        lane_weights,
        args.cg_weight,
        target_lane,
        args.target_weight,
        init_m2_weight,
        args.m2_weight_penalty,
    )
    init_objective += shape_objective_adjustment(
        init_m2_added,
        init_m2_removed,
        args.shape_net_add_penalty,
        args.shape_removed_bonus,
    )
    print(f"Init lane HW: {init_lane_hw} (sum={init_hw})")
    print(f"Init M2 weight: {init_m2_weight}")
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
        pair_m2_weight = m2_weight(m2)
        pair_added, pair_removed, pair_net_added = m2_transition_counts(base_M2, m2)
        if args.min_m2_weight is not None and pair_m2_weight < args.min_m2_weight:
            continue
        if args.max_m2_weight is not None and pair_m2_weight > args.max_m2_weight:
            continue
        if added_word_caps and not passes_added_word_caps(base_M2, m2, added_word_caps):
            continue
        pair_objective = objective_value(
            hw,
            lane_hw,
            args.pair_rank,
            lane_weights,
            args.cg_weight,
            target_lane,
            args.target_weight,
            pair_m2_weight,
            args.m2_weight_penalty,
        )
        pair_objective += shape_objective_adjustment(
            pair_added,
            pair_removed,
            args.shape_net_add_penalty,
            args.shape_removed_bonus,
        )
        all_pairs.append({
            "bit_indices": [i, j],
            "hw_total": hw,
            "lane_hw": lane_hw,
            "m2_weight": pair_m2_weight,
            "m2_added_bits": pair_added,
            "m2_removed_bits": pair_removed,
            "m2_net_added_bits": pair_net_added,
            "objective": round(pair_objective, 6),
        })
    all_pairs.sort(key=lambda p: (p["objective"], p["hw_total"]))
    if not all_pairs:
        raise SystemExit("pair pool is empty after M2-weight filtering")
    top_pairs = all_pairs[:args.pair_pool]
    pool_hw_min = min(pair["hw_total"] for pair in top_pairs)
    pool_hw_max = max(pair["hw_total"] for pair in top_pairs)
    pool_obj_min = min(pair["objective"] for pair in top_pairs)
    pool_obj_max = max(pair["objective"] for pair in top_pairs)
    print(
        f"  pair pool: {len(all_pairs)} -> top {len(top_pairs)} "
        f"(HW range {pool_hw_min}..{pool_hw_max}, objective range {pool_obj_min}..{pool_obj_max})"
    )

    # Step 2: beam search composing top pairs
    # State = (frozenset of bit indices flipped, hw)
    print("[2] Beam search...")
    initial = {
        "bits": frozenset(),
        "hw": init_hw,
        "lane_hw": init_lane_hw,
        "m2_weight": init_m2_weight,
        "m2_added_bits": init_m2_added,
        "m2_removed_bits": init_m2_removed,
        "m2_net_added_bits": init_m2_net_added,
        "objective": init_objective,
        "depth": 0,
        "M2": tuple(base_M2),
    }
    beam = [initial]
    best_objective_state = initial
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
                new_m2_weight = m2_weight(new_M2)
                new_added, new_removed, new_net_added = m2_transition_counts(base_M2, new_M2)
                if args.min_m2_weight is not None and new_m2_weight < args.min_m2_weight:
                    continue
                if args.max_m2_weight is not None and new_m2_weight > args.max_m2_weight:
                    continue
                if added_word_caps and not passes_added_word_caps(base_M2, new_M2, added_word_caps):
                    continue
                if args.max_target_l1 is not None and target_l1(lane_hw, target_lane) > args.max_target_l1:
                    continue
                state_objective = objective_value(
                    hw,
                    lane_hw,
                    args.objective,
                    lane_weights,
                    args.cg_weight,
                    target_lane,
                    args.target_weight,
                    new_m2_weight,
                    args.m2_weight_penalty,
                )
                state_objective += shape_objective_adjustment(
                    new_added,
                    new_removed,
                    args.shape_net_add_penalty,
                    args.shape_removed_bonus,
                )
                key = new_bits
                if key in seen_states:
                    continue
                seen_states[key] = True
                next_state = {
                    "bits": key,
                    "hw": hw,
                    "lane_hw": lane_hw,
                    "m2_weight": new_m2_weight,
                    "m2_added_bits": new_added,
                    "m2_removed_bits": new_removed,
                    "m2_net_added_bits": new_net_added,
                    "objective": state_objective,
                    "depth": depth,
                    "M2": tuple(new_M2),
                }
                next_beam.append(next_state)
                if (state_objective, hw) < (best_objective_state["objective"], best_objective_state["hw"]):
                    best_objective_state = next_state
                if hw < init_hw:
                    n_new_records += 1
                    record = {
                        "hw": hw,
                        "lane_hw": lane_hw,
                        "m2_weight": new_m2_weight,
                        "m2_added_bits": new_added,
                        "m2_removed_bits": new_removed,
                        "m2_net_added_bits": new_net_added,
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
    best_seen_m2_weight = initial["m2_weight"]
    best_seen_m2_added = initial["m2_added_bits"]
    best_seen_m2_removed = initial["m2_removed_bits"]
    best_seen_m2_net_added = initial["m2_net_added_bits"]
    best_seen_depth = initial["depth"]
    best_seen_source = "init"
    if beam:
        beam_best = min(beam, key=lambda s: s["hw"])
        if beam_best["hw"] < best_seen_hw:
            best_seen_hw = beam_best["hw"]
            best_seen_m2 = [f"0x{w:08x}" for w in beam_best["M2"]]
            best_seen_lane_hw = beam_best["lane_hw"]
            best_seen_m2_weight = beam_best["m2_weight"]
            best_seen_m2_added = beam_best["m2_added_bits"]
            best_seen_m2_removed = beam_best["m2_removed_bits"]
            best_seen_m2_net_added = beam_best["m2_net_added_bits"]
            best_seen_depth = beam_best["depth"]
            best_seen_source = "final_beam"
    if top_records and top_records[0]["hw"] < best_seen_hw:
        best_seen_hw = top_records[0]["hw"]
        best_seen_m2 = top_records[0]["M2"]
        best_seen_lane_hw = top_records[0]["lane_hw"]
        best_seen_m2_weight = top_records[0]["m2_weight"]
        best_seen_m2_added = top_records[0]["m2_added_bits"]
        best_seen_m2_removed = top_records[0]["m2_removed_bits"]
        best_seen_m2_net_added = top_records[0]["m2_net_added_bits"]
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
        "pair_pool_hw_min": pool_hw_min,
        "pair_pool_hw_max": pool_hw_max,
        "pair_pool_objective_min": pool_obj_min,
        "pair_pool_objective_max": pool_obj_max,
        "objective": args.objective,
        "pair_rank": args.pair_rank,
        "lane_weights": lane_weights,
        "cg_weight": args.cg_weight,
        "target_lane": target_lane,
        "target_weight": args.target_weight,
        "m2_weight_penalty": args.m2_weight_penalty,
        "shape_net_add_penalty": args.shape_net_add_penalty,
        "shape_removed_bonus": args.shape_removed_bonus,
        "min_m2_weight": args.min_m2_weight,
        "max_m2_weight": args.max_m2_weight,
        "max_added_word": dict(sorted(added_word_caps.items())),
        "max_target_l1": args.max_target_l1,
        "beam_width": args.beam_width,
        "max_pairs": args.max_pairs,
        "max_radius": args.max_radius,
        "init_M2": [f"0x{w:08x}" for w in m2_init],
        "seed_M2": [f"0x{w:08x}" for w in seed_m2],
        "init_M2_overridden": bool(args.init_M2),
        "init_hw": init_hw,
        "init_m2_weight": init_m2_weight,
        "init_m2_added_bits": init_m2_added,
        "init_m2_removed_bits": init_m2_removed,
        "init_m2_net_added_bits": init_m2_net_added,
        "absorber_best_hw_claimed": absorber_best_hw,
        "best_seen_hw": best_seen_hw,
        "best_seen_M2": best_seen_m2,
        "best_seen_lane_hw": best_seen_lane_hw,
        "best_seen_m2_weight": best_seen_m2_weight,
        "best_seen_m2_added_bits": best_seen_m2_added,
        "best_seen_m2_removed_bits": best_seen_m2_removed,
        "best_seen_m2_net_added_bits": best_seen_m2_net_added,
        "best_seen_depth": best_seen_depth,
        "best_seen_source": best_seen_source,
        "best_objective": round(best_objective_state["objective"], 6),
        "best_objective_hw": best_objective_state["hw"],
        "best_objective_lane_hw": best_objective_state["lane_hw"],
        "best_objective_m2_weight": best_objective_state["m2_weight"],
        "best_objective_m2_added_bits": best_objective_state["m2_added_bits"],
        "best_objective_m2_removed_bits": best_objective_state["m2_removed_bits"],
        "best_objective_m2_net_added_bits": best_objective_state["m2_net_added_bits"],
        "best_objective_depth": best_objective_state["depth"],
        "best_objective_bits": sorted(best_objective_state["bits"]),
        "best_objective_M2": [f"0x{w:08x}" for w in best_objective_state["M2"]],
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
