#!/usr/bin/env python3
"""
F430_w57_59_enumerate.py — symmetric counterpart to F429.

F429 enumerated the full Hamming-{1,2,3} neighborhood of W1[60] only
(W57/58/59 fixed) and found no new records. F430 does the symmetric
experiment: enumerate W1[57..59] Hamming-{1,2,3} with W1[60] fixed at
the current best per cand.

Test: does deeper HW exist via varying W1[57..59]? If yes, the W[60]
dominance pattern is misleading and W57/58/59 also have unmined
basins. If no, current bests are full-W1[57..60]-locally-optimal at
Hamming radius 3 (within bridge_score / cascade-1 fences).

Usage:
    python3 F430_w57_59_enumerate.py [--out path] [--max-radius 3]

Output: same structure as F429.
"""
import argparse
import itertools
import json
import os
import sys
import time

sys.path.insert(0, "/Users/mac/Desktop/sha256_review")
sys.path.insert(0, "/Users/mac/Desktop/sha256_review/headline_hunt/bets/block2_wang/encoders")
from lib.sha256 import MASK
from block2_bridge_beam import setup_cand, evaluate
from bridge_score import bridge_score


PANEL = [
    ("bit3_m33ec77ca",   0x33ec77ca, 0xffffffff,  3,
     (0xba476635, 0x8cf9982c, 0x0699c787, 0x8893274d), 51, 71.551, "F408"),
    ("bit2_ma896ee41",   0xa896ee41, 0xffffffff,  2,
     (0x504e056e, 0x3e435e29, 0xda594ea2, 0xe37c8fe1), 51, 71.551, "F408"),
    ("bit24_mdc27e18c",  0xdc27e18c, 0xffffffff, 24,
     (0x4be5074f, 0x429efff2, 0xe09458af, 0xe6560e70), 43, 79.073, "F428"),
    ("bit28_md1acca79",  0xd1acca79, 0xffffffff, 28,
     (0x307cf0e7, 0x853d504a, 0x78f16a5e, 0x41fc6a74), 45, 74.146, "F408"),
]


def enumerate_one(short, m0, fill, kbit, best_W, best_hw_known, best_score_known, source, max_radius):
    """Enumerate all r-bit flips of W1[57..59] (96 bits), W1[60] fixed.
    For each: cascade-1 + bridge_score evaluation."""
    setup = setup_cand(m0, fill, kbit)
    if setup is None:
        return {"cand": short, "error": "not cascade-eligible"}
    s1_init, s2_init, W1_pre, W2_pre = setup
    base_W = list(best_W)

    counts = {}
    for r in range(1, max_radius + 1):
        counts[f"r{r}_total"] = 0
        counts[f"r{r}_cascade1_ok"] = 0
        counts[f"r{r}_bridge_ok"] = 0

    candidates = []  # records of HW <= best_hw_known
    # 96 bits across slots 0,1,2 (W1[57], W1[58], W1[59]); W1[60] = slot 3 fixed.
    for radius in range(1, max_radius + 1):
        for bit_combo in itertools.combinations(range(96), radius):
            counts[f"r{radius}_total"] += 1
            new_W = list(base_W)
            for b in bit_combo:
                slot = b // 32
                bit = b % 32
                new_W[slot] ^= (1 << bit)
            rec = evaluate(s1_init, s2_init, W1_pre, W2_pre, m0, fill, kbit, *new_W)
            if rec is None:
                continue
            counts[f"r{radius}_cascade1_ok"] += 1
            sc = bridge_score(rec, kbit)
            if sc["score"] is None:
                continue
            counts[f"r{radius}_bridge_ok"] += 1
            # Keep candidates that match or improve current best
            if rec["hw_total"] <= best_hw_known:
                candidates.append({
                    "hw": rec["hw_total"],
                    "score": sc["score"],
                    "W": [f"0x{w:08x}" for w in new_W],
                    "radius": radius,
                    "bits_flipped": list(bit_combo),
                    "hw63": rec["hw63"],
                    "diff63": rec["diff63"],
                })

    candidates.sort(key=lambda c: (c["hw"], -c["score"]))

    new_records = [c for c in candidates if c["hw"] < best_hw_known]
    return {
        "cand": short, "kbit": kbit,
        "current_best": {
            "W": [f"0x{w:08x}" for w in best_W],
            "hw": best_hw_known, "score": best_score_known, "source": source,
        },
        "max_radius": max_radius,
        "enumeration_counts": counts,
        "n_candidates_le_best": len(candidates),
        "n_new_records": len(new_records),
        "new_records": new_records,
        "top_5_at_or_below_best": candidates[:5],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-radius", type=int, default=3,
                    help="Max Hamming radius (default 3). Note: r=3 over 96 bits = 142880 combos per cand.")
    ap.add_argument("--out", default="headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F430_w57_59_enumeration.json")
    args = ap.parse_args()

    print(f"=== F430: W1[57..59] Hamming-{{1..{args.max_radius}}} enumeration (W1[60] fixed) ===")
    total_per_cand = sum(
        len(list(itertools.combinations(range(96), r))) for r in range(1, args.max_radius + 1)
    )
    print(f"Panel: {len(PANEL)} cands × ~{total_per_cand} W candidates = ~{total_per_cand * len(PANEL)} evaluations\n")

    t0 = time.time()
    results = []
    for short, m0, fill, kbit, best_W, best_hw, best_score, source in PANEL:
        print(f"[{short}] enumerating W1[57..59] neighbors (current best HW={best_hw}, source={source})...")
        r = enumerate_one(short, m0, fill, kbit, best_W, best_hw, best_score, source, args.max_radius)
        if "error" in r:
            print(f"   ERROR: {r['error']}")
        else:
            cnt = r["enumeration_counts"]
            for radius in range(1, args.max_radius + 1):
                tot = cnt[f"r{radius}_total"]
                c1 = cnt[f"r{radius}_cascade1_ok"]
                br = cnt[f"r{radius}_bridge_ok"]
                print(f"   r{radius}: cascade-1 {c1}/{tot}; bridge-pass {br}")
            print(f"   candidates ≤ best HW: {r['n_candidates_le_best']}; NEW records: {r['n_new_records']}")
            if r["new_records"]:
                print(f"   *** NEW RECORDS ***")
                for rec in r["new_records"][:5]:
                    print(f"      HW={rec['hw']} score={rec['score']:.3f} radius={rec['radius']} W={rec['W']}")
            elif r["top_5_at_or_below_best"]:
                tops = r["top_5_at_or_below_best"][:3]
                print(f"   top tied-at-best: ", end="")
                print(", ".join(f"HW={c['hw']} (r{c['radius']})" for c in tops))
        results.append(r)

    wall = time.time() - t0
    print(f"\nTotal wall: {wall:.1f}s")

    out = {
        "description": f"F430: exhaustive W1[57..59] Hamming-{{1..{args.max_radius}}} enumeration around current best, W1[60] fixed",
        "panel": [{"cand": p[0], "kbit": p[3], "init_W": [f"0x{w:08x}" for w in p[4]],
                   "init_hw": p[5], "init_score": p[6], "source": p[7]} for p in PANEL],
        "max_radius": args.max_radius,
        "wall_seconds": round(wall, 2),
        "results": results,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
