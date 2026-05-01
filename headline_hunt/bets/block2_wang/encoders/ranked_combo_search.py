#!/usr/bin/env python3
"""Rank soft W-bit directions, then enumerate higher-radius combos.

The full radius-4 shells around the top Path C records are now closed.
This tool tries a different coordinate: first rank all single-bit moves by
their resulting residual HW/bridge score, then enumerate radius-r
combinations inside only the top-K soft directions. It is a selective
radius-5/6 probe, not a proof of closure.
"""

import argparse
from collections import Counter
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


def parse_radii(raw: str) -> tuple[int, ...]:
    radii = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        val = int(part, 10)
        if val < 1:
            raise ValueError("--radii values must be >= 1")
        radii.append(val)
    if not radii:
        raise ValueError("--radii must contain at least one value")
    return tuple(dict.fromkeys(radii))


def bit_label(idx: int) -> dict:
    return {"bit_index": idx, "slot": 57 + idx // 32, "bit": idx % 32}


def record_combo(bits: tuple[int, ...], hw: int, score: float, w: tuple[int, ...], rec: dict) -> dict:
    return {
        "bits": [bit_label(b) for b in bits],
        "hw_total": hw,
        "score": score,
        "W": [f"0x{x:08x}" for x in w],
        "record": rec,
    }


def keep_top(top: list[dict], entry: dict, limit: int) -> None:
    top.append(entry)
    top.sort(key=lambda e: (e["hw_total"], -e["score"]))
    del top[limit:]


def passes_slot_filter(bits: tuple[int, ...], min_distinct_slots: int, max_per_slot: int) -> bool:
    slots = [bit // 32 for bit in bits]
    counts = Counter(slots)
    if len(counts) < min_distinct_slots:
        return False
    if max_per_slot > 0 and max(counts.values()) > max_per_slot:
        return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--init-W", required=True, help="Comma-separated hex W1[57..60]")
    ap.add_argument("--init-hw", type=int, required=True)
    ap.add_argument("--slots", default="57,58,59,60")
    ap.add_argument("--top-bits", type=int, default=32)
    ap.add_argument("--radii", default="5,6", help="Comma-separated combo radii to test")
    ap.add_argument("--min-distinct-slots", type=int, default=1,
                    help="Require each combo to touch at least this many W slots")
    ap.add_argument("--max-per-slot", type=int, default=0,
                    help="Reject combos with more than this many bits in one W slot; 0 disables")
    ap.add_argument("--top-records", type=int, default=20)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    if args.top_bits < 1:
        raise SystemExit("--top-bits must be >= 1")
    if args.top_records < 1:
        raise SystemExit("--top-records must be >= 1")
    if not 1 <= args.min_distinct_slots <= 4:
        raise SystemExit("--min-distinct-slots must be in 1..4")
    if args.max_per_slot < 0:
        raise SystemExit("--max-per-slot must be >= 0")

    slots = parse_slots(args.slots)
    radii = parse_radii(args.radii)
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
        f"=== ranked_combo_search.py: {short} top_bits={args.top_bits} "
        f"radii={','.join(str(r) for r in radii)} slots W{','.join(str(57 + s) for s in slots)} ==="
    )
    if args.min_distinct_slots > 1 or args.max_per_slot:
        print(
            f"  slot filter: min_distinct_slots={args.min_distinct_slots}, "
            f"max_per_slot={args.max_per_slot or 'none'}"
        )
    t0 = time.time()

    single_bit = []
    accepted_single = []
    for bit in bit_domain:
        w = flip_bits(base_w, (bit,))
        rec = evaluate(s1_init, s2_init, W1_pre, W2_pre, m0, fill, kbit, *w)
        entry = bit_label(bit)
        if rec is None:
            entry.update({"cascade1": False, "bridge": False, "hw_total": None, "score": None})
            single_bit.append(entry)
            continue
        score = bridge_score(rec, kbit)
        entry.update({
            "cascade1": True,
            "bridge": score["score"] is not None,
            "hw_total": rec["hw_total"],
            "score": score["score"],
            "reject_reason": score["reject_reason"],
        })
        single_bit.append(entry)
        if score["score"] is not None:
            accepted_single.append(entry)

    accepted_single.sort(key=lambda e: (e["hw_total"], -e["score"], e["bit_index"]))
    selected = tuple(e["bit_index"] for e in accepted_single[:args.top_bits])
    print("  one-bit accepted:", len(accepted_single), "of", len(bit_domain))
    print("  selected soft bits:", ", ".join(f"W{57 + b // 32}.{b % 32}" for b in selected[:16]))

    counts = {
        "total": 0,
        "skipped_slot_filter": 0,
        "cascade1": 0,
        "bridge": 0,
        "hw_le_init": 0,
        "hw_lt_init": 0,
    }
    by_radius = {}
    best_seen = {
        "hw_total": init_rec["hw_total"],
        "score": init_score,
        "bits": [],
        "W": [f"0x{x:08x}" for x in base_w],
        "record": init_rec,
    }
    top_records = []
    new_records = []

    for radius in radii:
        if radius > len(selected):
            continue
        r_counts = {
            "total": 0,
            "skipped_slot_filter": 0,
            "cascade1": 0,
            "bridge": 0,
            "hw_le_init": 0,
            "hw_lt_init": 0,
        }
        for bits in combinations(selected, radius):
            if not passes_slot_filter(bits, args.min_distinct_slots, args.max_per_slot):
                counts["skipped_slot_filter"] += 1
                r_counts["skipped_slot_filter"] += 1
                continue
            counts["total"] += 1
            r_counts["total"] += 1
            w = flip_bits(base_w, bits)
            rec = evaluate(s1_init, s2_init, W1_pre, W2_pre, m0, fill, kbit, *w)
            if rec is None:
                continue
            counts["cascade1"] += 1
            r_counts["cascade1"] += 1
            score = bridge_score(rec, kbit)
            if score["score"] is None:
                continue
            counts["bridge"] += 1
            r_counts["bridge"] += 1
            hw = rec["hw_total"]
            sc = score["score"]
            entry = record_combo(bits, hw, sc, w, rec)
            keep_top(top_records, entry, args.top_records)
            if hw < best_seen["hw_total"] or (hw == best_seen["hw_total"] and sc > best_seen["score"]):
                best_seen = entry
            if hw <= args.init_hw:
                counts["hw_le_init"] += 1
                r_counts["hw_le_init"] += 1
                new_records.append(entry)
            if hw < args.init_hw:
                counts["hw_lt_init"] += 1
                r_counts["hw_lt_init"] += 1
        by_radius[str(radius)] = r_counts
        print(
            f"  r{radius}: total={r_counts['total']} cascade1={r_counts['cascade1']} "
            f"bridge={r_counts['bridge']} hw<=init={r_counts['hw_le_init']} "
            f"hw<init={r_counts['hw_lt_init']} skipped={r_counts['skipped_slot_filter']}"
        )

    wall = time.time() - t0
    payload = {
        "description": f"{args.label}: ranked combo search" if args.label else "ranked combo search",
        "candidate": short,
        "init_W": [f"0x{x:08x}" for x in base_w],
        "init_hw": args.init_hw,
        "init_score": init_score,
        "slots": [57 + s for s in slots],
        "bit_domain_size": len(bit_domain),
        "top_bits": args.top_bits,
        "radii": list(radii),
        "min_distinct_slots": args.min_distinct_slots,
        "max_per_slot": args.max_per_slot,
        "single_bit_rank": accepted_single,
        "selected_bits": [bit_label(b) for b in selected],
        "counts": counts,
        "by_radius": by_radius,
        "best_seen": best_seen,
        "top_records": top_records,
        "new_records": new_records,
        "wall_seconds": round(wall, 2),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"Total wall: {wall:.1f}s")
    print(f"best seen HW={best_seen['hw_total']} score={best_seen['score']}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
