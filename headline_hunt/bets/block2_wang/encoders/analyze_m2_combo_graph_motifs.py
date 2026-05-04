#!/usr/bin/env python3
"""Summarize word-pair graph motifs in M2 combo records."""

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


def motif_counts(word_pairs, late_start, late_end, early_end):
    late_touch = 0
    late_late = 0
    early_late = 0
    word_degree = Counter()
    for words in word_pairs:
        touches_late = any(late_start <= word <= late_end for word in words)
        touches_early = any(word <= early_end for word in words)
        if touches_late:
            late_touch += 1
        if all(late_start <= word <= late_end for word in words):
            late_late += 1
        if touches_late and touches_early:
            early_late += 1
        word_degree.update(words)
    return {
        "late_touch_pairs": late_touch,
        "late_late_pairs": late_late,
        "early_late_pairs": early_late,
        "word_degree": dict(sorted(word_degree.items())),
    }


def annotate_record(record, selected_pairs, late_start, late_end, early_end):
    pair_entries = []
    word_pairs = []
    source_counter = Counter()
    for pair_id in record["pair_ids"]:
        pair = selected_pairs[pair_id]
        words = word_pair(pair["bit_indices"])
        word_pairs.append(words)
        source_counter.update(pair["selection_sources"])
        pair_entries.append(
            {
                "pair_id": pair_id,
                "bit_indices": pair["bit_indices"],
                "word_pair": list(words),
                "selection_sources": pair["selection_sources"],
                "standalone_hw": pair["hw_total"],
                "standalone_target_l1": pair.get("target_l1"),
                "standalone_cg": pair.get("cg_objective"),
                "delta_lane_hw": pair.get("delta_lane_hw"),
            }
        )
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
        "word_pairs": [list(words) for words in word_pairs],
        "motifs": motif_counts(word_pairs, late_start, late_end, early_end),
        "source_counts": dict(sorted(source_counter.items())),
        "pairs": pair_entries,
    }


def summarize_combo(path, records_per_group):
    combo = json.loads(path.read_text())
    atlas = json.loads(Path(combo["pair_atlas"]).read_text())
    selection = combo["selection"]
    selected_pairs = reconstruct_selected_pairs(atlas, selection)
    late_start = selection.get("late_word_start", 12)
    late_end = selection.get("late_word_end", 15)
    early_end = selection.get("early_word_end", 8)

    groups = {}
    for name in ("top_records_hw_le_init", "top_by_hw", "top_by_target_l1", "top_by_cg"):
        records = combo.get(name, [])[:records_per_group]
        groups[name] = [
            annotate_record(record, selected_pairs, late_start, late_end, early_end)
            for record in records
        ]

    return {
        "combo_json": str(path),
        "label": combo.get("label"),
        "pair_atlas": combo["pair_atlas"],
        "init_hw": combo["init_hw"],
        "init_lane_hw": combo["init_lane_hw"],
        "init_target_l1": combo["init_target_l1"],
        "selection": selection,
        "counts": combo["counts"],
        "selected_pairs_reconstructed": len(selected_pairs),
        "groups": groups,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("combo_json", nargs="+")
    ap.add_argument("--records-per-group", type=int, default=3)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    payload = {
        "description": "M2 combo word-pair graph motif summary",
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
