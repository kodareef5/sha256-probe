#!/usr/bin/env python3
"""
compare_tanner_motifs.py - Cross-profile semantic motifs for Tanner pairs.

Input files are JSON profiles emitted by profile_tanner_pairs.py.  This tool
normalizes copy-specific labels such as actual_p1/actual_p2 and schedule
w1/w2, then ranks recurring semantic pair families.  The intended use is BP
design: decide which SHA-level alias motifs deserve model attention before
spending solver time on another raw Tanner gap sweep.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


STATE_RE = re.compile(r"^actual_p([12])\.([a-h])_(\d+)\.b(\d+)$")
SCHEDULE_RE = re.compile(r"^schedule\.w([12])\[(\d+)\]\.b(\d+)$")


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def normalize_label(label: str, *, keep_bit: bool) -> tuple[str, str | None, int | None]:
    state = STATE_RE.match(label)
    if state:
        _copy, word, round_s, bit_s = state.groups()
        bit = int(bit_s)
        bit_part = bit_s if keep_bit else "*"
        return f"actual_p?.{word}_{round_s}.b{bit_part}", "state", bit

    schedule = SCHEDULE_RE.match(label)
    if schedule:
        _copy, round_s, bit_s = schedule.groups()
        bit = int(bit_s)
        bit_part = bit_s if keep_bit else "*"
        return f"schedule.w?[{round_s}].b{bit_part}", "schedule", bit

    return label, None, None


def side_signature(side: dict[str, Any], *, keep_bit: bool) -> dict[str, Any]:
    labels = side.get("labels", [])
    if not isinstance(labels, list):
        labels = []

    normalized: list[str] = []
    bits: set[int] = set()
    semantic_kinds: set[str] = set()
    for label in labels:
        if not isinstance(label, str):
            continue
        norm, semantic_kind, bit = normalize_label(label, keep_bit=keep_bit)
        normalized.append(norm)
        if semantic_kind:
            semantic_kinds.add(semantic_kind)
        if bit is not None:
            bits.add(bit)

    kinds = side.get("kinds", [])
    if not isinstance(kinds, list):
        kinds = []

    return {
        "labels": sorted(set(normalized)),
        "bits": sorted(bits),
        "kinds": sorted(str(kind) for kind in kinds),
        "semantic_kinds": sorted(semantic_kinds),
        "var": side.get("var"),
        "label_count": int(side.get("label_count", len(labels)) or 0),
        "shown_label_count": len(labels),
        "truncated": int(side.get("label_count", len(labels)) or 0) > len(labels),
    }


def copy_relation(left: dict[str, Any], right: dict[str, Any]) -> str:
    left_kinds = set(left.get("kinds", []))
    right_kinds = set(right.get("kinds", []))
    left_sem = set(left.get("semantic_kinds", []))
    right_sem = set(right.get("semantic_kinds", []))

    if "actual_p1" in left_kinds and "actual_p2" in right_kinds:
        if left.get("labels") == right.get("labels"):
            return "p1_p2_same_alias"
        if left_sem & right_sem:
            return "p1_p2_related_alias"
        return "p1_p2_label_mismatch"

    if "actual_p2" in left_kinds and "actual_p1" in right_kinds:
        if left.get("labels") == right.get("labels"):
            return "p2_p1_same_alias"
        if left_sem & right_sem:
            return "p2_p1_related_alias"
        return "p2_p1_label_mismatch"

    if left_kinds == right_kinds and "schedule" in left_kinds:
        return "schedule_schedule"

    if "unmapped" in left_kinds or "unmapped" in right_kinds:
        return "partly_unmapped"

    return "other"


def record_from_pair(
    profile_path: Path,
    profile: dict[str, Any],
    source: str,
    pair: dict[str, Any],
) -> dict[str, Any]:
    left_bit = side_signature(pair.get("left", {}), keep_bit=True)
    right_bit = side_signature(pair.get("right", {}), keep_bit=True)
    left_family = side_signature(pair.get("left", {}), keep_bit=False)
    right_family = side_signature(pair.get("right", {}), keep_bit=False)

    relation = copy_relation(left_bit, right_bit)
    family_relation = copy_relation(left_family, right_family)
    family_labels = sorted(set(left_family["labels"]) | set(right_family["labels"]))

    return {
        "profile": str(profile_path),
        "cnf": profile.get("cnf"),
        "sources": [source],
        "pair": pair.get("pair"),
        "gap": pair.get("gap"),
        "multiplicity": pair.get("multiplicity"),
        "four_cycles": pair.get("four_cycles"),
        "relation": relation,
        "family_relation": family_relation,
        "left": left_bit,
        "right": right_bit,
        "family_key": " | ".join(family_labels) if family_labels else "unlabelled",
        "bit_key": " <-> ".join([
            ",".join(left_bit["labels"]) or "unlabelled",
            ",".join(right_bit["labels"]) or "unlabelled",
        ]),
        "truncated": bool(left_bit["truncated"] or right_bit["truncated"]),
    }


def iter_pair_records(profile_path: Path, profile: dict[str, Any]) -> list[dict[str, Any]]:
    records_by_pair: dict[tuple[int, int] | tuple[()], dict[str, Any]] = {}

    def add_many(source: str, rows: Any) -> None:
        if not isinstance(rows, list):
            return
        for row in rows:
            if not isinstance(row, dict):
                continue
            pair_raw = row.get("pair")
            pair_key: tuple[int, int] | tuple[()] = tuple(pair_raw) if isinstance(pair_raw, list) else ()
            if pair_key in records_by_pair:
                sources = records_by_pair[pair_key]["sources"]
                if source not in sources:
                    sources.append(source)
                continue
            records_by_pair[pair_key] = record_from_pair(profile_path, profile, source, row)

    add_many("top_pairs", profile.get("top_pairs"))
    top_by_gap = profile.get("top_by_gap", {})
    if isinstance(top_by_gap, dict):
        for gap, rows in sorted(top_by_gap.items(), key=lambda item: int(item[0])):
            add_many(f"top_by_gap:{gap}", rows)
    return list(records_by_pair.values())


def aggregate(records: list[dict[str, Any]], top: int) -> list[dict[str, Any]]:
    relation_priority = {
        "p1_p2_same_alias": 5,
        "p2_p1_same_alias": 5,
        "p1_p2_related_alias": 4,
        "p2_p1_related_alias": 4,
        "schedule_schedule": 3,
        "p1_p2_label_mismatch": 2,
        "p2_p1_label_mismatch": 2,
        "other": 1,
        "partly_unmapped": 0,
    }
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        key = (record["family_relation"], record["family_key"])
        groups[key].append(record)

    summaries: list[dict[str, Any]] = []
    for (relation, family_key), rows in groups.items():
        profile_names = sorted({str(row["profile"]) for row in rows})
        gaps = sorted({row["gap"] for row in rows if row.get("gap") is not None})
        mults = [int(row["multiplicity"]) for row in rows if row.get("multiplicity") is not None]
        cycles = [int(row["four_cycles"]) for row in rows if row.get("four_cycles") is not None]
        rows_sorted = sorted(
            rows,
            key=lambda row: (
                int(row.get("four_cycles") or 0),
                int(row.get("multiplicity") or 0),
            ),
            reverse=True,
        )
        summaries.append({
            "family_relation": relation,
            "relation_priority": relation_priority.get(relation, 1),
            "family_key": family_key,
            "profile_count": len(profile_names),
            "profiles": profile_names,
            "record_count": len(rows),
            "gaps": gaps,
            "total_four_cycles_in_records": sum(cycles),
            "max_multiplicity": max(mults) if mults else None,
            "min_multiplicity": min(mults) if mults else None,
            "truncated_records": sum(1 for row in rows if row.get("truncated")),
            "examples": rows_sorted[:top],
        })

    summaries.sort(
        key=lambda row: (
            row["relation_priority"],
            row["profile_count"],
            row["total_four_cycles_in_records"],
            row["max_multiplicity"] or 0,
        ),
        reverse=True,
    )
    return summaries


def write_markdown(path: Path, payload: dict[str, Any], *, top: int) -> None:
    lines = [
        "---",
        f"date: {_dt.date.today().isoformat()}",
        "bet: cascade_aux_encoding",
        "status: TANNER_MOTIFS_COMPARED",
        "---",
        "",
        "# Cross-profile Tanner motif comparison",
        "",
        "This report is generated by `compare_tanner_motifs.py` from profiles emitted by `profile_tanner_pairs.py`.",
        "",
        "## Inputs",
        "",
    ]
    for item in payload["inputs"]:
        lines.append(
            f"- `{item['profile']}`: vars={item['n_vars']} clauses={item['n_clauses_read']} "
            f"four_cycles={item['four_cycles']}"
        )
    lines.extend(["", "## Top motif families", ""])
    lines.append("| Rank | Relation | Profiles | Records | Gaps | Total cycles | Max mult | Family |")
    lines.append("|---:|---|---:|---:|---|---:|---:|---|")
    for idx, family in enumerate(payload["families"][:top], start=1):
        family_key = family["family_key"].replace("|", "\\|")
        if len(family_key) > 110:
            family_key = family_key[:107] + "..."
        lines.append(
            f"| {idx} | `{family['family_relation']}` | {family['profile_count']} | "
            f"{family['record_count']} | `{family['gaps']}` | "
            f"{family['total_four_cycles_in_records']} | {family['max_multiplicity']} | "
            f"`{family_key}` |"
        )

    truncated = payload["truncated_record_count"]
    lines.extend([
        "",
        "## BP follow-up",
        "",
        "- Prefer the top `p1_p2_same_alias` families over raw gap IDs when choosing correction targets.",
        "- Re-profile with a larger `--max-labels` before freezing targets if any leading family reports truncated records.",
        "- Treat mode-specific later-round families as candidates for cross-mode validation, not as universal structure yet.",
        "",
        "## Notes",
        "",
        f"- Records scanned: {payload['record_count']}",
        f"- Records with truncated label lists: {truncated}",
        "- Treat totals as rankings over the profiled top-pair surfaces, not global CNF counts.",
        "- `p1_p2_same_alias` means both sides match after normalizing p1/p2 and W1/W2.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("profiles", nargs="+", type=Path)
    ap.add_argument("--top", type=int, default=20, help="top families/examples to retain")
    ap.add_argument("--out-json", type=Path)
    ap.add_argument("--out-md", type=Path)
    args = ap.parse_args()

    all_records: list[dict[str, Any]] = []
    inputs: list[dict[str, Any]] = []
    for profile_path in args.profiles:
        profile = load_json(profile_path)
        inputs.append({
            "profile": str(profile_path),
            "cnf": profile.get("cnf"),
            "n_vars": profile.get("n_vars"),
            "n_clauses_read": profile.get("n_clauses_read"),
            "four_cycles": profile.get("four_cycles"),
        })
        all_records.extend(iter_pair_records(profile_path, profile))

    payload = {
        "inputs": inputs,
        "record_count": len(all_records),
        "truncated_record_count": sum(1 for row in all_records if row.get("truncated")),
        "families": aggregate(all_records, args.top),
    }

    compact_families = []
    for family in payload["families"][: min(8, len(payload["families"]))]:
        compact_families.append({
            "family_relation": family["family_relation"],
            "family_key": family["family_key"],
            "profile_count": family["profile_count"],
            "record_count": family["record_count"],
            "gaps": family["gaps"],
            "total_four_cycles_in_records": family["total_four_cycles_in_records"],
            "max_multiplicity": family["max_multiplicity"],
            "truncated_records": family["truncated_records"],
        })

    print(json.dumps({
        "profiles": len(inputs),
        "records": payload["record_count"],
        "truncated_records": payload["truncated_record_count"],
        "top_families": compact_families,
    }, indent=2, sort_keys=True))

    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        with args.out_json.open("w") as f:
            json.dump(payload, f, indent=2, sort_keys=True)
            f.write("\n")
    if args.out_md:
        write_markdown(args.out_md, payload, top=args.top)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
