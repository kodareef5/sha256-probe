#!/usr/bin/env python3
"""Compare selected M2 witnesses by lane shape and distances to target lanes."""

import argparse
import json
from pathlib import Path


def parse_lane(raw):
    parts = [int(part.strip()) for part in raw.split(",") if part.strip()]
    if len(parts) != 8:
        raise SystemExit(f"lane needs 8 comma-separated ints: {raw}")
    return parts


def lane_l1(a, b):
    return sum(abs(x - y) for x, y in zip(a, b))


def lane_linf(a, b):
    return max(abs(x - y) for x, y in zip(a, b))


def cg_sum(lane):
    return lane[2] + lane[6]


def m2_words(raw_words):
    if raw_words is None:
        return None
    return [int(word, 16) if isinstance(word, str) else int(word) for word in raw_words]


def popcount_words(words):
    if words is None:
        return None
    return sum(word.bit_count() for word in words)


def m2_distance(a, b):
    if a is None or b is None:
        return None
    return sum((x ^ y).bit_count() for x, y in zip(a, b))


def extract_combo(path, group, index, label):
    data = json.loads(path.read_text())
    records = data[group]
    record = records[index]
    words = m2_words(record.get("M2"))
    return {
        "label": label,
        "source_path": str(path),
        "source_kind": f"combo:{group}[{index}]",
        "hw": record["hw_total"],
        "lane_hw": record["lane_hw"],
        "cg_sum": cg_sum(record["lane_hw"]),
        "m2_weight": popcount_words(words),
        "target_l1": record.get("target_l1"),
        "M2": record.get("M2"),
        "bits": record.get("bits"),
    }


def extract_beam(path, field, label):
    data = json.loads(path.read_text())
    if field == "best_seen":
        words = m2_words(data["best_seen_M2"])
        return {
            "label": label,
            "source_path": str(path),
            "source_kind": "beam:best_seen",
            "hw": data["best_seen_hw"],
            "lane_hw": data["best_seen_lane_hw"],
            "cg_sum": cg_sum(data["best_seen_lane_hw"]),
            "m2_weight": popcount_words(words),
            "target_l1": None,
            "M2": data["best_seen_M2"],
            "bits": data.get("best_objective_bits")
            if data.get("best_objective_hw") == data.get("best_seen_hw")
            else None,
        }
    if field == "best_objective":
        words = m2_words(data["best_objective_M2"])
        return {
            "label": label,
            "source_path": str(path),
            "source_kind": "beam:best_objective",
            "hw": data["best_objective_hw"],
            "lane_hw": data["best_objective_lane_hw"],
            "cg_sum": cg_sum(data["best_objective_lane_hw"]),
            "m2_weight": popcount_words(words),
            "target_l1": None,
            "M2": data["best_objective_M2"],
            "bits": data.get("best_objective_bits"),
        }
    raise SystemExit(f"unsupported beam field {field}")


def parse_combo_entry(raw):
    path_raw, group, index_raw, label = raw.split(":", 3)
    return extract_combo(Path(path_raw), group, int(index_raw), label)


def parse_beam_entry(raw):
    path_raw, field, label = raw.split(":", 2)
    return extract_beam(Path(path_raw), field, label)


def parse_target(raw):
    label, lane_raw = raw.split(":", 1)
    return label, parse_lane(lane_raw)


def add_distances(witnesses, targets):
    for witness in witnesses:
        lane = witness["lane_hw"]
        witness["distances"] = {
            label: {
                "l1": lane_l1(lane, target_lane),
                "linf": lane_linf(lane, target_lane),
            }
            for label, target_lane in targets.items()
        }
    for left in witnesses:
        left_words = m2_words(left.get("M2"))
        left["m2_distances"] = {}
        for right in witnesses:
            if left["label"] == right["label"]:
                continue
            left["m2_distances"][right["label"]] = m2_distance(left_words, m2_words(right.get("M2")))


def markdown(witnesses, target_labels):
    headers = ["label", "HW", "lane", "c+g", "M2 wt"] + [f"L1 {label}" for label in target_labels]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for witness in witnesses:
        values = [
            witness["label"],
            str(witness["hw"]),
            "[" + ", ".join(str(x) for x in witness["lane_hw"]) + "]",
            str(witness["cg_sum"]),
            str(witness["m2_weight"]),
        ]
        values.extend(str(witness["distances"][label]["l1"]) for label in target_labels)
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--combo-entry", action="append", default=[],
                    help="PATH:GROUP:INDEX:LABEL, e.g. file.json:top_by_hw:0:F788_HW86")
    ap.add_argument("--beam-entry", action="append", default=[],
                    help="PATH:FIELD:LABEL, FIELD is best_seen or best_objective")
    ap.add_argument("--target", action="append", default=[],
                    help="LABEL:v0,v1,v2,v3,v4,v5,v6,v7")
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown-out")
    args = ap.parse_args()

    witnesses = [parse_combo_entry(raw) for raw in args.combo_entry]
    witnesses.extend(parse_beam_entry(raw) for raw in args.beam_entry)
    targets = dict(parse_target(raw) for raw in args.target)
    add_distances(witnesses, targets)

    payload = {
        "description": "M2 witness lane comparison",
        "targets": targets,
        "witnesses": witnesses,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")

    if args.markdown_out:
        md_out = Path(args.markdown_out)
        md_out.parent.mkdir(parents=True, exist_ok=True)
        md_out.write_text(markdown(witnesses, list(targets)))
        print(f"wrote {out} and {md_out}")
    else:
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
