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


def parse_optional_int_vector(raw, name):
    if not raw:
        return None
    values = []
    for part in raw.split(","):
        item = part.strip().lower()
        if item in ("", "*", "x", "none", "na"):
            values.append(None)
        else:
            values.append(int(item))
    if len(values) != 8:
        raise SystemExit(f"{name} needs 8 comma-separated values, got {len(values)}")
    return values


def bit_set(word):
    return {idx for idx in range(32) if (word >> idx) & 1}


def diff_bit_sets(diff):
    return [bit_set(word) for word in diff]


def lane_changes(init_sets, final_sets):
    removed = [init_sets[idx] - final_sets[idx] for idx in range(8)]
    added = [final_sets[idx] - init_sets[idx] for idx in range(8)]
    return removed, added


def bit_effect_summary(pair_effects, combo_ids):
    removed_union = [set() for _ in range(8)]
    added_union = [set() for _ in range(8)]
    removed_occurrences = 0
    added_occurrences = 0
    for idx in combo_ids:
        removed, added = pair_effects[idx]
        for lane_idx in range(8):
            removed_occurrences += len(removed[lane_idx])
            added_occurrences += len(added[lane_idx])
            removed_union[lane_idx].update(removed[lane_idx])
            added_union[lane_idx].update(added[lane_idx])
    removed_union_total = sum(len(items) for items in removed_union)
    added_union_total = sum(len(items) for items in added_union)
    return {
        "pair_removed_union_total": removed_union_total,
        "pair_added_union_total": added_union_total,
        "pair_removed_occurrences": removed_occurrences,
        "pair_added_occurrences": added_occurrences,
        "pair_removed_repeat_excess": removed_occurrences - removed_union_total,
        "pair_added_repeat_excess": added_occurrences - added_union_total,
    }


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
    ap.add_argument("--late-word-start", type=int, default=12)
    ap.add_argument("--late-word-end", type=int, default=15)
    ap.add_argument("--early-word-end", type=int, default=8)
    ap.add_argument(
        "--min-late-pairs",
        type=int,
        default=0,
        help="Require at least this many selected pairs to touch words in late-word-start..late-word-end.",
    )
    ap.add_argument("--min-late-late-pairs", type=int, default=0)
    ap.add_argument("--min-early-late-pairs", type=int, default=0)
    ap.add_argument(
        "--min-delta-lane-sum",
        default="",
        help="Optional 8-int lower bounds for sum of selected pairs' delta_lane_hw; use x to ignore a lane.",
    )
    ap.add_argument(
        "--max-delta-lane-sum",
        default="",
        help="Optional 8-int upper bounds for sum of selected pairs' delta_lane_hw; use x to ignore a lane.",
    )
    ap.add_argument("--min-standalone-net-delta-sum", type=int, default=None)
    ap.add_argument("--max-standalone-net-delta-sum", type=int, default=None)
    ap.add_argument("--min-pair-removed-union", type=int, default=None)
    ap.add_argument("--max-pair-added-union", type=int, default=None)
    ap.add_argument("--min-pair-added-repeat-excess", type=int, default=None)
    ap.add_argument("--min-pair-removed-repeat-excess", type=int, default=None)
    ap.add_argument("--min-m2-added", type=int, default=None)
    ap.add_argument("--max-m2-added", type=int, default=None)
    ap.add_argument("--min-m2-removed", type=int, default=None)
    ap.add_argument("--max-m2-removed", type=int, default=None)
    ap.add_argument("--min-m2-net-added", type=int, default=None)
    ap.add_argument("--max-m2-net-added", type=int, default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()
    min_delta_lane_sum = parse_optional_int_vector(args.min_delta_lane_sum, "--min-delta-lane-sum")
    max_delta_lane_sum = parse_optional_int_vector(args.max_delta_lane_sum, "--max-delta-lane-sum")

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
    use_bit_overlap_signature = any(
        value is not None
        for value in (
            args.min_pair_removed_union,
            args.max_pair_added_union,
            args.min_pair_added_repeat_excess,
            args.min_pair_removed_repeat_excess,
        )
    )
    pair_effects = None
    if use_bit_overlap_signature:
        init_sets = diff_bit_sets(init_diff)
        pair_effects = []
        for pair in selected_pairs:
            pair_m2 = flip_bits(base_m2, pair["bit_indices"])
            _, pair_diff = eval_m2(iv1, iv2, m1_w, pair_m2, args.rounds)
            pair_effects.append(lane_changes(init_sets, diff_bit_sets(pair_diff)))

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
        "skipped_late_pair_motif": 0,
        "skipped_pair_graph_motif": 0,
        "skipped_delta_signature": 0,
        "skipped_bit_overlap_signature": 0,
        "skipped_m2_shape_signature": 0,
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
        if args.min_late_pairs:
            late_pairs = 0
            for idx in combo_ids:
                if any(
                    args.late_word_start <= bit_index // 32 <= args.late_word_end
                    for bit_index in selected_pairs[idx]["bit_indices"]
                ):
                    late_pairs += 1
            if late_pairs < args.min_late_pairs:
                counts["skipped_late_pair_motif"] += 1
                continue
        if args.min_late_late_pairs or args.min_early_late_pairs:
            late_late_pairs = 0
            early_late_pairs = 0
            for idx in combo_ids:
                words = [bit_index // 32 for bit_index in selected_pairs[idx]["bit_indices"]]
                touches_late = any(args.late_word_start <= word <= args.late_word_end for word in words)
                touches_early = any(word <= args.early_word_end for word in words)
                if all(args.late_word_start <= word <= args.late_word_end for word in words):
                    late_late_pairs += 1
                if touches_late and touches_early:
                    early_late_pairs += 1
            if late_late_pairs < args.min_late_late_pairs or early_late_pairs < args.min_early_late_pairs:
                counts["skipped_pair_graph_motif"] += 1
                continue
        delta_lane_sum = [0] * 8
        standalone_net_delta_sum = 0
        for idx in combo_ids:
            pair = selected_pairs[idx]
            standalone_net_delta_sum += pair["hw_total"] - init_hw
            for lane_idx, value in enumerate(pair["delta_lane_hw"]):
                delta_lane_sum[lane_idx] += value
        if (
            min_delta_lane_sum
            or max_delta_lane_sum
            or args.min_standalone_net_delta_sum is not None
            or args.max_standalone_net_delta_sum is not None
        ):
            failed_delta_signature = False
            if (
                args.min_standalone_net_delta_sum is not None
                and standalone_net_delta_sum < args.min_standalone_net_delta_sum
            ):
                failed_delta_signature = True
            if (
                args.max_standalone_net_delta_sum is not None
                and standalone_net_delta_sum > args.max_standalone_net_delta_sum
            ):
                failed_delta_signature = True
            if min_delta_lane_sum:
                for lane_idx, minimum in enumerate(min_delta_lane_sum):
                    if minimum is not None and delta_lane_sum[lane_idx] < minimum:
                        failed_delta_signature = True
                        break
            if max_delta_lane_sum:
                for lane_idx, maximum in enumerate(max_delta_lane_sum):
                    if maximum is not None and delta_lane_sum[lane_idx] > maximum:
                        failed_delta_signature = True
                        break
            if failed_delta_signature:
                counts["skipped_delta_signature"] += 1
                continue
        bit_overlap_summary = None
        if use_bit_overlap_signature:
            bit_overlap_summary = bit_effect_summary(pair_effects, combo_ids)
            failed_bit_overlap_signature = False
            if (
                args.min_pair_removed_union is not None
                and bit_overlap_summary["pair_removed_union_total"] < args.min_pair_removed_union
            ):
                failed_bit_overlap_signature = True
            if (
                args.max_pair_added_union is not None
                and bit_overlap_summary["pair_added_union_total"] > args.max_pair_added_union
            ):
                failed_bit_overlap_signature = True
            if (
                args.min_pair_added_repeat_excess is not None
                and bit_overlap_summary["pair_added_repeat_excess"] < args.min_pair_added_repeat_excess
            ):
                failed_bit_overlap_signature = True
            if (
                args.min_pair_removed_repeat_excess is not None
                and bit_overlap_summary["pair_removed_repeat_excess"] < args.min_pair_removed_repeat_excess
            ):
                failed_bit_overlap_signature = True
            if failed_bit_overlap_signature:
                counts["skipped_bit_overlap_signature"] += 1
                continue
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
        m2_added, m2_removed, m2_net_added = m2_transition_counts(base_m2, m2)
        failed_m2_shape = False
        if args.min_m2_added is not None and m2_added < args.min_m2_added:
            failed_m2_shape = True
        if args.max_m2_added is not None and m2_added > args.max_m2_added:
            failed_m2_shape = True
        if args.min_m2_removed is not None and m2_removed < args.min_m2_removed:
            failed_m2_shape = True
        if args.max_m2_removed is not None and m2_removed > args.max_m2_removed:
            failed_m2_shape = True
        if args.min_m2_net_added is not None and m2_net_added < args.min_m2_net_added:
            failed_m2_shape = True
        if args.max_m2_net_added is not None and m2_net_added > args.max_m2_net_added:
            failed_m2_shape = True
        if failed_m2_shape:
            counts["skipped_m2_shape_signature"] += 1
            continue
        hw, diff = eval_m2(iv1, iv2, m1_w, m2, args.rounds)
        lane = hw_per_lane(diff)
        cg_obj = objective_value(hw, lane, "cg", [1.0] * 8, args.cg_weight)
        target_l1 = l1_distance(lane, target_lane)
        entry = {
            "pair_ids": list(combo_ids),
            "bits": list(bits),
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
            "standalone_net_delta_sum": standalone_net_delta_sum,
            "delta_lane_sum": delta_lane_sum,
            "bit_overlap_signature": bit_overlap_summary,
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
            "late_word_start": args.late_word_start,
            "late_word_end": args.late_word_end,
            "early_word_end": args.early_word_end,
            "min_late_pairs": args.min_late_pairs,
            "min_late_late_pairs": args.min_late_late_pairs,
            "min_early_late_pairs": args.min_early_late_pairs,
            "min_delta_lane_sum": min_delta_lane_sum,
            "max_delta_lane_sum": max_delta_lane_sum,
            "min_standalone_net_delta_sum": args.min_standalone_net_delta_sum,
            "max_standalone_net_delta_sum": args.max_standalone_net_delta_sum,
            "min_pair_removed_union": args.min_pair_removed_union,
            "max_pair_added_union": args.max_pair_added_union,
            "min_pair_added_repeat_excess": args.min_pair_added_repeat_excess,
            "min_pair_removed_repeat_excess": args.min_pair_removed_repeat_excess,
            "min_m2_added": args.min_m2_added,
            "max_m2_added": args.max_m2_added,
            "min_m2_removed": args.min_m2_removed,
            "max_m2_removed": args.max_m2_removed,
            "min_m2_net_added": args.min_m2_net_added,
            "max_m2_net_added": args.max_m2_net_added,
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
    if top_by_hw:
        print(f"  best HW combo: {top_by_hw[0]['hw_total']} target_l1={top_by_hw[0]['target_l1']}")
        print(f"  best target combo: l1={top_by_target[0]['target_l1']} hw={top_by_target[0]['hw_total']}")
    else:
        print("  no combos passed filters")
    print(f"Total wall: {wall:.1f}s")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
