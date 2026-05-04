#!/usr/bin/env python3
"""Beam over selected M2 pair-potential moves from an atlas.

This sits between exact/sampled final-state combo search and the generic M2
pair beam. The pair pool is selected from a pair-potential atlas
(target/repair/HW/cg/per-register repair), then composed as a prefix beam with
optional target-lane objectives or caps.
"""

import argparse
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
    target_l1,
)


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


def reconstruct_selected_pairs(atlas, args):
    selected = {}
    add_entries(selected, atlas.get("best_by_target_l1", []), args.target_pairs, "target")
    add_entries(selected, atlas.get("best_by_total_repair", []), args.repair_pairs, "repair")
    add_entries(selected, atlas.get("best_by_hw", []), args.hw_pairs, "hw")
    add_entries(selected, atlas.get("best_by_cg", []), args.cg_pairs, "cg")
    for reg, entries in (atlas.get("per_register_repairs") or {}).items():
        add_entries(selected, entries, args.per_reg_pairs, f"repair_{reg}")
    return sorted(
        selected.values(),
        key=lambda e: (
            e.get("target_l1", 999),
            e.get("hw_total", 999),
            e.get("cg_objective", 999),
            e["bit_indices"],
        ),
    )


def flip_pair(m2, bit_indices):
    out = list(m2)
    for b in bit_indices:
        out[b // 32] ^= 1 << (b % 32)
    return tuple(out)


def keep_top(items, entry, limit, key):
    items.append(entry)
    items.sort(key=key)
    del items[limit:]


def record_sort_key(entry):
    return (entry["hw_total"], entry["target_l1"], entry["objective"], entry["bits"])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed-jsonl", required=True)
    ap.add_argument("--rank", type=int, default=0)
    ap.add_argument("--rounds", type=int, default=24)
    ap.add_argument("--init-M2", required=True)
    ap.add_argument("--init-hw", type=int, required=True)
    ap.add_argument("--pair-atlas", required=True)
    ap.add_argument("--target-pairs", type=int, default=40)
    ap.add_argument("--repair-pairs", type=int, default=40)
    ap.add_argument("--hw-pairs", type=int, default=16)
    ap.add_argument("--cg-pairs", type=int, default=16)
    ap.add_argument("--per-reg-pairs", type=int, default=4)
    ap.add_argument("--objective", choices=["hw", "cg", "target", "cg_target"], default="hw")
    ap.add_argument("--cg-weight", type=float, default=2.0)
    ap.add_argument("--target-weight", type=float, default=1.0)
    ap.add_argument("--max-target-l1", type=int, default=None)
    ap.add_argument("--beam-width", type=int, default=1024)
    ap.add_argument("--max-pairs", type=int, default=6)
    ap.add_argument("--max-radius", type=int, default=12)
    ap.add_argument("--top-records", type=int, default=30)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    seed, total = load_seed(args.seed_jsonl, args.rank)
    diff63 = parse_w_arr(seed["block1_diff63"])
    base_m2 = tuple(parse_m2_override(args.init_M2))
    iv1 = list(IV)
    iv2 = [iv1[i] ^ diff63[i] & MASK for i in range(8)]
    m1_w = expand_schedule([0] * 16)

    with open(args.pair_atlas) as f:
        atlas = json.load(f)
    target_lane = atlas.get("target_lane_hw")
    if target_lane is None:
        raise SystemExit("pair atlas lacks target_lane_hw")

    init_hw, init_diff = eval_m2(iv1, iv2, m1_w, base_m2, args.rounds)
    if init_hw != args.init_hw:
        raise SystemExit(f"--init-hw mismatch: expected {args.init_hw}, evaluated {init_hw}")
    init_lane = hw_per_lane(init_diff)
    init_target_l1 = target_l1(init_lane, target_lane)
    init_objective = objective_value(
        init_hw, init_lane, args.objective, [1.0] * 8, args.cg_weight, target_lane, args.target_weight
    )

    selected_pairs = reconstruct_selected_pairs(atlas, args)
    print(
        f"=== m2_atlas_pair_beam.py: rank={args.rank}/{total} "
        f"selected_pairs={len(selected_pairs)} objective={args.objective} ==="
    )
    print(f"init_hw={init_hw} init_lane={init_lane} init_target_l1={init_target_l1}")

    t0 = time.time()
    counts = {
        "expanded": 0,
        "skipped_radius": 0,
        "skipped_seen": 0,
        "skipped_target_l1": 0,
        "hw_lt_init": 0,
        "hw_le_init": 0,
        "target_l1_lt_init": 0,
    }
    initial = {
        "bits": frozenset(),
        "M2": base_m2,
        "hw_total": init_hw,
        "lane_hw": init_lane,
        "target_l1": init_target_l1,
        "objective": init_objective,
        "depth": 0,
        "pair_path": [],
        "pair_sources": [],
    }
    beam = [initial]
    seen = {frozenset()}
    top_records = []
    top_by_hw = []
    top_by_target = []
    top_by_objective = []

    for depth in range(1, args.max_pairs + 1):
        next_beam = []
        for state in beam:
            for pair_id, pair in enumerate(selected_pairs):
                pair_bits = frozenset(pair["bit_indices"])
                bits = state["bits"] ^ pair_bits
                if len(bits) > args.max_radius:
                    counts["skipped_radius"] += 1
                    continue
                if bits in seen:
                    counts["skipped_seen"] += 1
                    continue
                seen.add(bits)
                m2 = flip_pair(state["M2"], pair["bit_indices"])
                hw, diff = eval_m2(iv1, iv2, m1_w, m2, args.rounds)
                lane = hw_per_lane(diff)
                l1 = target_l1(lane, target_lane)
                if args.max_target_l1 is not None and l1 > args.max_target_l1:
                    counts["skipped_target_l1"] += 1
                    continue
                obj = objective_value(hw, lane, args.objective, [1.0] * 8, args.cg_weight, target_lane, args.target_weight)
                counts["expanded"] += 1
                if hw < init_hw:
                    counts["hw_lt_init"] += 1
                if hw <= init_hw:
                    counts["hw_le_init"] += 1
                if l1 < init_target_l1:
                    counts["target_l1_lt_init"] += 1
                entry = {
                    "bits": sorted(bits),
                    "radius": len(bits),
                    "hw_total": hw,
                    "net_delta": hw - init_hw,
                    "lane_hw": lane,
                    "target_l1": l1,
                    "target_l1_delta": l1 - init_target_l1,
                    "objective": round(obj, 6),
                    "depth": depth,
                    "pair_path": state["pair_path"] + [pair_id],
                    "pair_sources": state["pair_sources"] + [pair.get("selection_sources", [])],
                    "M2": [f"0x{x:08x}" for x in m2],
                }
                next_beam.append({
                    **entry,
                    "bits": bits,
                    "M2": m2,
                })
                compact = {**entry, "bits": sorted(bits), "M2": [f"0x{x:08x}" for x in m2]}
                keep_top(top_by_hw, compact, args.top_records, record_sort_key)
                keep_top(top_by_target, compact, args.top_records, lambda e: (e["target_l1"], e["hw_total"], e["objective"], e["bits"]))
                keep_top(top_by_objective, compact, args.top_records, lambda e: (e["objective"], e["hw_total"], e["target_l1"], e["bits"]))
                if hw <= init_hw:
                    keep_top(top_records, compact, args.top_records, record_sort_key)

        next_beam.sort(key=lambda s: (s["objective"], s["hw_total"], s["target_l1"]))
        beam = next_beam[: args.beam_width]
        if not beam:
            print(f"  depth {depth}: empty beam, stopping")
            break
        print(
            f"  depth {depth}: kept={len(beam)} "
            f"best_hw={min(s['hw_total'] for s in beam)} "
            f"best_obj={beam[0]['objective']:.3f} best_l1={min(s['target_l1'] for s in beam)}"
        )

    wall = time.time() - t0
    payload = {
        "description": f"{args.label}: M2 atlas pair beam" if args.label else "M2 atlas pair beam",
        "label": args.label,
        "seed_jsonl": args.seed_jsonl,
        "seed_rank": args.rank,
        "rounds": args.rounds,
        "pair_atlas": args.pair_atlas,
        "init_M2": [f"0x{x:08x}" for x in base_m2],
        "init_hw": init_hw,
        "init_lane_hw": init_lane,
        "target_lane_hw": target_lane,
        "init_target_l1": init_target_l1,
        "selection": {
            "target_pairs": args.target_pairs,
            "repair_pairs": args.repair_pairs,
            "hw_pairs": args.hw_pairs,
            "cg_pairs": args.cg_pairs,
            "per_reg_pairs": args.per_reg_pairs,
            "selected_pairs": len(selected_pairs),
        },
        "objective": args.objective,
        "cg_weight": args.cg_weight,
        "target_weight": args.target_weight,
        "max_target_l1": args.max_target_l1,
        "beam_width": args.beam_width,
        "max_pairs": args.max_pairs,
        "max_radius": args.max_radius,
        "counts": counts,
        "top_records_hw_le_init": top_records,
        "top_by_hw": top_by_hw,
        "top_by_target_l1": top_by_target,
        "top_by_objective": top_by_objective,
        "wall_seconds": round(wall, 2),
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(
        f"Total wall: {wall:.1f}s expanded={counts['expanded']} "
        f"hw<=init={counts['hw_le_init']} target<init={counts['target_l1_lt_init']}"
    )
    if top_by_hw:
        print(f"best HW: {top_by_hw[0]['hw_total']} target_l1={top_by_hw[0]['target_l1']}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
