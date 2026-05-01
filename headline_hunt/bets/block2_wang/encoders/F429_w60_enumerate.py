#!/usr/bin/env python3
"""
F429_w60_enumerate.py — exhaustive W1[60] Hamming-neighborhood enumeration.

Motivation: F408 (wide anneal), F427 (bit28 seeded refine), and F428
(bit3/bit2/bit24 seeded refine) all show that block-2 residual
breakthroughs are small W1[60] perturbations. W57/W58/W59 stay at the
greedy/wide-search optimum. This script tests the hypothesis directly
by enumerating the full {1, 2, 3}-bit Hamming neighborhood of W1[60]
for each cand's current best W vector.

Output: per-cand best HW across all neighborhoods, plus the full
enumeration record for analysis. No SAT solver runs.

Usage:
    python3 F429_w60_enumerate.py [--out path]
"""
import argparse
import itertools
import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
ENCODERS = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(ENCODERS))
from lib.sha256 import MASK
from block2_bridge_beam import setup_cand, evaluate
from bridge_score import bridge_score


# Current best W vectors per cand (post F408 + F427/F428 seeded refines)
# format: (short, m0, fill, kbit, current_best_W, current_best_hw, current_best_score, source)
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


def enumerate_one(short, m0, fill, kbit, best_W, best_hw_known, best_score_known, source):
    """For one cand, enumerate all 1-, 2-, 3-bit flips of W1[60] only;
    evaluate cascade-1 + bridge_score. Return summary + records of any
    HW <= best_hw_known."""
    setup = setup_cand(m0, fill, kbit)
    if setup is None:
        return {"cand": short, "error": "not cascade-eligible"}
    s1_init, s2_init, W1_pre, W2_pre = setup

    best_W = list(best_W)  # mutable
    base_w60 = best_W[3]

    counts = {"r1_total": 0, "r1_cascade1_ok": 0, "r1_bridge_ok": 0,
              "r2_total": 0, "r2_cascade1_ok": 0, "r2_bridge_ok": 0,
              "r3_total": 0, "r3_cascade1_ok": 0, "r3_bridge_ok": 0}
    candidates = []  # (HW, score, w60, radius)

    for radius in (1, 2, 3):
        for bit_combo in itertools.combinations(range(32), radius):
            counts[f"r{radius}_total"] += 1
            mask = 0
            for b in bit_combo:
                mask |= (1 << b)
            new_w60 = (base_w60 ^ mask) & MASK
            rec = evaluate(s1_init, s2_init, W1_pre, W2_pre, m0, fill, kbit,
                           best_W[0], best_W[1], best_W[2], new_w60)
            if rec is None:
                continue
            counts[f"r{radius}_cascade1_ok"] += 1
            sc = bridge_score(rec, kbit)
            if sc["score"] is None:
                continue
            counts[f"r{radius}_bridge_ok"] += 1
            candidates.append({
                "hw": rec["hw_total"],
                "score": sc["score"],
                "w60": f"0x{new_w60:08x}",
                "radius": radius,
                "bits_flipped": list(bit_combo),
                "hw63": rec["hw63"],
                "diff63": rec["diff63"],
            })

    # Sort by HW (ascending), then by score (descending)
    candidates.sort(key=lambda c: (c["hw"], -c["score"]))

    # Top results
    top = candidates[:20]

    # Best HW found
    best_hw = candidates[0]["hw"] if candidates else None
    best_score_in_set = max(c["score"] for c in candidates) if candidates else None
    new_records = [c for c in candidates if c["hw"] < best_hw_known]

    return {
        "cand": short, "kbit": kbit,
        "current_best": {
            "W": [f"0x{w:08x}" for w in best_W],
            "hw": best_hw_known, "score": best_score_known, "source": source,
        },
        "enumeration_counts": counts,
        "best_hw_found": best_hw,
        "best_score_found": best_score_in_set,
        "n_new_records": len(new_records),
        "new_records": new_records,
        "top_20_by_hw": top,
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F429_w60_enumeration.json")
    args = ap.parse_args()

    print("=== F429: W1[60] Hamming-neighborhood enumeration ===")
    print(f"Panel: {len(PANEL)} cands, radii {{1,2,3}}, expected ~{32 + 496 + 4960} W1[60] candidates per cand\n")

    t0 = time.time()
    results = []
    for short, m0, fill, kbit, best_W, best_hw, best_score, source in PANEL:
        print(f"[{short}] enumerating W1[60] neighbors of 0x{best_W[3]:08x} (current best HW={best_hw}, source={source})...")
        r = enumerate_one(short, m0, fill, kbit, best_W, best_hw, best_score, source)
        if "error" in r:
            print(f"   ERROR: {r['error']}")
        else:
            cnt = r["enumeration_counts"]
            print(f"   r1: {cnt['r1_cascade1_ok']}/{cnt['r1_total']} cascade-1; {cnt['r1_bridge_ok']} bridge-pass")
            print(f"   r2: {cnt['r2_cascade1_ok']}/{cnt['r2_total']} cascade-1; {cnt['r2_bridge_ok']} bridge-pass")
            print(f"   r3: {cnt['r3_cascade1_ok']}/{cnt['r3_total']} cascade-1; {cnt['r3_bridge_ok']} bridge-pass")
            print(f"   best HW found: {r['best_hw_found']}  (current best: {best_hw}; new records: {r['n_new_records']})")
            print(f"   best score found: {r['best_score_found']}")
            if r["new_records"]:
                print(f"   *** NEW RECORDS ***")
                for rec in r["new_records"][:5]:
                    print(f"      HW={rec['hw']} score={rec['score']:.3f} w60={rec['w60']} radius={rec['radius']} bits={rec['bits_flipped']}")
        results.append(r)

    wall = time.time() - t0
    print(f"\nTotal wall: {wall:.1f}s")

    out = {
        "description": "F429: exhaustive W1[60] Hamming-{1,2,3} enumeration around current best per cand",
        "panel": [{"cand": p[0], "kbit": p[3], "init_W": [f"0x{w:08x}" for w in p[4]],
                   "init_hw": p[5], "init_score": p[6], "source": p[7]} for p in PANEL],
        "wall_seconds": round(wall, 2),
        "results": results,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(out, f, indent=2)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
