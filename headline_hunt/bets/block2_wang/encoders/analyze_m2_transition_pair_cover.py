#!/usr/bin/env python3
"""Analyze how known M2 beam transitions decompose into ranked pair moves."""

import argparse
from collections import Counter
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
    m2_weight,
    objective_value,
    parse_w_arr,
)


BIT_DOMAIN = tuple(range(16 * 32))


def parse_words(raw_words):
    return [int(word, 16) if isinstance(word, str) else int(word) for word in raw_words]


def format_words(words):
    return [f"0x{word:08x}" for word in words]


def bit_is_set(words, bit_idx):
    return bool(words[bit_idx // 32] & (1 << (bit_idx % 32)))


def classify_bits(base_m2, bits):
    added = []
    removed = []
    for bit_idx in bits:
        if bit_is_set(base_m2, bit_idx):
            removed.append(bit_idx)
        else:
            added.append(bit_idx)
    return added, removed


def word_hist(bits):
    return dict(sorted(Counter(bit // 32 for bit in bits).items()))


def parse_transition(raw):
    path_raw, index_raw, label = raw.split(":", 2)
    path = Path(path_raw)
    data = json.loads(path.read_text())
    index = int(index_raw)
    records = data.get("top_records") or []
    if index >= len(records):
        raise SystemExit(f"{path} has only {len(records)} top_records, cannot use index {index}")
    record = records[index]
    return {
        "label": label,
        "source_path": str(path),
        "seed_jsonl": data["seed_jsonl"],
        "seed_rank": data["seed_rank"],
        "rounds": data["rounds"],
        "pair_pool": data["pair_pool"],
        "pair_rank": data.get("pair_rank") or data.get("objective") or "hw",
        "lane_weights": data.get("lane_weights") or [1.0] * 8,
        "cg_weight": data.get("cg_weight", 1.0),
        "target_lane": data.get("target_lane"),
        "target_weight": data.get("target_weight", 1.0),
        "m2_weight_penalty": data.get("m2_weight_penalty") or 0.0,
        "init_M2": parse_words(data["init_M2"]),
        "target_M2": parse_words(record["M2"]),
        "target_bits": sorted(record["bits"]),
        "target_hw": record["hw"],
        "target_lane_hw": record["lane_hw"],
        "target_depth": record["depth"],
    }


def context_for_transition(transition):
    seed, _ = load_seed(transition["seed_jsonl"], transition["seed_rank"])
    diff63 = parse_w_arr(seed["block1_diff63"])
    iv1 = list(IV)
    iv2 = [iv1[i] ^ diff63[i] for i in range(8)]
    m1_w = expand_schedule([0] * 16)
    return iv1, iv2, m1_w


def evaluate_pair_pool(transition):
    iv1, iv2, m1_w = context_for_transition(transition)
    base_m2 = transition["init_M2"]
    base_weight = m2_weight(base_m2)
    pair_records = []
    for left_pos, left_bit in enumerate(BIT_DOMAIN):
        for right_bit in BIT_DOMAIN[left_pos + 1:]:
            m2 = list(base_m2)
            for bit_idx in (left_bit, right_bit):
                m2[bit_idx // 32] ^= 1 << (bit_idx % 32)
            hw, diff = eval_m2(iv1, iv2, m1_w, m2, transition["rounds"])
            lane_hw = hw_per_lane(diff)
            weight = m2_weight(m2)
            obj = objective_value(
                hw,
                lane_hw,
                transition["pair_rank"],
                transition["lane_weights"],
                transition["cg_weight"],
                transition["target_lane"],
                transition["target_weight"],
                weight,
                transition["m2_weight_penalty"],
            )
            bits = (left_bit, right_bit)
            added, removed = classify_bits(base_m2, bits)
            pair_records.append({
                "bits": bits,
                "rank_objective": round(obj, 6),
                "hw": hw,
                "lane_hw": lane_hw,
                "m2_weight": weight,
                "weight_delta": weight - base_weight,
                "added_bits": added,
                "removed_bits": removed,
            })
    pair_records.sort(key=lambda record: (
        record["rank_objective"],
        record["hw"],
        record["bits"][0],
        record["bits"][1],
    ))
    by_bits = {}
    for rank, record in enumerate(pair_records, 1):
        record["pair_rank"] = rank
        by_bits[record["bits"]] = record
    return by_bits


def perfect_matchings(bits):
    bits = tuple(bits)
    if not bits:
        yield []
        return
    first = bits[0]
    for idx in range(1, len(bits)):
        second = bits[idx]
        rest = bits[1:idx] + bits[idx + 1:]
        for matching in perfect_matchings(rest):
            yield [(first, second)] + matching


def compact_pair(record):
    return {
        "bits": list(record["bits"]),
        "pair_rank": record["pair_rank"],
        "rank_objective": record["rank_objective"],
        "hw": record["hw"],
        "lane_hw": record["lane_hw"],
        "m2_weight": record["m2_weight"],
        "weight_delta": record["weight_delta"],
        "added_bits": record["added_bits"],
        "removed_bits": record["removed_bits"],
    }


def compact_cover(pair_records, pair_pool):
    ranks = [record["pair_rank"] for record in pair_records]
    hws = [record["hw"] for record in pair_records]
    objectives = [record["rank_objective"] for record in pair_records]
    shapes = Counter(
        f"add{len(record['added_bits'])}_remove{len(record['removed_bits'])}"
        for record in pair_records
    )
    added = [bit for record in pair_records for bit in record["added_bits"]]
    removed = [bit for record in pair_records for bit in record["removed_bits"]]
    return {
        "pair_count": len(pair_records),
        "all_pairs_in_pool": max(ranks) <= pair_pool,
        "max_rank": max(ranks),
        "sum_rank": sum(ranks),
        "max_hw": max(hws),
        "sum_hw": sum(hws),
        "max_rank_objective": max(objectives),
        "sum_rank_objective": round(sum(objectives), 6),
        "transition_shape_hist": dict(sorted(shapes.items())),
        "added_word_hist": word_hist(added),
        "removed_word_hist": word_hist(removed),
        "pairs": [compact_pair(record) for record in pair_records],
    }


def cover_key(cover, mode):
    if mode == "max_rank":
        return (cover["max_rank"], cover["sum_rank"], cover["max_hw"], cover["sum_hw"])
    if mode == "sum_rank":
        return (cover["sum_rank"], cover["max_rank"], cover["sum_hw"], cover["max_hw"])
    if mode == "max_hw":
        return (cover["max_hw"], cover["sum_hw"], cover["max_rank"], cover["sum_rank"])
    raise ValueError(mode)


def analyze_transition(transition):
    t0 = time.time()
    base_m2 = transition["init_M2"]
    target_m2 = transition["target_M2"]
    toggled = sorted(
        bit
        for bit in BIT_DOMAIN
        if bit_is_set(base_m2, bit) != bit_is_set(target_m2, bit)
    )
    if toggled != transition["target_bits"]:
        raise SystemExit(
            f"{transition['label']} target bits mismatch: record has "
            f"{transition['target_bits']} but M2 diff gives {toggled}"
        )
    if len(toggled) % 2:
        raise SystemExit(f"{transition['label']} has odd toggled-bit count {len(toggled)}")

    iv1, iv2, m1_w = context_for_transition(transition)
    source_hw, source_diff = eval_m2(iv1, iv2, m1_w, base_m2, transition["rounds"])
    target_hw, target_diff = eval_m2(iv1, iv2, m1_w, target_m2, transition["rounds"])
    if target_hw != transition["target_hw"]:
        raise SystemExit(
            f"{transition['label']} target HW mismatch: record {transition['target_hw']} "
            f"evaluated {target_hw}"
        )

    pair_by_bits = evaluate_pair_pool(transition)
    all_transition_pairs = [
        compact_pair(pair_by_bits[(toggled[left], toggled[right])])
        for left in range(len(toggled))
        for right in range(left + 1, len(toggled))
    ]
    covers_in_pool = 0
    best_by_mode = {}
    cover_count = 0
    for matching in perfect_matchings(toggled):
        cover_count += 1
        pairs = [pair_by_bits[tuple(pair)] for pair in matching]
        cover = compact_cover(pairs, transition["pair_pool"])
        if cover["all_pairs_in_pool"]:
            covers_in_pool += 1
        for mode in ("max_rank", "sum_rank", "max_hw"):
            previous = best_by_mode.get(mode)
            if previous is None or cover_key(cover, mode) < cover_key(previous, mode):
                best_by_mode[mode] = cover

    added, removed = classify_bits(base_m2, toggled)
    return {
        "label": transition["label"],
        "source_path": transition["source_path"],
        "rounds": transition["rounds"],
        "pair_rank": transition["pair_rank"],
        "pair_pool": transition["pair_pool"],
        "source_hw": source_hw,
        "source_lane_hw": hw_per_lane(source_diff),
        "source_m2_weight": m2_weight(base_m2),
        "target_hw": target_hw,
        "target_lane_hw": hw_per_lane(target_diff),
        "target_m2_weight": m2_weight(target_m2),
        "target_depth": transition["target_depth"],
        "transition_bits": toggled,
        "transition_bit_count": len(toggled),
        "transition_added_bits": added,
        "transition_removed_bits": removed,
        "transition_added_word_hist": word_hist(added),
        "transition_removed_word_hist": word_hist(removed),
        "source_M2": format_words(base_m2),
        "target_M2": format_words(target_m2),
        "transition_pair_count": len(all_transition_pairs),
        "transition_pairs": sorted(
            all_transition_pairs,
            key=lambda record: (record["pair_rank"], record["hw"], record["bits"]),
        ),
        "cover_count": cover_count,
        "covers_all_pairs_in_pool": covers_in_pool,
        "best_covers": best_by_mode,
        "wall_seconds": round(time.time() - t0, 2),
    }


def markdown(results):
    lines = [
        "# M2 Transition Pair Covers",
        "",
        "| transition | HW | M2 wt | bits | covers in pool | best max-rank | best sum-rank | best max-HW |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for result in results:
        max_rank = result["best_covers"]["max_rank"]
        sum_rank = result["best_covers"]["sum_rank"]
        max_hw = result["best_covers"]["max_hw"]
        lines.append(
            "| {label} | {source_hw}->{target_hw} | {source_wt}->{target_wt} | {bits} | "
            "{covers}/{total} | {max_rank_value} | {sum_rank_value} | {max_hw_value} |".format(
                label=result["label"],
                source_hw=result["source_hw"],
                target_hw=result["target_hw"],
                source_wt=result["source_m2_weight"],
                target_wt=result["target_m2_weight"],
                bits=result["transition_bit_count"],
                covers=result["covers_all_pairs_in_pool"],
                total=result["cover_count"],
                max_rank_value=max_rank["max_rank"],
                sum_rank_value=sum_rank["sum_rank"],
                max_hw_value=max_hw["max_hw"],
            )
        )
    for result in results:
        lines.extend([
            "",
            f"## {result['label']}",
            "",
            "| mode | max rank | sum rank | max HW | sum HW | shapes | pairs |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ])
        for mode in ("max_rank", "sum_rank", "max_hw"):
            cover = result["best_covers"][mode]
            pair_summary = [
                {
                    "bits": pair["bits"],
                    "rank": pair["pair_rank"],
                    "hw": pair["hw"],
                    "delta": pair["weight_delta"],
                }
                for pair in cover["pairs"]
            ]
            lines.append(
                f"| {mode} | {cover['max_rank']} | {cover['sum_rank']} | "
                f"{cover['max_hw']} | {cover['sum_hw']} | "
                f"{json.dumps(cover['transition_shape_hist'], sort_keys=True)} | "
                f"{json.dumps(pair_summary)} |"
            )
        lines.extend([
            "",
            "| pair bits | rank | obj | HW | delta | added | removed |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ])
        for pair in result["transition_pairs"][:16]:
            lines.append(
                f"| {pair['bits']} | {pair['pair_rank']} | {pair['rank_objective']} | "
                f"{pair['hw']} | {pair['weight_delta']:+d} | "
                f"{pair['added_bits']} | {pair['removed_bits']} |"
            )
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--transition", action="append", default=[],
                    help="BEAM_JSON:TOP_RECORD_INDEX:LABEL")
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown-out")
    args = ap.parse_args()

    if not args.transition:
        raise SystemExit("provide at least one --transition")

    results = []
    for raw in args.transition:
        transition = parse_transition(raw)
        print(f"[cover] {transition['label']} from {transition['source_path']}")
        result = analyze_transition(transition)
        results.append(result)
        print(
            f"  HW {result['source_hw']}->{result['target_hw']} "
            f"M2 {result['source_m2_weight']}->{result['target_m2_weight']} "
            f"covers_in_pool={result['covers_all_pairs_in_pool']}/{result['cover_count']} "
            f"wall={result['wall_seconds']}s"
        )

    payload = {
        "description": "M2 transition pair-cover analysis",
        "results": results,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    if args.markdown_out:
        md_out = Path(args.markdown_out)
        md_out.parent.mkdir(parents=True, exist_ok=True)
        md_out.write_text(markdown(results))
        print(f"wrote {out} and {md_out}")
    else:
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
