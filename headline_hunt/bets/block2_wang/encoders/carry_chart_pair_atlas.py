#!/usr/bin/env python3
"""Build a pair-delta atlas over the final carry/residual chart.

For each two-bit W57..W60 move, record how the HW vector
[a,b,c,d,e,f,g,h] changes. This is not a search first; it asks whether
local moves can repair specific register lanes, and what compensation they
force into the other lanes.
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
from ranked_combo_search import bit_label

REGS = ["a", "b", "c", "d", "e", "f", "g", "h"]


def pair_bits(bits: tuple[int, int]) -> list[dict]:
    return [bit_label(b) for b in bits]


def trim_top(items: list[dict], key, limit: int) -> list[dict]:
    return sorted(items, key=key)[:limit]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--init-W", required=True)
    ap.add_argument("--init-hw", type=int, required=True)
    ap.add_argument("--slots", default="57,58,59,60")
    ap.add_argument("--top", type=int, default=20)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()

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

    print(f"=== carry_chart_pair_atlas.py: {short} pairs over W{','.join(str(57 + s) for s in slots)} ===")
    t0 = time.time()
    counts = {"total": 0, "cascade1": 0, "bridge": 0}
    entries = []
    base_hw63 = init_rec["hw63"]

    for bits in combinations(bit_domain, 2):
        counts["total"] += 1
        w = flip_bits(base_w, bits)
        rec = evaluate(s1_init, s2_init, W1_pre, W2_pre, m0, fill, kbit, *w)
        if rec is None:
            continue
        counts["cascade1"] += 1
        score = bridge_score(rec, kbit)
        if score["score"] is None:
            continue
        counts["bridge"] += 1
        delta = [rec["hw63"][i] - base_hw63[i] for i in range(8)]
        repairs = [max(0, -d) for d in delta]
        damage = [max(0, d) for d in delta]
        entries.append({
            "bits": pair_bits(bits),
            "hw_total": rec["hw_total"],
            "score": score["score"],
            "hw63": rec["hw63"],
            "delta_hw63": delta,
            "total_repair": sum(repairs),
            "total_damage": sum(damage),
            "net_delta": rec["hw_total"] - args.init_hw,
            "W": [f"0x{x:08x}" for x in w],
        })

    best_by_hw = trim_top(entries, lambda e: (e["hw_total"], -e["score"]), args.top)
    best_by_repair = trim_top(entries, lambda e: (-e["total_repair"], e["net_delta"], -e["score"]), args.top)
    per_reg = {}
    for idx, reg in enumerate(REGS):
        per_reg[reg] = trim_top(
            [e for e in entries if e["delta_hw63"][idx] < 0],
            lambda e, i=idx: (e["delta_hw63"][i], e["net_delta"], -e["score"]),
            args.top,
        )

    wall = time.time() - t0
    payload = {
        "description": f"{args.label}: carry-chart pair atlas" if args.label else "carry-chart pair atlas",
        "candidate": short,
        "init_W": [f"0x{x:08x}" for x in base_w],
        "init_hw": args.init_hw,
        "init_score": init_score,
        "init_hw63": base_hw63,
        "slots": [57 + s for s in slots],
        "counts": counts,
        "best_by_hw": best_by_hw,
        "best_by_total_repair": best_by_repair,
        "per_register_repairs": per_reg,
        "wall_seconds": round(wall, 2),
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"  accepted pairs: {counts['bridge']}/{counts['total']}")
    print(f"  best HW pair: {best_by_hw[0]['hw_total']} delta={best_by_hw[0]['net_delta']}")
    print(f"  best repair pair: repair={best_by_repair[0]['total_repair']} net_delta={best_by_repair[0]['net_delta']}")
    print(f"Total wall: {wall:.1f}s")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
