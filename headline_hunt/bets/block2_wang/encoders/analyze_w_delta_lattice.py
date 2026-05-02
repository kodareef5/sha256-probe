#!/usr/bin/env python3
"""Compare W57..W60 delta masks across pair-beam artifacts.

The pair-beam tools can find good points from different seeds, but the
headline question after F521/F542 is whether the actual W-bit moves share
structure across candidates or are only local basin accidents. This utility
extracts init->target XOR masks for best/new/top records, deduplicates them,
and reports recurring bit positions and word-level delta masks.
"""

import argparse
from collections import Counter, defaultdict
from itertools import combinations
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def parse_words(words: list[str]) -> list[int]:
    return [int(word, 16) & 0xFFFFFFFF for word in words]


def bit_label(local_idx: int) -> str:
    return f"W{57 + local_idx // 32}:b{local_idx % 32}"


def delta_bits(init_words: list[int], target_words: list[int]) -> list[int]:
    out = []
    for slot, (old, new) in enumerate(zip(init_words, target_words)):
        mask = old ^ new
        for bit in range(32):
            if mask & (1 << bit):
                out.append(slot * 32 + bit)
    return out


def section_entries(payload: dict[str, Any], sections: set[str], top_per_section: int) -> list[tuple[str, dict[str, Any]]]:
    entries: list[tuple[str, dict[str, Any]]] = []
    if "best_seen" in sections and payload.get("best_seen"):
        entries.append(("best_seen", payload["best_seen"]))
    for section in ("new_records", "top_records"):
        if section not in sections:
            continue
        for idx, entry in enumerate(payload.get(section, [])[:top_per_section], start=1):
            entries.append((f"{section}:{idx}", entry))
    return entries


def record_from_entry(path: Path, payload: dict[str, Any], section: str, entry: dict[str, Any]) -> dict[str, Any] | None:
    init_w = payload.get("init_W")
    target_w = entry.get("W")
    if not init_w or not target_w:
        return None
    init_words = parse_words(init_w)
    target_words = parse_words(target_w)
    bits = delta_bits(init_words, target_words)
    delta_words = [old ^ new for old, new in zip(init_words, target_words)]
    record = entry.get("record") or {}
    return {
        "source_artifact": str(path),
        "artifact": path.name,
        "source_description": payload.get("description"),
        "section": section,
        "candidate": payload.get("candidate"),
        "init_hw": payload.get("init_hw"),
        "target_hw": entry.get("hw_total", record.get("hw_total")),
        "score": entry.get("score"),
        "init_W": init_w,
        "target_W": target_w,
        "delta_words": [f"0x{word:08x}" for word in delta_words],
        "changed_words": [57 + idx for idx, word in enumerate(delta_words) if word],
        "delta_bit_count": len(bits),
        "delta_bits": [{"bit_index": idx, "label": bit_label(idx)} for idx in bits],
        "hw63": record.get("hw63"),
    }


def dedupe_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[tuple[Any, ...], dict[str, Any]] = {}
    for rec in records:
        key = (
            rec["candidate"],
            tuple(rec["init_W"]),
            tuple(rec["target_W"]),
            rec["target_hw"],
            rec["section"],
        )
        old = deduped.get(key)
        if old is None or (rec["target_hw"], -(rec["score"] or -10**9)) < (
            old["target_hw"],
            -(old["score"] or -10**9),
        ):
            deduped[key] = rec
    return sorted(
        deduped.values(),
        key=lambda r: (r["target_hw"] if r["target_hw"] is not None else 10**9, -(r["score"] or -10**9), r["candidate"] or "", r["artifact"]),
    )


def make_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    bit_counts: Counter[str] = Counter()
    bit_candidates: dict[str, set[str]] = defaultdict(set)
    word_delta_counts: Counter[tuple[int, str]] = Counter()
    pair_counts: Counter[tuple[str, str]] = Counter()

    for rec in records:
        cand = rec.get("candidate") or "unknown"
        labels = [bit["label"] for bit in rec["delta_bits"]]
        bit_counts.update(labels)
        for label in labels:
            bit_candidates[label].add(cand)
        for word, mask in zip((57, 58, 59, 60), rec["delta_words"]):
            if mask != "0x00000000":
                word_delta_counts[(word, mask)] += 1
        for a, b in combinations(labels, 2):
            pair_counts[tuple(sorted((a, b)))] += 1

    return {
        "record_count": len(records),
        "top_bits": [
            {
                "label": label,
                "count": count,
                "candidate_count": len(bit_candidates[label]),
                "candidates": sorted(bit_candidates[label]),
            }
            for label, count in bit_counts.most_common()
        ],
        "shared_bits": [
            {
                "label": label,
                "count": bit_counts[label],
                "candidate_count": len(cands),
                "candidates": sorted(cands),
            }
            for label, cands in sorted(bit_candidates.items())
            if len(cands) >= 2
        ],
        "top_word_deltas": [
            {"word": word, "mask": mask, "count": count}
            for (word, mask), count in word_delta_counts.most_common()
        ],
        "top_bit_pairs": [
            {"bits": list(bits), "count": count}
            for bits, count in pair_counts.most_common()
        ],
    }


def markdown(payload: dict[str, Any], top_n: int) -> str:
    lines = [
        "# W Delta Lattice",
        "",
        f"Artifacts: {len(payload['source_artifacts'])}",
        f"Records: {payload['summary']['record_count']}",
        "",
        "## Record Deltas",
        "",
        "| Artifact | Section | Candidate | HW | Bits | Changed words | Delta masks |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for rec in payload["records"][:top_n]:
        hw = f"{rec['init_hw']}->{rec['target_hw']}"
        changed = ",".join(str(w) for w in rec["changed_words"]) or "-"
        masks = " ".join(rec["delta_words"])
        lines.append(
            f"| `{rec['artifact']}` | {rec['section']} | `{rec['candidate']}` | {hw} | "
            f"{rec['delta_bit_count']} | {changed} | `{masks}` |"
        )

    lines.extend([
        "",
        "## Shared Bit Positions",
        "",
        "| Bit | Count | Candidates |",
        "|---|---:|---|",
    ])
    for item in payload["summary"]["shared_bits"][:top_n]:
        lines.append(f"| `{item['label']}` | {item['count']} | {', '.join(item['candidates'])} |")

    lines.extend([
        "",
        "## Top Bit Positions",
        "",
        "| Bit | Count | Candidate count | Candidates |",
        "|---|---:|---:|---|",
    ])
    for item in payload["summary"]["top_bits"][:top_n]:
        lines.append(
            f"| `{item['label']}` | {item['count']} | {item['candidate_count']} | "
            f"{', '.join(item['candidates'])} |"
        )

    lines.extend([
        "",
        "## Top Word Delta Masks",
        "",
        "| Word | Mask | Count |",
        "|---:|---|---:|",
    ])
    for item in payload["summary"]["top_word_deltas"][:top_n]:
        lines.append(f"| W{item['word']} | `{item['mask']}` | {item['count']} |")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--artifacts", nargs="+", required=True)
    ap.add_argument("--sections", default="best_seen")
    ap.add_argument("--top-per-section", type=int, default=20)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--top-n", type=int, default=40)
    args = ap.parse_args()

    sections = {part.strip() for part in args.sections.split(",") if part.strip()}
    records = []
    for raw in args.artifacts:
        path = Path(raw)
        payload = load_json(path)
        for section, entry in section_entries(payload, sections, args.top_per_section):
            rec = record_from_entry(path, payload, section, entry)
            if rec is not None:
                records.append(rec)

    records = dedupe_records(records)
    payload = {
        "description": "W57..W60 delta lattice across pair-beam artifacts",
        "source_artifacts": args.artifacts,
        "sections": sorted(sections),
        "top_per_section": args.top_per_section,
        "records": records,
        "summary": make_summary(records),
    }

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(markdown(payload, args.top_n), encoding="utf-8")

    print(f"wrote {out_json}: {len(records)} records")
    print(f"wrote {out_md}")


if __name__ == "__main__":
    main()
