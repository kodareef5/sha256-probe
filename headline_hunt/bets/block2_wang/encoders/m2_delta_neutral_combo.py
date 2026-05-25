#!/usr/bin/env python3
"""Meet-in-the-middle M2 combo search over standalone pair-delta signatures.

This is a selector for rare combos like F788 whose selected pairs have near-zero
standalone lane-delta sum. Random pair-combo sampling can miss those because
the neutral combinations are a tiny subset of the selected-pair pool.
"""

import argparse
from collections import defaultdict
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


def l1_distance(left, right):
    return sum(abs(a - b) for a, b in zip(left, right))


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


def reconstruct_selected_pairs(atlas, selection):
    selected = {}
    add_entries(selected, atlas.get("best_by_target_l1", []), selection["target_pairs"], "target")
    add_entries(selected, atlas.get("best_by_total_repair", []), selection["repair_pairs"], "repair")
    add_entries(selected, atlas.get("best_by_hw", []), selection["hw_pairs"], "hw")
    add_entries(selected, atlas.get("best_by_cg", []), selection["cg_pairs"], "cg")
    for reg, entries in (atlas.get("per_register_repairs") or {}).items():
        add_entries(selected, entries, selection["per_reg_pairs"], f"repair_{reg}")
    return sorted(
        selected.values(),
        key=lambda e: (
            e.get("target_l1", 999),
            e.get("hw_total", 999),
            e.get("cg_objective", 999),
            e["bit_indices"],
        ),
    )


def flip_bits(base_m2, bits):
    m2 = list(base_m2)
    for bit_index in bits:
        word = bit_index // 32
        bit = bit_index % 32
        m2[word] ^= 1 << bit
    return m2


def m2_transition_counts(base_m2, m2):
    added = 0
    removed = 0
    for base_word, word in zip(base_m2, m2):
        added += bin((~base_word) & word & MASK).count("1")
        removed += bin(base_word & (~word) & MASK).count("1")
    return added, removed, added - removed


def vector_add(left, right):
    return tuple(a + b for a, b in zip(left, right))


def vector_neg(values):
    return tuple(-value for value in values)


def keep_top(items, entry, limit, key):
    items.append(entry)
    items.sort(key=key)
    del items[limit:]


def source_lists(selected_pairs, combo_ids):
    return [selected_pairs[idx].get("selection_sources", []) for idx in combo_ids]


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
    ap.add_argument("--pair-count", type=int, default=6)
    ap.add_argument("--max-standalone-net-delta-sum", type=int, default=0)
    ap.add_argument("--min-radius", type=int, default=8)
    ap.add_argument("--max-radius", type=int, default=12)
    ap.add_argument("--max-evals", type=int, default=10000)
    ap.add_argument("--top-records", type=int, default=30)
    ap.add_argument("--cg-weight", type=float, default=2.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()
    if args.pair_count % 2:
        raise SystemExit("--pair-count must be even for meet-in-the-middle search")

    seed, total = load_seed(args.seed_jsonl, args.rank)
    diff63 = parse_w_arr(seed["block1_diff63"])
    base_m2 = parse_m2_override(args.init_M2)
    iv1 = list(IV)
    iv2 = [(iv1[idx] ^ diff63[idx]) & MASK for idx in range(8)]
    m1_w = expand_schedule([0] * 16)

    init_hw, init_diff = eval_m2(iv1, iv2, m1_w, base_m2, args.rounds)
    if init_hw != args.init_hw:
        raise SystemExit(f"--init-hw mismatch: expected {args.init_hw}, evaluated {init_hw}")
    init_lane = hw_per_lane(init_diff)
    init_cg = objective_value(init_hw, init_lane, "cg", [1.0] * 8, args.cg_weight)

    atlas = json.loads(Path(args.pair_atlas).read_text())
    target_lane = atlas.get("target_lane_hw")
    if not target_lane:
        raise SystemExit("pair atlas lacks target_lane_hw")
    init_target_l1 = l1_distance(init_lane, target_lane)

    selection = {
        "target_pairs": args.target_pairs,
        "repair_pairs": args.repair_pairs,
        "hw_pairs": args.hw_pairs,
        "cg_pairs": args.cg_pairs,
        "per_reg_pairs": args.per_reg_pairs,
    }
    selected_pairs = reconstruct_selected_pairs(atlas, selection)
    half_count = args.pair_count // 2

    print(
        f"=== m2_delta_neutral_combo.py: rank={args.rank}/{total} "
        f"selected_pairs={len(selected_pairs)} pair_count={args.pair_count} ==="
    )
    t0 = time.time()
    partials_by_delta = defaultdict(list)
    partial_count = 0
    kept_partial_count = 0
    for combo_ids in combinations(range(len(selected_pairs)), half_count):
        partial_count += 1
        delta = [0] * 8
        standalone_sum = 0
        bits = set()
        for idx in combo_ids:
            pair = selected_pairs[idx]
            standalone_sum += pair["hw_total"] - init_hw
            for lane_idx, value in enumerate(pair["delta_lane_hw"]):
                delta[lane_idx] += value
            bits.update(pair["bit_indices"])
        if standalone_sum > args.max_standalone_net_delta_sum:
            continue
        kept_partial_count += 1
        partials_by_delta[tuple(delta)].append({
            "ids": combo_ids,
            "standalone_sum": standalone_sum,
            "bits": frozenset(bits),
        })

    counts = {
        "partial_combos": partial_count,
        "kept_partials": kept_partial_count,
        "delta_buckets": len(partials_by_delta),
        "candidate_matches": 0,
        "skipped_pair_id_overlap": 0,
        "skipped_radius": 0,
        "skipped_duplicate_bits": 0,
        "evaluated": 0,
        "hw_lt_init": 0,
        "hw_le_init": 0,
        "cg_lt_init": 0,
        "target_l1_lt_init": 0,
    }
    seen_bits = set()
    top_by_hw = []
    top_by_target = []
    top_by_cg = []
    top_records = []

    for delta, left_partials in partials_by_delta.items():
        right_partials = partials_by_delta.get(vector_neg(delta), [])
        if not right_partials:
            continue
        for left in left_partials:
            left_ids = set(left["ids"])
            for right in right_partials:
                if left["ids"] >= right["ids"]:
                    continue
                counts["candidate_matches"] += 1
                if left_ids.intersection(right["ids"]):
                    counts["skipped_pair_id_overlap"] += 1
                    continue
                combo_ids = tuple(sorted(left["ids"] + right["ids"]))
                bits = frozenset(left["bits"] ^ right["bits"])
                radius = len(bits)
                if radius < args.min_radius or radius > args.max_radius:
                    counts["skipped_radius"] += 1
                    continue
                if bits in seen_bits:
                    counts["skipped_duplicate_bits"] += 1
                    continue
                seen_bits.add(bits)

                m2 = flip_bits(base_m2, bits)
                m2_added, m2_removed, m2_net_added = m2_transition_counts(base_m2, m2)
                hw, diff = eval_m2(iv1, iv2, m1_w, m2, args.rounds)
                lane = hw_per_lane(diff)
                cg_obj = objective_value(hw, lane, "cg", [1.0] * 8, args.cg_weight)
                target_l1 = l1_distance(lane, target_lane)
                standalone_sum = left["standalone_sum"] + right["standalone_sum"]
                entry = {
                    "pair_ids": list(combo_ids),
                    "bits": sorted(bits),
                    "radius": radius,
                    "m2_added_bits": m2_added,
                    "m2_removed_bits": m2_removed,
                    "m2_net_added_bits": m2_net_added,
                    "hw_total": hw,
                    "net_delta": hw - init_hw,
                    "lane_hw": lane,
                    "cg_objective": round(cg_obj, 6),
                    "cg_delta": round(cg_obj - init_cg, 6),
                    "target_l1": target_l1,
                    "target_l1_delta": target_l1 - init_target_l1,
                    "standalone_net_delta_sum": standalone_sum,
                    "delta_lane_sum": list(vector_add(delta, vector_neg(delta))),
                    "pair_sources": source_lists(selected_pairs, combo_ids),
                    "M2": [f"0x{word:08x}" for word in m2],
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
                keep_top(
                    top_by_hw,
                    entry,
                    args.top_records,
                    lambda item: (item["hw_total"], item["target_l1"], item["cg_objective"], item["bits"]),
                )
                keep_top(
                    top_by_target,
                    entry,
                    args.top_records,
                    lambda item: (item["target_l1"], item["hw_total"], item["cg_objective"], item["bits"]),
                )
                keep_top(
                    top_by_cg,
                    entry,
                    args.top_records,
                    lambda item: (item["cg_objective"], item["hw_total"], item["target_l1"], item["bits"]),
                )
                if hw <= init_hw:
                    keep_top(
                        top_records,
                        entry,
                        args.top_records,
                        lambda item: (item["hw_total"], item["target_l1"], item["cg_objective"], item["bits"]),
                    )
                if counts["evaluated"] >= args.max_evals:
                    break
            if counts["evaluated"] >= args.max_evals:
                break
        if counts["evaluated"] >= args.max_evals:
            break

    wall = time.time() - t0
    payload = {
        "description": f"{args.label}: M2 delta-neutral combo search" if args.label else "M2 delta-neutral combo search",
        "label": args.label,
        "seed_jsonl": args.seed_jsonl,
        "seed_rank": args.rank,
        "rounds": args.rounds,
        "pair_atlas": args.pair_atlas,
        "init_M2": [f"0x{word:08x}" for word in base_m2],
        "init_hw": init_hw,
        "init_lane_hw": init_lane,
        "init_cg_objective": round(init_cg, 6),
        "target_lane_hw": target_lane,
        "init_target_l1": init_target_l1,
        "selection": {
            **selection,
            "selected_pairs": len(selected_pairs),
            "pair_count": args.pair_count,
            "half_count": half_count,
            "max_standalone_net_delta_sum": args.max_standalone_net_delta_sum,
            "min_radius": args.min_radius,
            "max_radius": args.max_radius,
            "max_evals": args.max_evals,
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
        f"  partials={partial_count} kept={kept_partial_count} "
        f"matches={counts['candidate_matches']} evaluated={counts['evaluated']}"
    )
    if top_by_hw:
        print(f"  best HW combo: {top_by_hw[0]['hw_total']} target_l1={top_by_hw[0]['target_l1']}")
        print(f"  best target combo: l1={top_by_target[0]['target_l1']} hw={top_by_target[0]['hw_total']}")
    else:
        print("  no combos evaluated")
    print(f"Total wall: {wall:.1f}s")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
