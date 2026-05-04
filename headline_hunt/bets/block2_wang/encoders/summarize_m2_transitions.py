#!/usr/bin/env python3
"""Summarize bit-level transitions between named M2 witnesses."""

import argparse
from collections import Counter
import json
from pathlib import Path


def parse_words(raw_words):
    return [int(word, 16) if isinstance(word, str) else int(word) for word in raw_words]


def bit_positions(words):
    out = set()
    for word_idx, word in enumerate(words):
        for bit in range(32):
            if word & (1 << bit):
                out.add(word_idx * 32 + bit)
    return out


def word_hist(bits):
    return dict(sorted(Counter(bit // 32 for bit in bits).items()))


def parse_transition(raw):
    left, right = raw.split(":", 1)
    return left, right


def summarize_transition(witnesses, left_label, right_label):
    left = witnesses[left_label]
    right = witnesses[right_label]
    left_bits = bit_positions(parse_words(left["M2"]))
    right_bits = bit_positions(parse_words(right["M2"]))
    added = sorted(right_bits - left_bits)
    removed = sorted(left_bits - right_bits)
    toggled = sorted(left_bits ^ right_bits)
    return {
        "label": f"{left_label}_to_{right_label}",
        "from": left_label,
        "to": right_label,
        "from_hw": left["hw"],
        "to_hw": right["hw"],
        "from_lane_hw": left["lane_hw"],
        "to_lane_hw": right["lane_hw"],
        "from_m2_weight": left["m2_weight"],
        "to_m2_weight": right["m2_weight"],
        "m2_weight_delta": right["m2_weight"] - left["m2_weight"],
        "hamming_distance": len(toggled),
        "added_count": len(added),
        "removed_count": len(removed),
        "added_bits": added,
        "removed_bits": removed,
        "toggled_bits": toggled,
        "added_word_hist": word_hist(added),
        "removed_word_hist": word_hist(removed),
        "toggled_word_hist": word_hist(toggled),
    }


def markdown(transitions):
    headers = [
        "transition",
        "HW",
        "M2 wt",
        "dist",
        "add",
        "remove",
        "add words",
        "remove words",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for transition in transitions:
        values = [
            transition["label"],
            f"{transition['from_hw']}->{transition['to_hw']}",
            f"{transition['from_m2_weight']}->{transition['to_m2_weight']}",
            str(transition["hamming_distance"]),
            str(transition["added_count"]),
            str(transition["removed_count"]),
            json.dumps(transition["added_word_hist"], sort_keys=True),
            json.dumps(transition["removed_word_hist"], sort_keys=True),
        ]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--witness-json", required=True)
    ap.add_argument("--transition", action="append", default=[],
                    help="FROM_LABEL:TO_LABEL")
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown-out")
    args = ap.parse_args()

    data = json.loads(Path(args.witness_json).read_text())
    witnesses = {witness["label"]: witness for witness in data["witnesses"]}
    transitions = [
        summarize_transition(witnesses, *parse_transition(raw))
        for raw in args.transition
    ]
    payload = {
        "description": "M2 witness transition summary",
        "witness_json": args.witness_json,
        "transitions": transitions,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")

    if args.markdown_out:
        md_out = Path(args.markdown_out)
        md_out.parent.mkdir(parents=True, exist_ok=True)
        md_out.write_text(markdown(transitions))
        print(f"wrote {out} and {md_out}")
    else:
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
