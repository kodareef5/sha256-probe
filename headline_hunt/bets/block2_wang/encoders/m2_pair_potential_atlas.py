#!/usr/bin/env python3
"""Enumerate two-bit M2 move geometry around an absorber witness.

This is an atlas, not a beam search. For every two-bit flip in the 512-bit M2
mask space, evaluate the 24-round absorber residual and record how the lane HW
vector changes relative to the witness. The goal is to identify repair
directions and target-lane moves that the beam objective may not select.
"""

import argparse
from itertools import combinations
import json
from pathlib import Path
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

REGS = ["a", "b", "c", "d", "e", "f", "g", "h"]


def parse_target_lane(raw):
    if not raw:
        return None
    parts = [int(p.strip()) for p in raw.split(",") if p.strip()]
    if len(parts) != 8:
        raise SystemExit(f"--target-lane needs 8 comma-separated integers, got {len(parts)}")
    return parts


def bit_label(bit_index):
    return {
        "index": bit_index,
        "word": bit_index // 32,
        "bit": bit_index % 32,
    }


def flip_pair(base_m2, pair):
    m2 = list(base_m2)
    for bit_index in pair:
        word = bit_index // 32
        bit = bit_index % 32
        m2[word] ^= 1 << bit
    return m2


def trim_top(entries, key, limit):
    return sorted(entries, key=key)[:limit]


def l1_distance(left, right):
    if right is None:
        return None
    return sum(abs(a - b) for a, b in zip(left, right))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed-jsonl", required=True)
    ap.add_argument("--rank", type=int, default=0)
    ap.add_argument("--rounds", type=int, default=24)
    ap.add_argument("--init-M2", required=True)
    ap.add_argument("--init-hw", type=int, required=True)
    ap.add_argument("--target-lane", default="", help="Optional 8-int lane target, comma-separated.")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--cg-weight", type=float, default=2.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    target_lane = parse_target_lane(args.target_lane)
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
    init_target_l1 = l1_distance(init_lane, target_lane)

    print(
        f"=== m2_pair_potential_atlas.py: rank={args.rank}/{total} "
        f"rounds={args.rounds} init_hw={init_hw} ==="
    )
    t0 = time.time()
    entries = []
    bit_domain = range(16 * 32)
    for pair in combinations(bit_domain, 2):
        m2 = flip_pair(base_m2, pair)
        hw, diff = eval_m2(iv1, iv2, m1_w, m2, args.rounds)
        lane = hw_per_lane(diff)
        delta = [lane[i] - init_lane[i] for i in range(8)]
        repairs = [max(0, -d) for d in delta]
        damage = [max(0, d) for d in delta]
        cg_obj = objective_value(hw, lane, "cg", [1.0] * 8, args.cg_weight)
        target_l1 = l1_distance(lane, target_lane)
        entries.append({
            "bits": [bit_label(pair[0]), bit_label(pair[1])],
            "bit_indices": list(pair),
            "hw_total": hw,
            "lane_hw": lane,
            "delta_lane_hw": delta,
            "net_delta": hw - init_hw,
            "cg_objective": round(cg_obj, 6),
            "cg_delta": round(cg_obj - init_cg, 6),
            "total_repair": sum(repairs),
            "total_damage": sum(damage),
            "target_l1": target_l1,
            "target_l1_delta": None if target_l1 is None else target_l1 - init_target_l1,
            "M2": [f"0x{x:08x}" for x in m2],
        })

    best_by_hw = trim_top(entries, lambda e: (e["hw_total"], e["cg_objective"], e["bit_indices"]), args.top)
    best_by_cg = trim_top(entries, lambda e: (e["cg_objective"], e["hw_total"], e["bit_indices"]), args.top)
    best_by_repair = trim_top(
        entries,
        lambda e: (-e["total_repair"], e["net_delta"], e["total_damage"], e["bit_indices"]),
        args.top,
    )
    best_by_target = []
    if target_lane is not None:
        best_by_target = trim_top(
            entries,
            lambda e: (e["target_l1"], e["hw_total"], e["cg_objective"], e["bit_indices"]),
            args.top,
        )

    per_register_repairs = {}
    for idx, reg in enumerate(REGS):
        per_register_repairs[reg] = trim_top(
            [entry for entry in entries if entry["delta_lane_hw"][idx] < 0],
            lambda e, i=idx: (e["delta_lane_hw"][i], e["net_delta"], e["total_damage"], e["bit_indices"]),
            args.top,
        )

    improving_hw = sum(1 for e in entries if e["hw_total"] < init_hw)
    nonworse_hw = sum(1 for e in entries if e["hw_total"] <= init_hw)
    improving_cg = sum(1 for e in entries if e["cg_objective"] < init_cg)
    improving_target = (
        None if target_lane is None else sum(1 for e in entries if e["target_l1"] < init_target_l1)
    )
    wall = time.time() - t0
    payload = {
        "description": f"{args.label}: M2 pair-potential atlas" if args.label else "M2 pair-potential atlas",
        "label": args.label,
        "seed_jsonl": args.seed_jsonl,
        "seed_rank": args.rank,
        "rounds": args.rounds,
        "init_M2": [f"0x{x:08x}" for x in base_m2],
        "init_hw": init_hw,
        "init_lane_hw": init_lane,
        "init_cg_objective": round(init_cg, 6),
        "target_lane_hw": target_lane,
        "init_target_l1": init_target_l1,
        "counts": {
            "total_pairs": len(entries),
            "hw_lt_init": improving_hw,
            "hw_le_init": nonworse_hw,
            "cg_lt_init": improving_cg,
            "target_l1_lt_init": improving_target,
        },
        "best_by_hw": best_by_hw,
        "best_by_cg": best_by_cg,
        "best_by_total_repair": best_by_repair,
        "best_by_target_l1": best_by_target,
        "per_register_repairs": per_register_repairs,
        "wall_seconds": round(wall, 2),
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(
        f"  pairs={len(entries)} hw<init={improving_hw} "
        f"cg<init={improving_cg} target<init={improving_target}"
    )
    print(f"  best HW pair: {best_by_hw[0]['hw_total']} delta={best_by_hw[0]['net_delta']}")
    print(f"  best c/g pair: obj={best_by_cg[0]['cg_objective']} hw={best_by_cg[0]['hw_total']}")
    if best_by_target:
        print(f"  best target-L1 pair: l1={best_by_target[0]['target_l1']} hw={best_by_target[0]['hw_total']}")
    print(f"Total wall: {wall:.1f}s")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
