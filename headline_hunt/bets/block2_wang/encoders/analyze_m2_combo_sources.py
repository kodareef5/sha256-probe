#!/usr/bin/env python3
"""Explain which selected pair-potential moves compose M2 combo records."""

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


def compact_pair(entry):
    return {
        "bit_indices": entry["bit_indices"],
        "selection_sources": entry["selection_sources"],
        "standalone_hw": entry["hw_total"],
        "standalone_cg": entry["cg_objective"],
        "standalone_target_l1": entry.get("target_l1"),
        "total_repair": entry.get("total_repair"),
        "total_damage": entry.get("total_damage"),
        "delta_lane_hw": entry.get("delta_lane_hw"),
    }


def annotate_record(record, selected_pairs):
    details = []
    source_counter = Counter()
    for pair_id in record["pair_ids"]:
        pair = selected_pairs[pair_id]
        details.append({"pair_id": pair_id, **compact_pair(pair)})
        source_counter.update(pair["selection_sources"])
    return {
        "record": {
            "hw_total": record["hw_total"],
            "net_delta": record["net_delta"],
            "lane_hw": record["lane_hw"],
            "cg_objective": record["cg_objective"],
            "target_l1": record["target_l1"],
            "bits": record["bits"],
            "pair_ids": record["pair_ids"],
            "pair_sources": record["pair_sources"],
        },
        "source_counts": dict(sorted(source_counter.items())),
        "pair_details": details,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--combo-json", required=True)
    ap.add_argument("--records-per-group", type=int, default=3)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    combo_path = Path(args.combo_json)
    combo = json.loads(combo_path.read_text())
    atlas_path = Path(combo["pair_atlas"])
    atlas = json.loads(atlas_path.read_text())
    selected_pairs = reconstruct_selected_pairs(atlas, combo["selection"])

    groups = {}
    for name in ("top_records_hw_le_init", "top_by_hw", "top_by_target_l1", "top_by_cg"):
        records = combo.get(name, [])[: args.records_per_group]
        groups[name] = [annotate_record(record, selected_pairs) for record in records]

    selection_source_counts = Counter()
    for pair in selected_pairs:
        selection_source_counts.update(pair["selection_sources"])

    payload = {
        "description": "M2 combo source analysis",
        "combo_json": str(combo_path),
        "pair_atlas": str(atlas_path),
        "label": combo.get("label"),
        "selection": combo["selection"],
        "selected_pairs_reconstructed": len(selected_pairs),
        "selection_source_counts": dict(sorted(selection_source_counts.items())),
        "groups": groups,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"selected_pairs={len(selected_pairs)} wrote {out}")


if __name__ == "__main__":
    main()
