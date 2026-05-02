#!/usr/bin/env python3
"""Multi-objective beam search over composed two-bit W moves.

The scalar pair beam tends to collapse onto one local notion of "best."
This variant deliberately keeps several frontier types alive at each depth:
low total HW, c/g relief, lane balance, target-shape distance, bridge score,
and explicit repair. The intent is to find compensating compositions that a
single sorted beam would prune before their payoffs become visible.
"""

import argparse
from collections import Counter
from itertools import combinations
import json
from math import ceil
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
from pair_beam_search import parse_regs, pair_entry
from ranked_combo_search import keep_top, record_combo

REG_NAMES = ("a", "b", "c", "d", "e", "f", "g", "h")
DEFAULT_OBJECTIVES = ("hw", "cg", "balance", "target", "score", "repair")
ALLOWED_OBJECTIVES = set(DEFAULT_OBJECTIVES) | {"novel"}


def parse_objectives(raw: str) -> tuple[str, ...]:
    names = []
    for part in raw.split(","):
        name = part.strip().lower()
        if not name:
            continue
        if name not in ALLOWED_OBJECTIVES:
            raise ValueError(f"unknown objective: {name}")
        names.append(name)
    if not names:
        raise ValueError("--objectives must contain at least one objective")
    return tuple(dict.fromkeys(names))


def parse_target_hw63(raw: str | None, init_hw63: list[int], target_relief: int) -> list[int]:
    if raw:
        parts = [int(p.strip(), 10) for p in raw.split(",") if p.strip()]
        if len(parts) != 8:
            raise ValueError("--target-hw63 must contain exactly 8 integers")
        if any(p < 0 for p in parts):
            raise ValueError("--target-hw63 values must be non-negative")
        return parts

    target = list(init_hw63)
    for idx in (2, 6):
        target[idx] = max(0, target[idx] - target_relief)
    return target


def lane_delta(hw63: list[int], init_hw63: list[int]) -> list[int]:
    return [hw63[i] - init_hw63[i] for i in range(8)]


def repair_damage(delta: list[int]) -> tuple[int, int]:
    repair = sum(max(0, -d) for d in delta)
    damage = sum(max(0, d) for d in delta)
    return repair, damage


def balance_l1(hw63: list[int]) -> float:
    mean = sum(hw63) / len(hw63)
    return sum(abs(x - mean) for x in hw63)


def target_distance(hw63: list[int], target_hw63: list[int], target_regs: tuple[int, ...]) -> float:
    total = 0.0
    for idx, (actual, target) in enumerate(zip(hw63, target_hw63)):
        weight = 2.0 if idx in target_regs else 1.0
        total += weight * abs(actual - target)
    return total


def score_state(
    rec: dict,
    score: float,
    init_hw63: list[int],
    target_hw63: list[int],
    target_regs: tuple[int, ...],
    cg_weight: float,
    balance_weight: float,
    target_weight: float,
    score_weight: float,
    repair_weight: float,
    damage_weight: float,
) -> dict[str, float]:
    hw63 = rec["hw63"]
    delta = lane_delta(hw63, init_hw63)
    repair, damage = repair_damage(delta)
    cg_pressure = sum(hw63[i] for i in target_regs)
    return {
        "hw": round(rec["hw_total"] - 0.001 * score, 6),
        "cg": round(rec["hw_total"] + cg_weight * cg_pressure - 0.001 * score, 6),
        "balance": round(rec["hw_total"] + balance_weight * balance_l1(hw63) - 0.001 * score, 6),
        "target": round(
            target_weight * target_distance(hw63, target_hw63, target_regs)
            + 0.1 * rec["hw_total"]
            - 0.001 * score,
            6,
        ),
        "score": round(0.25 * rec["hw_total"] - score_weight * score, 6),
        "repair": round(rec["hw_total"] - repair_weight * repair + damage_weight * damage - 0.001 * score, 6),
    }


def pair_rank_key(name: str, entry: dict, target_hw63: list[int], target_regs: tuple[int, ...]) -> tuple:
    hw63 = entry["hw63"]
    score = entry["score"]
    if name == "hw":
        return (entry["hw_total"], -score, entry["bit_indices"])
    if name == "cg":
        return (sum(hw63[i] for i in target_regs), entry["hw_total"], -score, entry["bit_indices"])
    if name == "balance":
        return (balance_l1(hw63), entry["hw_total"], -score, entry["bit_indices"])
    if name == "target":
        return (target_distance(hw63, target_hw63, target_regs), entry["hw_total"], -score, entry["bit_indices"])
    if name == "score":
        return (-score, entry["hw_total"], entry["bit_indices"])
    if name == "repair":
        return (-entry["total_repair"], entry["net_delta"], -score, entry["bit_indices"])
    if name == "novel":
        return (tuple(hw63), entry["hw_total"], -score, entry["bit_indices"])
    raise ValueError(name)


def select_pair_pool(
    pairs: list[dict],
    pair_pool: int,
    rank_sources: tuple[str, ...],
    target_hw63: list[int],
    target_regs: tuple[int, ...],
) -> tuple[list[dict], dict[str, int]]:
    ranked = {
        name: sorted(pairs, key=lambda e, n=name: pair_rank_key(n, e, target_hw63, target_regs))
        for name in rank_sources
    }
    selected = []
    selected_bits = set()
    source_counts = Counter()
    offsets = {name: 0 for name in rank_sources}

    while len(selected) < pair_pool:
        changed = False
        for name in rank_sources:
            entries = ranked[name]
            while offsets[name] < len(entries):
                entry = entries[offsets[name]]
                offsets[name] += 1
                key = tuple(entry["bit_indices"])
                if key in selected_bits:
                    continue
                selected_bits.add(key)
                selected.append(entry)
                source_counts[name] += 1
                changed = True
                break
            if len(selected) >= pair_pool:
                break
        if not changed:
            break
    return selected, dict(source_counts)


def state_sort_key(name: str, entry: dict, bucket_counts: Counter) -> tuple:
    if name == "novel":
        return (
            bucket_counts[entry["hw63_tuple"]],
            entry["hw_total"],
            -entry["score"],
            entry["bits"],
        )
    return (
        entry["objective_scores"][name],
        entry["hw_total"],
        -entry["score"],
        entry["bits"],
    )


def select_beam(expanded: list[dict], objectives: tuple[str, ...], beam_width: int, per_objective: int) -> list[dict]:
    bucket_counts = Counter(e["hw63_tuple"] for e in expanded)
    selected = []
    selected_bits = set()

    for name in objectives:
        ranked = sorted(expanded, key=lambda e, n=name: state_sort_key(n, e, bucket_counts))
        for entry in ranked:
            if entry["bits"] in selected_bits:
                continue
            entry["selected_by"] = name
            selected.append(entry)
            selected_bits.add(entry["bits"])
            if sum(1 for e in selected if e["selected_by"] == name) >= per_objective:
                break

    selected_buckets = {entry["hw63_tuple"] for entry in selected}
    global_rank = sorted(expanded, key=lambda e: (e["hw_total"], -e["score"], e["bits"]))
    for entry in global_rank:
        if len(selected) >= beam_width:
            break
        if entry["bits"] in selected_bits:
            continue
        if entry["hw63_tuple"] in selected_buckets:
            continue
        entry["selected_by"] = "shape_fill"
        selected.append(entry)
        selected_bits.add(entry["bits"])
        selected_buckets.add(entry["hw63_tuple"])

    for entry in global_rank:
        if len(selected) >= beam_width:
            break
        if entry["bits"] in selected_bits:
            continue
        entry["selected_by"] = "global_fill"
        selected.append(entry)
        selected_bits.add(entry["bits"])

    return selected[:beam_width]


def summarize_objective_best(beam: list[dict], objectives: tuple[str, ...]) -> dict[str, dict]:
    out = {}
    if not beam:
        return out
    bucket_counts = Counter(e["hw63_tuple"] for e in beam)
    for name in objectives:
        best = min(beam, key=lambda e, n=name: state_sort_key(n, e, bucket_counts))
        out[name] = {
            "objective": best["objective_scores"].get(name),
            "hw_total": best["hw_total"],
            "score": best["score"],
            "hw63": list(best["hw63_tuple"]),
            "bits": best["bits"],
        }
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--init-W", required=True)
    ap.add_argument("--init-hw", type=int, required=True)
    ap.add_argument("--slots", default="57,58,59,60")
    ap.add_argument("--pair-pool", type=int, default=384)
    ap.add_argument("--pair-rank-sources", default="hw,cg,balance,target,score,repair")
    ap.add_argument("--max-pairs", type=int, default=4)
    ap.add_argument("--beam-width", type=int, default=256)
    ap.add_argument("--per-objective", type=int, default=0)
    ap.add_argument("--max-radius", type=int, default=8)
    ap.add_argument("--objectives", default=",".join(DEFAULT_OBJECTIVES))
    ap.add_argument("--target-regs", default="c,g")
    ap.add_argument("--target-relief", type=int, default=2)
    ap.add_argument("--target-hw63", default=None, help="Optional comma-separated a,b,c,d,e,f,g,h target vector")
    ap.add_argument("--cg-weight", type=float, default=1.5)
    ap.add_argument("--balance-weight", type=float, default=0.35)
    ap.add_argument("--target-weight", type=float, default=1.0)
    ap.add_argument("--score-weight", type=float, default=0.01)
    ap.add_argument("--repair-weight", type=float, default=1.0)
    ap.add_argument("--damage-weight", type=float, default=0.5)
    ap.add_argument("--top-records", type=int, default=20)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    if args.pair_pool < 1 or args.max_pairs < 1 or args.beam_width < 1:
        raise SystemExit("pair-pool, max-pairs, and beam-width must be >= 1")
    if args.max_radius < 1:
        raise SystemExit("--max-radius must be >= 1")
    if args.target_relief < 0:
        raise SystemExit("--target-relief must be >= 0")
    if args.per_objective < 0:
        raise SystemExit("--per-objective must be >= 0")

    slots = parse_slots(args.slots)
    bit_domain = tuple(slot * 32 + bit for slot in slots for bit in range(32))
    objectives = parse_objectives(args.objectives)
    rank_sources = parse_objectives(args.pair_rank_sources)
    target_regs = parse_regs(args.target_regs)
    if not target_regs:
        raise SystemExit("--target-regs must contain at least one register")
    per_objective = args.per_objective or max(1, ceil(args.beam_width / max(1, len(objectives) * 2)))

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
    target_hw63 = parse_target_hw63(args.target_hw63, init_rec["hw63"], args.target_relief)
    init_objective_scores = score_state(
        init_rec,
        init_score,
        init_rec["hw63"],
        target_hw63,
        target_regs,
        args.cg_weight,
        args.balance_weight,
        args.target_weight,
        args.score_weight,
        args.repair_weight,
        args.damage_weight,
    )

    print(
        f"=== multi_objective_pair_beam.py: {short} pool={args.pair_pool} "
        f"beam={args.beam_width} max_pairs={args.max_pairs} max_radius={args.max_radius} ==="
    )
    print(
        "  objectives="
        + ",".join(objectives)
        + f" per_objective={per_objective} target={target_hw63}"
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

    pool, pair_pool_sources = select_pair_pool(pairs, args.pair_pool, rank_sources, target_hw63, target_regs)

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
    best_seen = record_combo(tuple(), init_rec["hw_total"], init_score, base_w, init_rec)
    best_seen["objective_scores"] = init_objective_scores

    beam = [{
        "bits": tuple(),
        "objective_scores": init_objective_scores,
        "hw_total": args.init_hw,
        "score": init_score,
        "hw63_tuple": tuple(init_rec["hw63"]),
        "selected_by": "init",
    }]
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
                objective_scores = score_state(
                    rec,
                    score["score"],
                    init_rec["hw63"],
                    target_hw63,
                    target_regs,
                    args.cg_weight,
                    args.balance_weight,
                    args.target_weight,
                    args.score_weight,
                    args.repair_weight,
                    args.damage_weight,
                )
                entry = {
                    "bits": bits,
                    "objective_scores": objective_scores,
                    "hw_total": rec["hw_total"],
                    "score": score["score"],
                    "record": rec,
                    "W": [f"0x{x:08x}" for x in w],
                    "hw63_tuple": tuple(rec["hw63"]),
                    "selected_by": "",
                }
                expanded.append(entry)

                out_entry = record_combo(bits, rec["hw_total"], score["score"], w, rec)
                out_entry["objective_scores"] = objective_scores
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

        beam = select_beam(expanded, objectives, args.beam_width, per_objective)
        best_depth = min(beam, key=lambda e: (e["hw_total"], -e["score"], e["bits"])) if beam else None
        selected_by = Counter(e["selected_by"] for e in beam)
        depth_summaries.append({
            "depth": depth,
            "expanded": len(expanded),
            "kept": len(beam),
            "best_hw": best_depth["hw_total"] if best_depth else None,
            "best_score": best_depth["score"] if best_depth else None,
            "best_hw63": list(best_depth["hw63_tuple"]) if best_depth else None,
            "selected_by": dict(selected_by),
            "objective_best": summarize_objective_best(beam, objectives),
        })
        print(
            f"  depth {depth}: expanded={len(expanded)} kept={len(beam)} "
            f"best_hw={best_depth['hw_total'] if best_depth else 'n/a'} "
            f"best_score={best_depth['score'] if best_depth else 'n/a'}"
        )
        if not beam:
            break

    wall = time.time() - t0
    payload = {
        "description": f"{args.label}: multi-objective pair beam search" if args.label else "multi-objective pair beam search",
        "candidate": short,
        "init_W": [f"0x{x:08x}" for x in base_w],
        "init_hw": args.init_hw,
        "init_score": init_score,
        "init_hw63": init_rec["hw63"],
        "target_hw63": target_hw63,
        "target_regs": [REG_NAMES[i] for i in target_regs],
        "slots": [57 + s for s in slots],
        "pair_pool": args.pair_pool,
        "pair_rank_sources": list(rank_sources),
        "pair_pool_sources": pair_pool_sources,
        "max_pairs": args.max_pairs,
        "beam_width": args.beam_width,
        "per_objective": per_objective,
        "max_radius": args.max_radius,
        "objectives": list(objectives),
        "weights": {
            "cg_weight": args.cg_weight,
            "balance_weight": args.balance_weight,
            "target_weight": args.target_weight,
            "score_weight": args.score_weight,
            "repair_weight": args.repair_weight,
            "damage_weight": args.damage_weight,
        },
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
