#!/usr/bin/env python3
"""Prior-weighted W-slot sampler for Path C residual basins.

F552 showed recurring W60 bit positions across several candidate families,
but no reusable full W60 masks. This tool treats those recurring bit positions
as soft sampling weights and lets the remaining bits vary candidate by
candidate. It defaults to W60-only for backward compatibility, but can sample
joint W59/W60 domains via --slots 59,60.
"""

import argparse
import json
from pathlib import Path
import random
import sys
import time
from typing import Any

REPO = Path(__file__).resolve().parents[4]
ENCODERS = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(ENCODERS))

from block2_bridge_beam import setup_cand, evaluate
from bridge_score import bridge_score
from enumerate_hamming_ball import parse_w, parse_slots, find_cand, flip_bits
from ranked_combo_search import record_combo, keep_top


DEFAULT_PRIORS = {
    30: 6.0,
    27: 4.5,
    29: 4.5,
    31: 4.5,
    16: 4.0,
    19: 4.0,
    21: 4.0,
    3: 4.0,
    13: 3.0,
    14: 3.0,
    15: 3.0,
    12: 3.0,
    2: 3.0,
    25: 3.0,
    28: 3.0,
}


def local_idx(slot: int, bit: int) -> int:
    return (slot - 57) * 32 + bit


def parse_weights(raw: str, slots: tuple[int, ...]) -> dict[int, float]:
    if not raw:
        weights = {}
        if 3 in slots:
            weights.update({local_idx(60, bit): weight for bit, weight in DEFAULT_PRIORS.items()})
        if 2 in slots:
            weights[local_idx(59, 21)] = 3.0
        return weights
    weights: dict[int, float] = {}
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        fields = part.split(":")
        if len(fields) == 3:
            slot = int(fields[0], 10)
            bit = int(fields[1], 10)
            weight = float(fields[2])
        elif len(fields) == 2:
            slot = 60
            bit_raw, weight_raw = fields
            bit = int(bit_raw, 10)
            weight = float(weight_raw)
        elif len(fields) == 1:
            slot = 60
            bit = int(fields[0], 10)
            weight = 3.0
        else:
            raise ValueError(f"bad weight spec: {part}")
        if not 57 <= slot <= 60:
            raise ValueError(f"W slot out of range: {slot}")
        if not 0 <= bit < 32:
            raise ValueError(f"W bit out of range: {bit}")
        if weight <= 0:
            raise ValueError(f"weight must be positive for W{slot}:b{bit}")
        weights[local_idx(slot, bit)] = weight
    return weights


def parse_flip_counts(raw: str) -> list[int]:
    counts = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo_raw, hi_raw = part.split("-", 1)
            lo = int(lo_raw)
            hi = int(hi_raw)
            counts.extend(range(lo, hi + 1))
        else:
            counts.append(int(part))
    out = sorted({count for count in counts if 1 <= count <= 32})
    if not out:
        raise ValueError("--flip-counts must include at least one count in 1..32")
    return out


def weighted_sample_without_replacement(
    rng: random.Random,
    domain: list[int],
    weights: dict[int, float],
    k: int,
) -> tuple[int, ...]:
    available = list(domain)
    chosen = []
    for _ in range(min(k, len(domain))):
        total = sum(weights.get(bit, 1.0) for bit in available)
        pick = rng.random() * total
        acc = 0.0
        for idx, bit in enumerate(available):
            acc += weights.get(bit, 1.0)
            if acc >= pick:
                chosen.append(bit)
                del available[idx]
                break
    return tuple(sorted(chosen))


def label_local(idx: int) -> str:
    return f"W{57 + idx // 32}:b{idx % 32}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--init-W", required=True)
    ap.add_argument("--init-hw", type=int, required=True)
    ap.add_argument("--iterations", type=int, default=200_000)
    ap.add_argument("--seed", type=int, default=20260502)
    ap.add_argument("--slots", default="60", help="W slots to sample: 60 or 59,60")
    ap.add_argument("--flip-counts", default="7-14")
    ap.add_argument(
        "--weights",
        default="",
        help="optional weights: bit:weight means W60:bit:weight; slot:bit:weight supports W59",
    )
    ap.add_argument("--top-records", type=int, default=40)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    if args.iterations < 1:
        raise SystemExit("--iterations must be >= 1")

    short, m0, fill, kbit = find_cand(args.candidate)
    setup = setup_cand(m0, fill, kbit)
    if setup is None:
        raise SystemExit(f"{short} is not cascade-eligible")
    s1_init, s2_init, W1_pre, W2_pre = setup
    base_w = parse_w(args.init_W)
    slots = parse_slots(args.slots)
    domain = [slot * 32 + bit for slot in slots for bit in range(32)]
    weights = parse_weights(args.weights, slots)
    flip_counts = parse_flip_counts(args.flip_counts)
    rng = random.Random(args.seed)

    init_rec = evaluate(s1_init, s2_init, W1_pre, W2_pre, m0, fill, kbit, *base_w)
    if init_rec is None:
        raise SystemExit("init-W violates cascade-1")
    if init_rec["hw_total"] != args.init_hw:
        raise SystemExit(f"init-HW mismatch: argument {args.init_hw}, evaluated {init_rec['hw_total']}")
    init_score = bridge_score(init_rec, kbit)["score"]
    if init_score is None:
        raise SystemExit("init-W fails bridge selector")

    print(
        f"=== prior_weighted_w60_search.py: {short} iters={args.iterations} "
        f"slots={args.slots} flip_counts={args.flip_counts} seed={args.seed} ==="
    )
    t0 = time.time()
    counts = {
        "total": 0,
        "duplicate": 0,
        "cascade1": 0,
        "bridge": 0,
        "hw_le_init": 0,
        "hw_lt_init": 0,
    }
    seen = set()
    top_records: list[dict[str, Any]] = []
    new_records: list[dict[str, Any]] = []
    best_seen = {
        "hw_total": init_rec["hw_total"],
        "score": init_score,
        "bits": [],
        "W": [f"0x{x:08x}" for x in base_w],
        "record": init_rec,
    }

    for _ in range(args.iterations):
        k = rng.choice(flip_counts)
        local_bits = weighted_sample_without_replacement(rng, domain, weights, k)
        if local_bits in seen:
            counts["duplicate"] += 1
            continue
        seen.add(local_bits)
        counts["total"] += 1
        w = flip_bits(base_w, local_bits)
        rec = evaluate(s1_init, s2_init, W1_pre, W2_pre, m0, fill, kbit, *w)
        if rec is None:
            continue
        counts["cascade1"] += 1
        score = bridge_score(rec, kbit)
        if score["score"] is None:
            continue
        counts["bridge"] += 1
        out_entry = record_combo(local_bits, rec["hw_total"], score["score"], w, rec)
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

    wall = time.time() - t0
    payload = {
        "description": f"{args.label}: prior-weighted W60 search" if args.label else "prior-weighted W60 search",
        "candidate": short,
        "init_W": [f"0x{x:08x}" for x in base_w],
        "init_hw": args.init_hw,
        "init_score": init_score,
        "init_hw63": init_rec["hw63"],
        "slots": [57 + slot for slot in slots],
        "iterations": args.iterations,
        "seed": args.seed,
        "flip_counts": flip_counts,
        "weights": {label_local(bit): weight for bit, weight in sorted(weights.items())},
        "counts": counts,
        "best_seen": best_seen,
        "top_records": top_records,
        "new_records": new_records[: args.top_records],
        "wall_seconds": round(wall, 2),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Total wall: {wall:.1f}s")
    print(f"best seen HW={best_seen['hw_total']} score={best_seen['score']}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
