#!/usr/bin/env python3
"""Compare M2 combo-search branch artifacts at a selector/record level."""

import argparse
from collections import Counter
import json
from pathlib import Path


GROUPS = ("top_by_hw", "top_by_target_l1", "top_by_cg")


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


def rate_per_million(count, evaluated):
    if not evaluated:
        return 0.0
    return count * 1_000_000.0 / evaluated


def source_bucket(source_counts):
    target = source_counts.get("target", 0)
    repair = sum(count for source, count in source_counts.items() if source.startswith("repair"))
    hw = source_counts.get("hw", 0)
    cg = source_counts.get("cg", 0)
    return {"target": target, "repair": repair, "hw": hw, "cg": cg}


def annotate_record(record, selected_pairs, selection):
    if record is None:
        return None
    source_counter = Counter()
    word_pairs = []
    standalone_hw = []
    for pair_id in record["pair_ids"]:
        pair = selected_pairs[pair_id]
        source_counter.update(pair["selection_sources"])
        word_pairs.append(word_pair(pair["bit_indices"]))
        standalone_hw.append(pair["hw_total"])
    return {
        "hw_total": record["hw_total"],
        "target_l1": record["target_l1"],
        "cg_objective": record["cg_objective"],
        "net_delta": record["net_delta"],
        "lane_hw": record["lane_hw"],
        "bits": record["bits"],
        "pair_ids": record["pair_ids"],
        "word_pairs": [list(pair) for pair in word_pairs],
        "motifs": motif_counts(
            word_pairs,
            selection.get("late_word_start", 12),
            selection.get("late_word_end", 15),
            selection.get("early_word_end", 8),
        ),
        "source_counts": dict(sorted(source_counter.items())),
        "source_bucket": source_bucket(source_counter),
        "standalone_net_delta_sum": record.get("standalone_net_delta_sum"),
        "delta_lane_sum": record.get("delta_lane_sum"),
        "bit_overlap_signature": record.get("bit_overlap_signature"),
        "standalone_hw": standalone_hw,
    }


def summarize_combo(path):
    combo = json.loads(path.read_text())
    atlas = json.loads(Path(combo["pair_atlas"]).read_text())
    selected_pairs = reconstruct_selected_pairs(atlas, combo["selection"])
    counts = combo["counts"]
    evaluated = counts["evaluated"]

    best = {}
    for group in GROUPS:
        records = combo.get(group, [])
        best[group] = annotate_record(records[0] if records else None, selected_pairs, combo["selection"])

    best_hw = best["top_by_hw"]
    best_target = best["top_by_target_l1"]
    best_cg = best["top_by_cg"]

    return {
        "path": str(path),
        "label": combo.get("label"),
        "init_hw": combo["init_hw"],
        "init_lane_hw": combo["init_lane_hw"],
        "init_target_l1": combo.get("init_target_l1"),
        "init_cg_objective": combo.get("init_cg_objective"),
        "selection": combo["selection"],
        "selected_pairs_reconstructed": len(selected_pairs),
        "counts": counts,
        "rates_per_million": {
            "hw_lt_init": rate_per_million(counts["hw_lt_init"], evaluated),
            "hw_le_init": rate_per_million(counts["hw_le_init"], evaluated),
            "target_l1_lt_init": rate_per_million(counts["target_l1_lt_init"], evaluated),
            "cg_lt_init": rate_per_million(counts["cg_lt_init"], evaluated),
        },
        "best": best,
        "derived": {
            "best_hw_delta": None if best_hw is None else best_hw["hw_total"] - combo["init_hw"],
            "best_hw_target_l1": None if best_hw is None else best_hw["target_l1"],
            "best_target_l1": None if best_target is None else best_target["target_l1"],
            "best_target_hw_delta": None
            if best_target is None
            else best_target["hw_total"] - combo["init_hw"],
            "best_cg_delta": None
            if best_cg is None or combo.get("init_cg_objective") is None
            else best_cg["cg_objective"] - combo["init_cg_objective"],
        },
    }


def md_table(rows):
    headers = [
        "label",
        "evals",
        "HW<=init",
        "target<init",
        "target/M",
        "best HW",
        "best HW target",
        "best target",
        "best target HW",
        "selected",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        counts = row["counts"]
        rates = row["rates_per_million"]
        best_hw = row["best"]["top_by_hw"]
        best_target = row["best"]["top_by_target_l1"]
        values = [
            row["label"],
            f"{counts['evaluated']:,}",
            str(counts["hw_le_init"]),
            str(counts["target_l1_lt_init"]),
            f"{rates['target_l1_lt_init']:.2f}",
            "n/a" if best_hw is None else str(best_hw["hw_total"]),
            "n/a" if best_hw is None else str(best_hw["target_l1"]),
            "n/a" if best_target is None else str(best_target["target_l1"]),
            "n/a" if best_target is None else str(best_target["hw_total"]),
            str(row["selected_pairs_reconstructed"]),
        ]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("combo_json", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown-out")
    args = ap.parse_args()

    rows = [summarize_combo(Path(combo_json)) for combo_json in args.combo_json]
    payload = {
        "description": "M2 combo branch comparison",
        "combo_count": len(rows),
        "combos": rows,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")

    if args.markdown_out:
        md_out = Path(args.markdown_out)
        md_out.parent.mkdir(parents=True, exist_ok=True)
        md_out.write_text(md_table(rows))
        print(f"wrote {out} and {md_out}")
    else:
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
