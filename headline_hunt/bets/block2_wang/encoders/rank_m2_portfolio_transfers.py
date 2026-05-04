#!/usr/bin/env python3
"""Rank directed M2 portfolio transfer candidates from a witness-lane summary."""

import argparse
import json
from pathlib import Path


def lane_l1(left, right):
    return sum(abs(a - b) for a, b in zip(left, right))


def lane_linf(left, right):
    return max(abs(a - b) for a, b in zip(left, right))


def m2_words(raw_words):
    if raw_words is None:
        return None
    return [int(word, 16) if isinstance(word, str) else int(word) for word in raw_words]


def m2_distance(left, right):
    if left is None or right is None:
        return None
    return sum((a ^ b).bit_count() for a, b in zip(left, right))


def transfer_score(source, target, lane_distance, m2_dist):
    """Small heuristic for triage only; reports raw components next to score."""
    hw_direction_penalty = max(0, target["hw"] - source["hw"])
    m2_term = 0.0 if m2_dist is None else 0.2 * float(m2_dist)
    return float(lane_distance) + m2_term + 3.0 * float(hw_direction_penalty)


def classify(source, target, lane_distance, m2_dist):
    labels = []
    if target["hw"] < source["hw"]:
        labels.append("downhill")
    elif target["hw"] == source["hw"]:
        labels.append("same-hw")
    else:
        labels.append("uphill")
    if lane_distance <= 12:
        labels.append("near-lane")
    if m2_dist is not None and m2_dist <= 40:
        labels.append("near-m2")
    if abs(target["cg_sum"] - source["cg_sum"]) <= 2:
        labels.append("cg-close")
    return labels


def load_witnesses(path):
    data = json.loads(path.read_text())
    witnesses = data["witnesses"]
    for witness in witnesses:
        witness["_m2_words"] = m2_words(witness.get("M2"))
    return witnesses


def build_candidates(witnesses):
    rows = []
    for source in witnesses:
        for target in witnesses:
            if source["label"] == target["label"]:
                continue
            lane_distance = lane_l1(source["lane_hw"], target["lane_hw"])
            linf = lane_linf(source["lane_hw"], target["lane_hw"])
            m2_dist = m2_distance(source["_m2_words"], target["_m2_words"])
            score = transfer_score(source, target, lane_distance, m2_dist)
            rows.append({
                "source": source["label"],
                "target": target["label"],
                "source_hw": source["hw"],
                "target_hw": target["hw"],
                "hw_delta_target_minus_source": target["hw"] - source["hw"],
                "source_lane_hw": source["lane_hw"],
                "target_lane_hw": target["lane_hw"],
                "lane_l1": lane_distance,
                "lane_linf": linf,
                "source_m2_weight": source["m2_weight"],
                "target_m2_weight": target["m2_weight"],
                "m2_xor_distance": m2_dist,
                "source_cg_sum": source["cg_sum"],
                "target_cg_sum": target["cg_sum"],
                "score": round(score, 3),
                "tags": classify(source, target, lane_distance, m2_dist),
                "source_path": source["source_path"],
                "target_path": target["source_path"],
            })
    rows.sort(key=lambda row: (row["score"], row["lane_l1"], row["m2_xor_distance"], row["target_hw"], row["source"]))
    return rows


def markdown(rows, limit):
    headers = [
        "rank",
        "source",
        "target",
        "HW",
        "lane L1",
        "M2 xor",
        "score",
        "tags",
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for idx, row in enumerate(rows[:limit], start=1):
        hw = f"{row['source_hw']} -> {row['target_hw']}"
        values = [
            str(idx),
            row["source"],
            row["target"],
            hw,
            str(row["lane_l1"]),
            str(row["m2_xor_distance"]),
            f"{row['score']:.1f}",
            ", ".join(row["tags"]),
        ]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--witness-json", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown-out")
    ap.add_argument("--top", type=int, default=30)
    args = ap.parse_args()

    witness_path = Path(args.witness_json)
    witnesses = load_witnesses(witness_path)
    candidates = build_candidates(witnesses)
    payload = {
        "description": "Directed M2 portfolio transfer ranking",
        "source_witness_json": str(witness_path),
        "scoring_note": "score = lane_l1 + 0.2*m2_xor_distance + 3*max(0, target_hw-source_hw)",
        "n_witnesses": len(witnesses),
        "n_candidates": len(candidates),
        "candidates": candidates,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")

    if args.markdown_out:
        md = Path(args.markdown_out)
        md.parent.mkdir(parents=True, exist_ok=True)
        md.write_text(markdown(candidates, args.top))
        print(f"wrote {out} and {md}")
    else:
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
