#!/usr/bin/env python3
"""Forecast local M2 repair geometry around selected witnesses.

For each witness, enumerate every 2-bit M2 flip from that witness and report
where the best one-pair repair opportunities live: sparse/additive/removal
shape, M2-weight buckets, and word-local additions. This is a cheap diagnostic
before spending beam time on a branch.
"""

import argparse
from collections import Counter
import heapq
import json
from pathlib import Path
import sys
import time

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from block2_m2_pair_beam import (  # noqa: E402
    IV,
    eval_m2,
    expand_schedule,
    hw_per_lane,
    load_seed,
    parse_w_arr,
)


BIT_DOMAIN = tuple(range(16 * 32))


def parse_words(raw_words):
    return [int(word, 16) if isinstance(word, str) else int(word) for word in raw_words]


def format_words(words):
    return [f"0x{word:08x}" for word in words]


def lane_l1(left, right):
    return sum(abs(a - b) for a, b in zip(left, right))


def word_hist(bits):
    return dict(sorted(Counter(bit // 32 for bit in bits).items()))


def parse_lane(raw):
    parts = [int(part.strip()) for part in raw.split(",") if part.strip()]
    if len(parts) != 8:
        raise SystemExit(f"lane needs 8 comma-separated integers: {raw}")
    return parts


def parse_target(raw):
    label, lane_raw = raw.split(":", 1)
    return label, parse_lane(lane_raw)


def parse_combo_entry(raw):
    path_raw, group, index_raw, label = raw.split(":", 3)
    path = Path(path_raw)
    data = json.loads(path.read_text())
    record = data[group][int(index_raw)]
    return {
        "label": label,
        "source_path": str(path),
        "source_kind": f"combo:{group}[{index_raw}]",
        "seed_jsonl": data["seed_jsonl"],
        "seed_rank": data["seed_rank"],
        "rounds": data["rounds"],
        "claimed_hw": record.get("hw_total"),
        "claimed_lane_hw": record.get("lane_hw"),
        "M2": parse_words(record["M2"]),
    }


def parse_beam_entry(raw):
    path_raw, field, label = raw.split(":", 2)
    path = Path(path_raw)
    data = json.loads(path.read_text())
    if field == "best_seen":
        m2_key = "best_seen_M2"
        hw_key = "best_seen_hw"
        lane_key = "best_seen_lane_hw"
    elif field == "best_objective":
        m2_key = "best_objective_M2"
        hw_key = "best_objective_hw"
        lane_key = "best_objective_lane_hw"
    else:
        raise SystemExit(f"unsupported beam field {field}")
    return {
        "label": label,
        "source_path": str(path),
        "source_kind": f"beam:{field}",
        "seed_jsonl": data["seed_jsonl"],
        "seed_rank": data["seed_rank"],
        "rounds": data["rounds"],
        "claimed_hw": data.get(hw_key),
        "claimed_lane_hw": data.get(lane_key),
        "M2": parse_words(data[m2_key]),
    }


def compact_record(record, targets):
    out = {
        "hw": record["hw"],
        "lane_hw": record["lane_hw"],
        "m2_weight": record["m2_weight"],
        "weight_delta": record["weight_delta"],
        "bits": record["bits"],
        "added_bits": record["added_bits"],
        "removed_bits": record["removed_bits"],
        "added_word_hist": word_hist(record["added_bits"]),
        "removed_word_hist": word_hist(record["removed_bits"]),
    }
    if targets:
        out["target_l1"] = {
            label: lane_l1(record["lane_hw"], lane)
            for label, lane in targets.items()
        }
    return out


def better(left, right):
    if right is None:
        return True
    return (
        left["hw"],
        abs(left["weight_delta"]),
        left["m2_weight"],
        left["bits"],
    ) < (
        right["hw"],
        abs(right["weight_delta"]),
        right["m2_weight"],
        right["bits"],
    )


def update_best(mapping, key, record):
    previous = mapping.get(key)
    if previous is None or better(record, previous):
        mapping[key] = record


class BoundedTop:
    def __init__(self, limit):
        self.limit = limit
        self.heap = []
        self.counter = 0

    @staticmethod
    def key(record):
        return (
            record["hw"],
            abs(record["weight_delta"]),
            record["m2_weight"],
            record["bits"][0],
            record["bits"][1],
        )

    @staticmethod
    def heap_key(key):
        return tuple(-value for value in key)

    def add(self, record):
        if self.limit <= 0:
            return
        key = self.key(record)
        entry = (self.heap_key(key), self.counter, key, record)
        self.counter += 1
        if len(self.heap) < self.limit:
            heapq.heappush(self.heap, entry)
            return
        if key < self.heap[0][2]:
            heapq.heapreplace(self.heap, entry)

    def records(self):
        return [
            entry[3]
            for entry in sorted(self.heap, key=lambda entry: entry[2])
        ]


def summarize_pool(records, base_hw, base_weight):
    if not records:
        return {}
    weights = [record["m2_weight"] for record in records]
    deltas = Counter(record["weight_delta"] for record in records)
    shapes = Counter(
        f"add{len(record['added_bits'])}_remove{len(record['removed_bits'])}"
        for record in records
    )
    return {
        "count": len(records),
        "hw_min": min(record["hw"] for record in records),
        "hw_max": max(record["hw"] for record in records),
        "improved_count": sum(1 for record in records if record["hw"] < base_hw),
        "m2_weight_min": min(weights),
        "m2_weight_max": max(weights),
        "m2_weight_delta_min": min(weights) - base_weight,
        "m2_weight_delta_max": max(weights) - base_weight,
        "weight_delta_hist": dict(sorted((str(k), v) for k, v in deltas.items())),
        "transition_shape_hist": dict(sorted(shapes.items())),
    }


def evaluate_witness(witness, targets, top_n, pool_n):
    seed, _ = load_seed(witness["seed_jsonl"], witness["seed_rank"])
    diff63 = parse_w_arr(seed["block1_diff63"])
    iv1 = list(IV)
    iv2 = [iv1[i] ^ diff63[i] for i in range(8)]
    m1_w = expand_schedule([0] * 16)
    base_m2 = witness["M2"]
    base_hw, base_diff = eval_m2(iv1, iv2, m1_w, base_m2, witness["rounds"])
    base_lane = hw_per_lane(base_diff)
    base_weight = sum(word.bit_count() for word in base_m2)

    if witness["claimed_hw"] is not None and witness["claimed_hw"] != base_hw:
        raise SystemExit(
            f"{witness['label']} HW mismatch: claimed {witness['claimed_hw']} "
            f"evaluated {base_hw}"
        )

    top_by_hw = BoundedTop(top_n)
    pool_by_hw = BoundedTop(pool_n)
    by_new_weight = {}
    by_weight_delta = {}
    by_transition_shape = {}
    by_added_word_count = {str(word): {} for word in range(16)}
    improved_count = 0
    total_pairs = 0
    t0 = time.time()

    for left_idx, left_bit in enumerate(BIT_DOMAIN):
        for right_bit in BIT_DOMAIN[left_idx + 1:]:
            total_pairs += 1
            m2 = list(base_m2)
            added_bits = []
            removed_bits = []
            for bit_idx in (left_bit, right_bit):
                word_idx = bit_idx // 32
                bit = bit_idx % 32
                mask = 1 << bit
                if m2[word_idx] & mask:
                    removed_bits.append(bit_idx)
                else:
                    added_bits.append(bit_idx)
                m2[word_idx] ^= mask
            hw, diff = eval_m2(iv1, iv2, m1_w, m2, witness["rounds"])
            lane = hw_per_lane(diff)
            m2_weight_value = sum(word.bit_count() for word in m2)
            record = {
                "hw": hw,
                "lane_hw": lane,
                "m2_weight": m2_weight_value,
                "weight_delta": m2_weight_value - base_weight,
                "bits": [left_bit, right_bit],
                "added_bits": added_bits,
                "removed_bits": removed_bits,
            }
            compact = compact_record(record, targets)
            if hw < base_hw:
                improved_count += 1
            top_by_hw.add(compact)
            pool_by_hw.add(compact)
            update_best(by_new_weight, str(m2_weight_value), compact)
            update_best(by_weight_delta, str(record["weight_delta"]), compact)
            shape = f"add{len(added_bits)}_remove{len(removed_bits)}"
            update_best(by_transition_shape, shape, compact)
            added_hist = word_hist(added_bits)
            for word in range(16):
                count = str(added_hist.get(word, 0))
                update_best(by_added_word_count[str(word)], count, compact)

    elapsed = time.time() - t0
    top_records = top_by_hw.records()
    pool_records = pool_by_hw.records()
    return {
        "label": witness["label"],
        "source_path": witness["source_path"],
        "source_kind": witness["source_kind"],
        "seed_jsonl": witness["seed_jsonl"],
        "seed_rank": witness["seed_rank"],
        "rounds": witness["rounds"],
        "base_hw": base_hw,
        "base_lane_hw": base_lane,
        "base_m2_weight": base_weight,
        "base_M2": format_words(base_m2),
        "total_pairs": total_pairs,
        "improved_pairs": improved_count,
        "improved_fraction": round(improved_count / total_pairs, 8),
        "top_by_hw": top_records,
        "pair_pool_by_hw_summary": summarize_pool(pool_records, base_hw, base_weight),
        "best_by_new_m2_weight": dict(sorted(by_new_weight.items(), key=lambda item: int(item[0]))),
        "best_by_weight_delta": dict(sorted(by_weight_delta.items(), key=lambda item: int(item[0]))),
        "best_by_transition_shape": dict(sorted(by_transition_shape.items())),
        "best_by_added_word_count": by_added_word_count,
        "wall_seconds": round(elapsed, 2),
    }


def markdown(results, targets):
    lines = [
        "# M2 Repair Forecast",
        "",
        "| witness | base HW | lane | M2 wt | improved pairs | best 1-pair HW | best wt/delta | pool HW | pool wt delta |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for result in results:
        best = result["top_by_hw"][0]
        pool = result["pair_pool_by_hw_summary"]
        lines.append(
            "| {label} | {base_hw} | {lane} | {base_wt} | {improved}/{total} | "
            "{best_hw} | {best_wt}/{best_delta:+d} | {pool_hw_min}..{pool_hw_max} | "
            "{pool_delta_min:+d}..{pool_delta_max:+d} |".format(
                label=result["label"],
                base_hw=result["base_hw"],
                lane=result["base_lane_hw"],
                base_wt=result["base_m2_weight"],
                improved=result["improved_pairs"],
                total=result["total_pairs"],
                best_hw=best["hw"],
                best_wt=best["m2_weight"],
                best_delta=best["weight_delta"],
                pool_hw_min=pool["hw_min"],
                pool_hw_max=pool["hw_max"],
                pool_delta_min=pool["m2_weight_delta_min"],
                pool_delta_max=pool["m2_weight_delta_max"],
            )
        )
    for result in results:
        lines.extend([
            "",
            f"## {result['label']}",
            "",
            "| shape | best HW | lane | M2 wt | bits | added | removed |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ])
        for shape, record in result["best_by_transition_shape"].items():
            lines.append(
                f"| {shape} | {record['hw']} | {record['lane_hw']} | "
                f"{record['m2_weight']} | {record['bits']} | "
                f"{record['added_bits']} | {record['removed_bits']} |"
            )
        lines.extend([
            "",
            "| top | HW | lane | M2 wt | delta | bits | target L1 |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ])
        for index, record in enumerate(result["top_by_hw"][:8], 1):
            target_summary = ""
            if targets:
                target_summary = json.dumps(record.get("target_l1", {}), sort_keys=True)
            lines.append(
                f"| {index} | {record['hw']} | {record['lane_hw']} | "
                f"{record['m2_weight']} | {record['weight_delta']:+d} | "
                f"{record['bits']} | {target_summary} |"
            )
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--combo-entry", action="append", default=[],
                    help="PATH:GROUP:INDEX:LABEL")
    ap.add_argument("--beam-entry", action="append", default=[],
                    help="PATH:FIELD:LABEL, FIELD is best_seen or best_objective")
    ap.add_argument("--target", action="append", default=[],
                    help="LABEL:v0,v1,v2,v3,v4,v5,v6,v7")
    ap.add_argument("--top-n", type=int, default=20)
    ap.add_argument("--pair-pool", type=int, default=1024)
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown-out")
    args = ap.parse_args()

    witnesses = [parse_combo_entry(raw) for raw in args.combo_entry]
    witnesses.extend(parse_beam_entry(raw) for raw in args.beam_entry)
    if not witnesses:
        raise SystemExit("provide at least one --combo-entry or --beam-entry")
    targets = dict(parse_target(raw) for raw in args.target)

    results = []
    for witness in witnesses:
        print(f"[forecast] {witness['label']} from {witness['source_kind']}")
        result = evaluate_witness(witness, targets, args.top_n, args.pair_pool)
        results.append(result)
        best = result["top_by_hw"][0]
        print(
            f"  base HW={result['base_hw']} M2 wt={result['base_m2_weight']} "
            f"best 1-pair HW={best['hw']} wt={best['m2_weight']} "
            f"improved={result['improved_pairs']}/{result['total_pairs']} "
            f"wall={result['wall_seconds']}s"
        )

    payload = {
        "description": "M2 one-pair repair forecast around selected witnesses",
        "targets": targets,
        "top_n": args.top_n,
        "pair_pool": args.pair_pool,
        "results": results,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    if args.markdown_out:
        md_out = Path(args.markdown_out)
        md_out.parent.mkdir(parents=True, exist_ok=True)
        md_out.write_text(markdown(results, targets))
        print(f"wrote {out} and {md_out}")
    else:
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
