#!/usr/bin/env python3
"""Inspect bit-level repair/addition overlap in M2 combo records."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[4]
ENCODERS = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(ENCODERS))

from block2_m2_pair_beam import (  # noqa: E402
    IV,
    MASK,
    eval_m2,
    expand_schedule,
    load_seed,
    parse_m2_override,
    parse_w_arr,
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


def bit_set(word):
    return {idx for idx in range(32) if (word >> idx) & 1}


def diff_bit_sets(diff):
    return [bit_set(word) for word in diff]


def sorted_sets(sets):
    return [sorted(items) for items in sets]


def set_counts(sets):
    return [len(items) for items in sets]


def set_union(set_groups):
    out = [set() for _ in range(8)]
    for group in set_groups:
        for idx, items in enumerate(group):
            out[idx].update(items)
    return out


def subtract_by_lane(left, right):
    return [left[idx] - right[idx] for idx in range(8)]


def intersect_by_lane(left, right):
    return [left[idx] & right[idx] for idx in range(8)]


def overlap_summary(combo_sets, union_sets):
    covered = intersect_by_lane(combo_sets, union_sets)
    noise = subtract_by_lane(union_sets, combo_sets)
    return {
        "combo_counts": set_counts(combo_sets),
        "union_counts": set_counts(union_sets),
        "covered_counts": set_counts(covered),
        "noise_counts": set_counts(noise),
        "covered_total": sum(len(items) for items in covered),
        "combo_total": sum(len(items) for items in combo_sets),
        "union_total": sum(len(items) for items in union_sets),
        "noise_total": sum(len(items) for items in noise),
        "covered_bits": sorted_sets(covered),
        "noise_bits": sorted_sets(noise),
    }


def lane_changes(init_sets, final_sets):
    removed = subtract_by_lane(init_sets, final_sets)
    added = subtract_by_lane(final_sets, init_sets)
    return removed, added


def eval_diff(iv1, iv2, m1_w, m2, rounds):
    hw, diff = eval_m2(iv1, iv2, m1_w, m2, rounds)
    return hw, diff_bit_sets(diff), [f"0x{x:08x}" for x in diff]


def annotate_record(record, selected_pairs, combo_ctx):
    init_sets = combo_ctx["init_sets"]
    final_m2 = parse_w_arr(record["M2"])
    final_hw, final_sets, final_diff_hex = eval_diff(
        combo_ctx["iv1"], combo_ctx["iv2"], combo_ctx["m1_w"], final_m2, combo_ctx["rounds"]
    )
    if final_hw != record["hw_total"]:
        raise SystemExit(f"record HW mismatch: record {record['hw_total']} evaluated {final_hw}")
    combo_removed, combo_added = lane_changes(init_sets, final_sets)

    pair_removed_groups = []
    pair_added_groups = []
    pair_details = []
    source_counter = Counter()
    for pair_id in record["pair_ids"]:
        pair = selected_pairs[pair_id]
        source_counter.update(pair["selection_sources"])
        pair_m2 = flip_bits(combo_ctx["base_m2"], pair["bit_indices"])
        pair_hw, pair_sets, pair_diff_hex = eval_diff(
            combo_ctx["iv1"], combo_ctx["iv2"], combo_ctx["m1_w"], pair_m2, combo_ctx["rounds"]
        )
        pair_removed, pair_added = lane_changes(init_sets, pair_sets)
        pair_removed_groups.append(pair_removed)
        pair_added_groups.append(pair_added)
        pair_details.append(
            {
                "pair_id": pair_id,
                "bit_indices": pair["bit_indices"],
                "word_pair": sorted(bit_index // 32 for bit_index in pair["bit_indices"]),
                "selection_sources": pair["selection_sources"],
                "standalone_hw": pair_hw,
                "standalone_diff_hex": pair_diff_hex,
                "removed_counts": set_counts(pair_removed),
                "added_counts": set_counts(pair_added),
                "removed_bits": sorted_sets(pair_removed),
                "added_bits": sorted_sets(pair_added),
            }
        )

    union_pair_removed = set_union(pair_removed_groups)
    union_pair_added = set_union(pair_added_groups)
    return {
        "record": {
            "hw_total": record["hw_total"],
            "net_delta": record["net_delta"],
            "lane_hw": record["lane_hw"],
            "target_l1": record["target_l1"],
            "cg_objective": record["cg_objective"],
            "bits": record["bits"],
            "pair_ids": record["pair_ids"],
        },
        "source_counts": dict(sorted(source_counter.items())),
        "final_diff_hex": final_diff_hex,
        "combo_removed_counts": set_counts(combo_removed),
        "combo_added_counts": set_counts(combo_added),
        "combo_removed_bits": sorted_sets(combo_removed),
        "combo_added_bits": sorted_sets(combo_added),
        "pair_removed_overlap": overlap_summary(combo_removed, union_pair_removed),
        "pair_added_overlap": overlap_summary(combo_added, union_pair_added),
        "pair_details": pair_details,
    }


def summarize_combo(path, records_per_group):
    combo = json.loads(path.read_text())
    atlas = json.loads(Path(combo["pair_atlas"]).read_text())
    selected_pairs = reconstruct_selected_pairs(atlas, combo["selection"])
    seed, _ = load_seed(combo["seed_jsonl"], combo["seed_rank"])
    diff63 = parse_w_arr(seed["block1_diff63"])
    iv1 = list(IV)
    iv2 = [(iv1[idx] ^ diff63[idx]) & MASK for idx in range(8)]
    m1_w = expand_schedule([0] * 16)
    base_m2 = parse_m2_override(",".join(combo["init_M2"]))
    init_hw, init_sets, init_diff_hex = eval_diff(iv1, iv2, m1_w, base_m2, combo["rounds"])
    if init_hw != combo["init_hw"]:
        raise SystemExit(f"init HW mismatch for {path}: combo {combo['init_hw']} evaluated {init_hw}")
    combo_ctx = {
        "iv1": iv1,
        "iv2": iv2,
        "m1_w": m1_w,
        "base_m2": base_m2,
        "init_sets": init_sets,
        "rounds": combo["rounds"],
    }

    groups = {}
    for name in ("top_records_hw_le_init", "top_by_hw", "top_by_target_l1", "top_by_cg"):
        records = combo.get(name, [])[:records_per_group]
        groups[name] = [annotate_record(record, selected_pairs, combo_ctx) for record in records]

    return {
        "combo_json": str(path),
        "label": combo.get("label"),
        "init_hw": combo["init_hw"],
        "init_lane_hw": combo["init_lane_hw"],
        "init_diff_hex": init_diff_hex,
        "selection": combo["selection"],
        "counts": combo["counts"],
        "groups": groups,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("combo_json", nargs="+")
    ap.add_argument("--records-per-group", type=int, default=2)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    payload = {
        "description": "M2 combo bit-level repair/addition overlap summary",
        "records_per_group": args.records_per_group,
        "combos": [
            summarize_combo(Path(combo_json), args.records_per_group)
            for combo_json in args.combo_json
        ],
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
