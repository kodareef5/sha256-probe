#!/usr/bin/env python3
"""Compose selected M2 pair-potential moves non-greedily.

The pair-potential atlas can reveal moves that improve a target lane signature
only by raising total HW. This pilot selects those target-lane moves plus
repair moves, then evaluates fixed-size combinations by final state only.
"""

import argparse
from itertools import combinations
import json
from pathlib import Path
import random
import sys
import time

REPO = Path(__file__).resolve().parents[4]
ENCODERS = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(ENCODERS))

from block2_m2_pair_beam import (  # noqa: E402
    IV,
    MASK,
    eval_m2,
    expand_schedule,
    hw_per_lane,
    load_seed,
    objective_value,
    parse_m2_override,
    parse_w_arr,
)


def l1_distance(left, right):
    return sum(abs(a - b) for a, b in zip(left, right))


def flip_bits(base_m2, bits):
    m2 = list(base_m2)
    for bit_index in bits:
        word = bit_index // 32
        bit = bit_index % 32
        m2[word] ^= 1 << bit
    return m2


def pair_key(entry):
    return tuple(sorted(entry["bit_indices"]))


def add_entries(selected, entries, limit, source):
    for entry in entries[:limit]:
        key = pair_key(entry)
        if key not in selected:
            copied = dict(entry)
            copied["selection_sources"] = [source]
            selected[key] = copied
        elif source not in selected[key]["selection_sources"]:
            selected[key]["selection_sources"].append(source)


def keep_top(items, entry, limit, key):
    items.append(entry)
    items.sort(key=key)
    del items[limit:]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed-jsonl", required=True)
    ap.add_argument("--rank", type=int, default=0)
    ap.add_argument("--rounds", type=int, default=24)
    ap.add_argument("--init-M2", required=True)
    ap.add_argument("--init-hw", type=int, required=True)
    ap.add_argument("--pair-atlas", required=True)
    ap.add_argument("--target-pairs", type=int, default=64)
    ap.add_argument("--repair-pairs", type=int, default=64)
    ap.add_argument("--hw-pairs", type=int, default=16)
    ap.add_argument("--cg-pairs", type=int, default=16)
    ap.add_argument("--per-reg-pairs", type=int, default=8)
    ap.add_argument("--pair-count", type=int, default=3)
    ap.add_argument("--min-radius", type=int, default=4)
    ap.add_argument("--max-radius", type=int, default=8)
    ap.add_argument("--top-records", type=int, default=30)
    ap.add_argument("--cg-weight", type=float, default=2.0)
    ap.add_argument(
        "--sample-combos",
        type=int,
        default=0,
        help="If nonzero, sample this many pair-index combinations instead of exact enumeration.",
    )
    ap.add_argument("--rng-seed", type=int, default=0)
    ap.add_argument("--progress-every", type=int, default=0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    seed, total = load_seed(args.seed_jsonl, args.rank)
    diff63 = parse_w_arr(seed["block1_diff63"])
    base_m2 = parse_m2_override(args.init_M2)
    iv1 = list(IV)
    iv2 = [iv1[i] ^ diff63[i] & MASK for i in range(8)]
    m1_w = expand_schedule([0] * 16)

    init_hw, init_diff = eval_m2(iv1, iv2, m1_w, base_m2, args.rounds)
    if init_hw != args.init_hw:
        raise SystemExit(f"--init-hw mismatch: expected {args.init_hw}, evaluated {init_hw}")
    init_lane = hw_per_lane(init_diff)
    init_cg = objective_value(init_hw, init_lane, "cg", [1.0] * 8, args.cg_weight)

    with open(args.pair_atlas) as f:
        atlas = json.load(f)
    target_lane = atlas.get("target_lane_hw")
    if not target_lane:
        raise SystemExit("pair atlas lacks target_lane_hw")
    init_target_l1 = l1_distance(init_lane, target_lane)

    selected = {}
    add_entries(selected, atlas.get("best_by_target_l1", []), args.target_pairs, "target")
    add_entries(selected, atlas.get("best_by_total_repair", []), args.repair_pairs, "repair")
    add_entries(selected, atlas.get("best_by_hw", []), args.hw_pairs, "hw")
    add_entries(selected, atlas.get("best_by_cg", []), args.cg_pairs, "cg")
    for reg, entries in (atlas.get("per_register_repairs") or {}).items():
        add_entries(selected, entries, args.per_reg_pairs, f"repair_{reg}")
    selected_pairs = sorted(
        selected.values(),
        key=lambda e: (
            e.get("target_l1", 999),
            e.get("hw_total", 999),
            e.get("cg_objective", 999),
            e["bit_indices"],
        ),
    )

    print(
        f"=== m2_target_pair_combo.py: rank={args.rank}/{total} "
        f"selected_pairs={len(selected_pairs)} pair_count={args.pair_count} ==="
    )
    t0 = time.time()
    counts = {
        "candidate_combos": 0,
        "skipped_radius": 0,
        "skipped_duplicate": 0,
        "evaluated": 0,
        "hw_lt_init": 0,
        "hw_le_init": 0,
        "cg_lt_init": 0,
        "target_l1_lt_init": 0,
    }
    seen = set()
    top_by_hw = []
    top_by_target = []
    top_by_cg = []
    top_records = []

    if args.sample_combos:
        rng = random.Random(args.rng_seed)

        def combo_iter():
            for _ in range(args.sample_combos):
                yield tuple(sorted(rng.sample(range(len(selected_pairs)), args.pair_count)))

    else:

        def combo_iter():
            yield from combinations(range(len(selected_pairs)), args.pair_count)

    for combo_ids in combo_iter():
        counts["candidate_combos"] += 1
        if args.progress_every and counts["candidate_combos"] % args.progress_every == 0:
            elapsed = time.time() - t0
            print(
                f"  progress combos={counts['candidate_combos']} "
                f"evaluated={counts['evaluated']} hw<init={counts['hw_lt_init']} "
                f"hw<=init={counts['hw_le_init']} target<init={counts['target_l1_lt_init']} "
                f"elapsed={elapsed:.1f}s",
                flush=True,
            )
        bits = tuple(sorted({b for idx in combo_ids for b in selected_pairs[idx]["bit_indices"]}))
        radius = len(bits)
        if radius < args.min_radius or radius > args.max_radius:
            counts["skipped_radius"] += 1
            continue
        if bits in seen:
            counts["skipped_duplicate"] += 1
            continue
        seen.add(bits)
        m2 = flip_bits(base_m2, bits)
        hw, diff = eval_m2(iv1, iv2, m1_w, m2, args.rounds)
        lane = hw_per_lane(diff)
        cg_obj = objective_value(hw, lane, "cg", [1.0] * 8, args.cg_weight)
        target_l1 = l1_distance(lane, target_lane)
        entry = {
            "pair_ids": list(combo_ids),
            "bits": list(bits),
            "radius": radius,
            "hw_total": hw,
            "net_delta": hw - init_hw,
            "lane_hw": lane,
            "cg_objective": round(cg_obj, 6),
            "cg_delta": round(cg_obj - init_cg, 6),
            "target_l1": target_l1,
            "target_l1_delta": target_l1 - init_target_l1,
            "pair_sources": [selected_pairs[idx].get("selection_sources", []) for idx in combo_ids],
            "M2": [f"0x{x:08x}" for x in m2],
        }
        counts["evaluated"] += 1
        if hw < init_hw:
            counts["hw_lt_init"] += 1
        if hw <= init_hw:
            counts["hw_le_init"] += 1
        if cg_obj < init_cg:
            counts["cg_lt_init"] += 1
        if target_l1 < init_target_l1:
            counts["target_l1_lt_init"] += 1
        keep_top(top_by_hw, entry, args.top_records, lambda e: (e["hw_total"], e["target_l1"], e["cg_objective"], e["bits"]))
        keep_top(top_by_target, entry, args.top_records, lambda e: (e["target_l1"], e["hw_total"], e["cg_objective"], e["bits"]))
        keep_top(top_by_cg, entry, args.top_records, lambda e: (e["cg_objective"], e["hw_total"], e["target_l1"], e["bits"]))
        if hw <= init_hw:
            keep_top(top_records, entry, args.top_records, lambda e: (e["hw_total"], e["target_l1"], e["cg_objective"], e["bits"]))

    wall = time.time() - t0
    payload = {
        "description": f"{args.label}: M2 target/repair pair combo" if args.label else "M2 target/repair pair combo",
        "label": args.label,
        "seed_jsonl": args.seed_jsonl,
        "seed_rank": args.rank,
        "rounds": args.rounds,
        "pair_atlas": args.pair_atlas,
        "init_M2": [f"0x{x:08x}" for x in base_m2],
        "init_hw": init_hw,
        "init_lane_hw": init_lane,
        "init_cg_objective": round(init_cg, 6),
        "target_lane_hw": target_lane,
        "init_target_l1": init_target_l1,
        "selection": {
            "target_pairs": args.target_pairs,
            "repair_pairs": args.repair_pairs,
            "hw_pairs": args.hw_pairs,
            "cg_pairs": args.cg_pairs,
            "per_reg_pairs": args.per_reg_pairs,
            "selected_pairs": len(selected_pairs),
            "pair_count": args.pair_count,
            "min_radius": args.min_radius,
            "max_radius": args.max_radius,
            "sample_combos": args.sample_combos,
            "rng_seed": args.rng_seed if args.sample_combos else None,
        },
        "counts": counts,
        "top_by_hw": top_by_hw,
        "top_by_target_l1": top_by_target,
        "top_by_cg": top_by_cg,
        "top_records_hw_le_init": top_records,
        "wall_seconds": round(wall, 2),
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(
        f"  evaluated={counts['evaluated']} hw<init={counts['hw_lt_init']} "
        f"hw<=init={counts['hw_le_init']} target<init={counts['target_l1_lt_init']}"
    )
    print(f"  best HW combo: {top_by_hw[0]['hw_total']} target_l1={top_by_hw[0]['target_l1']}")
    print(f"  best target combo: l1={top_by_target[0]['target_l1']} hw={top_by_target[0]['hw_total']}")
    print(f"Total wall: {wall:.1f}s")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
