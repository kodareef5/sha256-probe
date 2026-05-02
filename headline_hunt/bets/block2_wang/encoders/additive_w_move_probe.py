#!/usr/bin/env python3
"""Probe modular add/sub moves on W57..W60 witnesses.

Most Path C local tools flip XOR bits in W57..W60. F127 showed that modular
additive common-mode moves can expose structure that XOR-local probes miss in
the absorber setting. This script lifts that idea to the late schedule words:
apply W[word] +=/-= 2^bit moves, evaluate the actual carried result, and rank
the resulting residuals.
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
from enumerate_hamming_ball import parse_w, parse_slots, find_cand
from ranked_combo_search import keep_top

MASK = 0xFFFFFFFF


def move_label(move: tuple[int, int, int]) -> dict:
    slot, bit, sign = move
    return {
        "slot": 57 + slot,
        "bit": bit,
        "sign": "+" if sign > 0 else "-",
        "delta": f"{'-' if sign < 0 else ''}0x{(1 << bit):08x}",
    }


def apply_moves(base_w: tuple[int, int, int, int], moves: tuple[tuple[int, int, int], ...]) -> tuple[int, int, int, int]:
    out = list(base_w)
    for slot, bit, sign in moves:
        out[slot] = (out[slot] + sign * (1 << bit)) & MASK
    return tuple(out)


def xor_delta_bits(base_w: tuple[int, int, int, int], w: tuple[int, int, int, int]) -> int:
    return sum(((old ^ new) & MASK).bit_count() for old, new in zip(base_w, w))


def record_moves(
    moves: tuple[tuple[int, int, int], ...],
    init_hw63: list[int],
    hw: int,
    score: float,
    w: tuple[int, int, int, int],
    base_w: tuple[int, int, int, int],
    rec: dict,
) -> dict:
    return {
        "moves": [move_label(move) for move in moves],
        "terms": len(moves),
        "xor_delta_bits": xor_delta_bits(base_w, w),
        "hw_total": hw,
        "score": score,
        "W": [f"0x{x:08x}" for x in w],
        "record": rec,
        "delta_hw63": [rec["hw63"][i] - init_hw63[i] for i in range(8)],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--init-W", required=True)
    ap.add_argument("--init-hw", type=int, required=True)
    ap.add_argument("--slots", default="57,58,59,60")
    ap.add_argument("--max-terms", type=int, default=2)
    ap.add_argument("--top-records", type=int, default=40)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    if args.max_terms < 1:
        raise SystemExit("--max-terms must be >= 1")
    if args.top_records < 1:
        raise SystemExit("--top-records must be >= 1")

    slots = parse_slots(args.slots)
    moves = tuple((slot, bit, sign) for slot in slots for bit in range(32) for sign in (1, -1))

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
        f"=== additive_w_move_probe.py: {short} max_terms={args.max_terms} "
        f"over W{','.join(str(57 + s) for s in slots)} ==="
    )
    t0 = time.time()
    counts = {
        "total": 0,
        "skipped_duplicate_w": 0,
        "cascade1": 0,
        "bridge": 0,
        "hw_le_init": 0,
        "hw_lt_init": 0,
    }
    by_terms = {}
    seen_w = {base_w}
    top_records = []
    new_records = []
    best_seen = {
        "moves": [],
        "terms": 0,
        "xor_delta_bits": 0,
        "hw_total": init_rec["hw_total"],
        "score": init_score,
        "W": [f"0x{x:08x}" for x in base_w],
        "record": init_rec,
        "delta_hw63": [0] * 8,
    }

    for term_count in range(1, args.max_terms + 1):
        term_counts = {
            "total": 0,
            "skipped_duplicate_w": 0,
            "cascade1": 0,
            "bridge": 0,
            "hw_le_init": 0,
            "hw_lt_init": 0,
        }
        for combo in combinations(moves, term_count):
            counts["total"] += 1
            term_counts["total"] += 1
            w = apply_moves(base_w, combo)
            if w in seen_w:
                counts["skipped_duplicate_w"] += 1
                term_counts["skipped_duplicate_w"] += 1
                continue
            seen_w.add(w)
            rec = evaluate(s1_init, s2_init, W1_pre, W2_pre, m0, fill, kbit, *w)
            if rec is None:
                continue
            counts["cascade1"] += 1
            term_counts["cascade1"] += 1
            score = bridge_score(rec, kbit)
            if score["score"] is None:
                continue
            counts["bridge"] += 1
            term_counts["bridge"] += 1
            entry = record_moves(combo, init_rec["hw63"], rec["hw_total"], score["score"], w, base_w, rec)
            keep_top(top_records, entry, args.top_records)
            if rec["hw_total"] < best_seen["hw_total"] or (
                rec["hw_total"] == best_seen["hw_total"] and score["score"] > best_seen["score"]
            ):
                best_seen = entry
            if rec["hw_total"] <= args.init_hw:
                counts["hw_le_init"] += 1
                term_counts["hw_le_init"] += 1
                new_records.append(entry)
            if rec["hw_total"] < args.init_hw:
                counts["hw_lt_init"] += 1
                term_counts["hw_lt_init"] += 1
        by_terms[str(term_count)] = term_counts
        print(
            f"  terms {term_count}: total={term_counts['total']} "
            f"cascade1={term_counts['cascade1']} bridge={term_counts['bridge']} "
            f"hw<=init={term_counts['hw_le_init']} hw<init={term_counts['hw_lt_init']} "
            f"dupe={term_counts['skipped_duplicate_w']}"
        )

    wall = time.time() - t0
    payload = {
        "description": f"{args.label}: additive W move probe" if args.label else "additive W move probe",
        "candidate": short,
        "init_W": [f"0x{x:08x}" for x in base_w],
        "init_hw": args.init_hw,
        "init_score": init_score,
        "init_hw63": init_rec["hw63"],
        "slots": [57 + s for s in slots],
        "max_terms": args.max_terms,
        "move_count": len(moves),
        "counts": counts,
        "by_terms": by_terms,
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
