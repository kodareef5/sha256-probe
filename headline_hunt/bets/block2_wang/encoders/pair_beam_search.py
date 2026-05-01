#!/usr/bin/env python3
"""Beam search over composed two-bit W moves.

This is a compensation-aware alternative to exhaustive pair-combo pilots.
It builds a pool of strong exact two-bit deltas, then composes them one at a
time, evaluating the actual W state after each addition. Beam ranking can
penalize specified register-lane damage such as c/g.
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

REG_INDEX = {"a": 0, "b": 1, "c": 2, "d": 3, "e": 4, "f": 5, "g": 6, "h": 7}


def parse_regs(raw: str) -> tuple[int, ...]:
    if not raw:
        return ()
    out = []
    for part in raw.split(","):
        reg = part.strip().lower()
        if not reg:
            continue
        if reg not in REG_INDEX:
            raise ValueError(f"unknown register: {reg}")
        out.append(REG_INDEX[reg])
    return tuple(dict.fromkeys(out))


def pair_entry(bits: tuple[int, int], rec: dict, score: float, init_hw: int, init_hw63: list[int]) -> dict:
    delta = [rec["hw63"][i] - init_hw63[i] for i in range(8)]
    return {
        "bits": [bit_label(b) for b in bits],
        "bit_indices": list(bits),
        "hw_total": rec["hw_total"],
        "score": score,
        "hw63": rec["hw63"],
        "delta_hw63": delta,
        "net_delta": rec["hw_total"] - init_hw,
        "total_repair": sum(max(0, -d) for d in delta),
        "total_damage": sum(max(0, d) for d in delta),
    }


def state_objective(rec: dict, score: float, init_hw63: list[int], penalty_regs: tuple[int, ...], penalty_weight: float) -> float:
    delta = [rec["hw63"][i] - init_hw63[i] for i in range(8)]
    penalty = sum(max(0, delta[i]) for i in penalty_regs)
    return rec["hw_total"] + penalty_weight * penalty - 0.001 * score


def pair_objective(entry: dict, penalty_regs: tuple[int, ...], penalty_weight: float) -> float:
    penalty = sum(max(0, entry["delta_hw63"][i]) for i in penalty_regs)
    return entry["hw_total"] + penalty_weight * penalty - 0.001 * entry["score"]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--init-W", required=True)
    ap.add_argument("--init-hw", type=int, required=True)
    ap.add_argument("--slots", default="57,58,59,60")
    ap.add_argument("--pair-pool", type=int, default=192)
    ap.add_argument("--pair-rank", choices=["hw", "repair", "objective"], default="hw")
    ap.add_argument("--max-pairs", type=int, default=4)
    ap.add_argument("--beam-width", type=int, default=128)
    ap.add_argument("--max-radius", type=int, default=8)
    ap.add_argument("--penalty-regs", default="c,g")
    ap.add_argument("--penalty-weight", type=float, default=2.0)
    ap.add_argument("--top-records", type=int, default=20)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    if args.pair_pool < 1 or args.max_pairs < 1 or args.beam_width < 1:
        raise SystemExit("pair-pool, max-pairs, and beam-width must be >= 1")

    slots = parse_slots(args.slots)
    bit_domain = tuple(slot * 32 + bit for slot in slots for bit in range(32))
    penalty_regs = parse_regs(args.penalty_regs)

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
        f"=== pair_beam_search.py: {short} pool={args.pair_pool} "
        f"beam={args.beam_width} max_pairs={args.max_pairs} max_radius={args.max_radius} ==="
    )
    t0 = time.time()

    pair_counts = {"total": 0, "cascade1": 0, "bridge": 0}
    pairs = []
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
        pairs.append(pair_entry(bits, rec, score["score"], args.init_hw, init_rec["hw63"]))

    if args.pair_rank == "hw":
        pairs.sort(key=lambda e: (e["hw_total"], -e["score"], e["bit_indices"]))
    elif args.pair_rank == "objective":
        pairs.sort(key=lambda e: (pair_objective(e, penalty_regs, args.penalty_weight), e["hw_total"], -e["score"], e["bit_indices"]))
    else:
        pairs.sort(key=lambda e: (-e["total_repair"], e["net_delta"], -e["score"], e["bit_indices"]))
    pool = pairs[:args.pair_pool]

    counts = {
        "expanded": 0,
        "skipped_radius": 0,
        "skipped_duplicate": 0,
        "cascade1": 0,
        "bridge": 0,
        "hw_le_init": 0,
        "hw_lt_init": 0,
    }
    top_records = []
    new_records = []
    best_seen = {
        "hw_total": init_rec["hw_total"],
        "score": init_score,
        "bits": [],
        "W": [f"0x{x:08x}" for x in base_w],
        "record": init_rec,
    }

    beam = [{"bits": tuple(), "objective": args.init_hw, "hw_total": args.init_hw, "score": init_score}]
    seen_by_depth = [set() for _ in range(args.max_pairs + 1)]
    depth_summaries = []

    for depth in range(1, args.max_pairs + 1):
        expanded = []
        for state in beam:
            for pair in pool:
                bits = tuple(sorted(set(state["bits"]) | set(pair["bit_indices"])))
                if len(bits) > args.max_radius:
                    counts["skipped_radius"] += 1
                    continue
                if bits in seen_by_depth[depth]:
                    counts["skipped_duplicate"] += 1
                    continue
                seen_by_depth[depth].add(bits)
                counts["expanded"] += 1
                w = flip_bits(base_w, bits)
                rec = evaluate(s1_init, s2_init, W1_pre, W2_pre, m0, fill, kbit, *w)
                if rec is None:
                    continue
                counts["cascade1"] += 1
                score = bridge_score(rec, kbit)
                if score["score"] is None:
                    continue
                counts["bridge"] += 1
                obj = state_objective(rec, score["score"], init_rec["hw63"], penalty_regs, args.penalty_weight)
                entry = {
                    "bits": bits,
                    "objective": round(obj, 6),
                    "hw_total": rec["hw_total"],
                    "score": score["score"],
                    "record": rec,
                    "W": [f"0x{x:08x}" for x in w],
                }
                expanded.append(entry)
                out_entry = record_combo(bits, rec["hw_total"], score["score"], w, rec)
                out_entry["objective"] = round(obj, 6)
                keep_top(top_records, out_entry, args.top_records)
                if rec["hw_total"] < best_seen["hw_total"] or (
                    rec["hw_total"] == best_seen["hw_total"] and score["score"] > best_seen["score"]
                ):
                    best_seen = out_entry
                if rec["hw_total"] <= args.init_hw:
                    counts["hw_le_init"] += 1
                    new_records.append(out_entry)
                if rec["hw_total"] < args.init_hw:
                    counts["hw_lt_init"] += 1

        expanded.sort(key=lambda e: (e["objective"], e["hw_total"], -e["score"], e["bits"]))
        beam = expanded[:args.beam_width]
        best_depth = beam[0] if beam else None
        depth_summaries.append({
            "depth": depth,
            "kept": len(beam),
            "best_objective": best_depth["objective"] if best_depth else None,
            "best_hw": best_depth["hw_total"] if best_depth else None,
            "best_score": best_depth["score"] if best_depth else None,
        })
        print(
            f"  depth {depth}: kept={len(beam)} "
            f"best_hw={best_depth['hw_total'] if best_depth else 'n/a'} "
            f"best_obj={best_depth['objective'] if best_depth else 'n/a'}"
        )
        if not beam:
            break

    wall = time.time() - t0
    payload = {
        "description": f"{args.label}: pair beam search" if args.label else "pair beam search",
        "candidate": short,
        "init_W": [f"0x{x:08x}" for x in base_w],
        "init_hw": args.init_hw,
        "init_score": init_score,
        "init_hw63": init_rec["hw63"],
        "slots": [57 + s for s in slots],
        "pair_pool": args.pair_pool,
        "pair_rank": args.pair_rank,
        "max_pairs": args.max_pairs,
        "beam_width": args.beam_width,
        "max_radius": args.max_radius,
        "penalty_regs": args.penalty_regs,
        "penalty_weight": args.penalty_weight,
        "pair_counts": pair_counts,
        "counts": counts,
        "depth_summaries": depth_summaries,
        "selected_pairs": pool,
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
