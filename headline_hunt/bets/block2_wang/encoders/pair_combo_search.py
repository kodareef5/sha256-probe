#!/usr/bin/env python3
"""Rank exact two-bit W deltas, then combine the best pairs.

F443/F444 showed one-bit soft directions are too W60-local. This script
uses pair deltas as the primitive: enumerate every two-bit move, rank pairs
by resulting residual HW/bridge score, then combine top-ranked pairs into
larger jumps. The output is a pilot search and a pair atlas, not a closure.
"""

import argparse
from itertools import combinations
import json
from pathlib import Path
import sys
import time

REPO = Path(__file__).resolve().parents[4]
ENCODERS = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(ENCODERS))

from block2_bridge_beam import setup_cand, evaluate
from bridge_score import bridge_score
from enumerate_hamming_ball import parse_w, parse_slots, flip_bits, find_cand
from ranked_combo_search import bit_label, keep_top, record_combo


def pair_label(bits: tuple[int, int]) -> list[dict]:
    return [bit_label(b) for b in bits]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--init-W", required=True)
    ap.add_argument("--init-hw", type=int, required=True)
    ap.add_argument("--slots", default="57,58,59,60")
    ap.add_argument("--top-pairs", type=int, default=128)
    ap.add_argument("--pair-rank", choices=["hw", "repair"], default="hw",
                    help="Rank pairs by resulting HW or by total lane repair")
    ap.add_argument("--pair-count", type=int, default=3)
    ap.add_argument("--min-radius", type=int, default=5)
    ap.add_argument("--max-radius", type=int, default=6)
    ap.add_argument("--top-records", type=int, default=20)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    if args.top_pairs < 1:
        raise SystemExit("--top-pairs must be >= 1")
    if args.pair_count < 1:
        raise SystemExit("--pair-count must be >= 1")
    if args.min_radius < 1 or args.max_radius < args.min_radius:
        raise SystemExit("invalid radius bounds")

    slots = parse_slots(args.slots)
    bit_domain = tuple(slot * 32 + bit for slot in slots for bit in range(32))

    short, m0, fill, kbit = find_cand(args.candidate)
    setup = setup_cand(m0, fill, kbit)
    if setup is None:
        raise SystemExit(f"{short} is not cascade-eligible")
    s1_init, s2_init, W1_pre, W2_pre = setup
    base_w = parse_w(args.init_W)

    init_rec = evaluate(s1_init, s2_init, W1_pre, W2_pre, m0, fill, kbit, *base_w)
    if init_rec is None:
        raise SystemExit("init-W violates cascade-1")
    if init_rec["hw_total"] != args.init_hw:
        raise SystemExit(f"init-HW mismatch: argument {args.init_hw}, evaluated {init_rec['hw_total']}")
    init_score = bridge_score(init_rec, kbit)["score"]
    if init_score is None:
        raise SystemExit("init-W fails bridge selector")

    print(
        f"=== pair_combo_search.py: {short} top_pairs={args.top_pairs} "
        f"pair_count={args.pair_count} radius={args.min_radius}..{args.max_radius} ==="
    )
    t0 = time.time()

    pair_counts = {"total": 0, "cascade1": 0, "bridge": 0}
    accepted_pairs = []
    for bits in combinations(bit_domain, 2):
        pair_counts["total"] += 1
        w = flip_bits(base_w, bits)
        rec = evaluate(s1_init, s2_init, W1_pre, W2_pre, m0, fill, kbit, *w)
        if rec is None:
            continue
        pair_counts["cascade1"] += 1
        score = bridge_score(rec, kbit)
        if score["score"] is None:
            continue
        pair_counts["bridge"] += 1
        delta = [rec["hw63"][i] - init_rec["hw63"][i] for i in range(8)]
        repairs = [max(0, -d) for d in delta]
        damage = [max(0, d) for d in delta]
        accepted_pairs.append({
            "bits": pair_label(bits),
            "bit_indices": list(bits),
            "hw_total": rec["hw_total"],
            "score": score["score"],
            "hw63": rec["hw63"],
            "delta_hw63": delta,
            "total_repair": sum(repairs),
            "total_damage": sum(damage),
            "net_delta": rec["hw_total"] - args.init_hw,
        })

    if args.pair_rank == "hw":
        accepted_pairs.sort(key=lambda e: (e["hw_total"], -e["score"], e["bit_indices"]))
    else:
        accepted_pairs.sort(key=lambda e: (-e["total_repair"], e["net_delta"], -e["score"], e["bit_indices"]))
    selected_pairs = accepted_pairs[:args.top_pairs]
    print(f"  pair bridge accepted: {pair_counts['bridge']} of {pair_counts['total']}")
    print(
        "  selected pairs:",
        ", ".join(
            "+".join(f"W{b['slot']}.{b['bit']}" for b in p["bits"])
            for p in selected_pairs[:8]
        ),
    )

    combo_counts = {
        "total": 0,
        "skipped_radius": 0,
        "skipped_duplicate": 0,
        "cascade1": 0,
        "bridge": 0,
        "hw_le_init": 0,
        "hw_lt_init": 0,
    }
    seen_unions = set()
    top_records = []
    new_records = []
    best_seen = {
        "hw_total": init_rec["hw_total"],
        "score": init_score,
        "bits": [],
        "W": [f"0x{x:08x}" for x in base_w],
        "record": init_rec,
    }

    for pair_ids in combinations(range(len(selected_pairs)), args.pair_count):
        bits = tuple(sorted({b for idx in pair_ids for b in selected_pairs[idx]["bit_indices"]}))
        if len(bits) < args.min_radius or len(bits) > args.max_radius:
            combo_counts["skipped_radius"] += 1
            continue
        if bits in seen_unions:
            combo_counts["skipped_duplicate"] += 1
            continue
        seen_unions.add(bits)
        combo_counts["total"] += 1
        w = flip_bits(base_w, bits)
        rec = evaluate(s1_init, s2_init, W1_pre, W2_pre, m0, fill, kbit, *w)
        if rec is None:
            continue
        combo_counts["cascade1"] += 1
        score = bridge_score(rec, kbit)
        if score["score"] is None:
            continue
        combo_counts["bridge"] += 1
        hw = rec["hw_total"]
        sc = score["score"]
        entry = record_combo(bits, hw, sc, w, rec)
        keep_top(top_records, entry, args.top_records)
        if hw < best_seen["hw_total"] or (hw == best_seen["hw_total"] and sc > best_seen["score"]):
            best_seen = entry
        if hw <= args.init_hw:
            combo_counts["hw_le_init"] += 1
            new_records.append(entry)
        if hw < args.init_hw:
            combo_counts["hw_lt_init"] += 1

    wall = time.time() - t0
    payload = {
        "description": f"{args.label}: pair combo search" if args.label else "pair combo search",
        "candidate": short,
        "init_W": [f"0x{x:08x}" for x in base_w],
        "init_hw": args.init_hw,
        "init_score": init_score,
        "slots": [57 + s for s in slots],
        "bit_domain_size": len(bit_domain),
        "top_pairs": args.top_pairs,
        "pair_rank": args.pair_rank,
        "pair_count": args.pair_count,
        "min_radius": args.min_radius,
        "max_radius": args.max_radius,
        "pair_counts": pair_counts,
        "selected_pairs": selected_pairs,
        "combo_counts": combo_counts,
        "best_seen": best_seen,
        "top_records": top_records,
        "new_records": new_records,
        "wall_seconds": round(wall, 2),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(
        f"  combos: total={combo_counts['total']} cascade1={combo_counts['cascade1']} "
        f"bridge={combo_counts['bridge']} hw<=init={combo_counts['hw_le_init']} "
        f"hw<init={combo_counts['hw_lt_init']}"
    )
    print(f"Total wall: {wall:.1f}s")
    print(f"best seen HW={best_seen['hw_total']} score={best_seen['score']}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
