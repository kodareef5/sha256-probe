#!/usr/bin/env python3
"""Measure nonlinear cancellation in M2 combo records.

Each pair-potential entry records its standalone lane delta from the same base
M2 witness. If those deltas composed linearly, a combo lane would be
init_lane + sum(pair_delta_lane_hw). The gap between that prediction and the
actual final lane is a compact way to measure nonlinear repair cancellation.
"""

import argparse
from collections import Counter
import json
from pathlib import Path


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


def word_pair(bit_indices):
    return tuple(sorted(bit_index // 32 for bit_index in bit_indices))


def vector_add(vectors):
    out = [0] * 8
    for vec in vectors:
        for idx, value in enumerate(vec):
            out[idx] += value
    return out


def annotate_record(record, selected_pairs, init_hw, init_lane):
    pairs = [selected_pairs[pair_id] for pair_id in record["pair_ids"]]
    delta_vectors = [pair["delta_lane_hw"] for pair in pairs]
    delta_sum = vector_add(delta_vectors)
    linear_lane = [init_lane[idx] + delta_sum[idx] for idx in range(8)]
    actual_delta = [record["lane_hw"][idx] - init_lane[idx] for idx in range(8)]
    nonlinear_lane_gain = [
        linear_lane[idx] - record["lane_hw"][idx]
        for idx in range(8)
    ]
    standalone_net_delta_sum = sum(pair["hw_total"] - init_hw for pair in pairs)
    nonlinear_hw_gain = standalone_net_delta_sum - record["net_delta"]
    source_counter = Counter()
    for pair in pairs:
        source_counter.update(pair["selection_sources"])

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
        "word_pairs": [list(word_pair(pair["bit_indices"])) for pair in pairs],
        "source_counts": dict(sorted(source_counter.items())),
        "standalone_hw": [pair["hw_total"] for pair in pairs],
        "standalone_net_delta_sum": standalone_net_delta_sum,
        "delta_lane_sum": delta_sum,
        "linear_lane_hw": linear_lane,
        "linear_hw_total": sum(linear_lane),
        "actual_delta_lane_hw": actual_delta,
        "nonlinear_lane_gain": nonlinear_lane_gain,
        "nonlinear_hw_gain": nonlinear_hw_gain,
    }


def summarize_combo(path, records_per_group):
    combo = json.loads(path.read_text())
    atlas = json.loads(Path(combo["pair_atlas"]).read_text())
    selected_pairs = reconstruct_selected_pairs(atlas, combo["selection"])
    groups = {}
    for name in ("top_records_hw_le_init", "top_by_hw", "top_by_target_l1", "top_by_cg"):
        records = combo.get(name, [])[:records_per_group]
        groups[name] = [
            annotate_record(record, selected_pairs, combo["init_hw"], combo["init_lane_hw"])
            for record in records
        ]
    return {
        "combo_json": str(path),
        "label": combo.get("label"),
        "init_hw": combo["init_hw"],
        "init_lane_hw": combo["init_lane_hw"],
        "selection": combo["selection"],
        "counts": combo["counts"],
        "groups": groups,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("combo_json", nargs="+")
    ap.add_argument("--records-per-group", type=int, default=3)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    payload = {
        "description": "M2 combo nonlinear cancellation summary",
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
