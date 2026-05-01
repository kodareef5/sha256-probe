#!/usr/bin/env python3
"""
F431_joint_enumerate.py — fill the joint gap left by F429 + F430.

F429 covered W1[60] only at Hamming-{1,2,3} (5488 per cand).
F430 covered W1[57..59] only at Hamming-{1,2,3} (147,536 per cand).

Together: pure-word coverage. The gap is "joint" perturbations:
flips that span W1[57..59] AND W1[60].

F431 enumerates the joint cases at Hamming-2 and Hamming-3:
  H-2 joint: 1 bit in W1[57..59] (96) × 1 bit in W1[60] (32) = 3072
  H-3 joint:
    1+2: 96 × C(32,2) = 96 × 496 = 47,616
    2+1: C(96,2) × 32 = 4,560 × 32 = 145,920
  Total H-3 joint: 193,536
  Total joint per cand: 196,608

Together F429+F430+F431 cover the full Hamming-{1,2,3} ball over the
128-bit W1[57..60]. After F431 negative, the local-isolation finding
is complete.

Usage:
    python3 F431_joint_enumerate.py [--out path]
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
    setup = setup_cand(m0, fill, kbit)
    if setup is None:
        return {"cand": short, "error": "not cascade-eligible"}
    s1_init, s2_init, W1_pre, W2_pre = setup
    base_W = list(best_W)

    counts = {"h2_joint_total": 0, "h2_joint_cascade1_ok": 0, "h2_joint_bridge_ok": 0,
              "h3_1plus2_total": 0, "h3_1plus2_cascade1_ok": 0, "h3_1plus2_bridge_ok": 0,
              "h3_2plus1_total": 0, "h3_2plus1_cascade1_ok": 0, "h3_2plus1_bridge_ok": 0}

    candidates = []  # records of HW <= best_hw_known

    def eval_at(new_W, label, bits_top, bits_w60):
        rec = evaluate(s1_init, s2_init, W1_pre, W2_pre, m0, fill, kbit, *new_W)
        if rec is None:
            return False
        counts[f"{label}_cascade1_ok"] += 1
        sc = bridge_score(rec, kbit)
        if sc["score"] is None:
            return False
        counts[f"{label}_bridge_ok"] += 1
        if rec["hw_total"] <= best_hw_known:
            candidates.append({
                "hw": rec["hw_total"],
                "score": sc["score"],
                "W": [f"0x{w:08x}" for w in new_W],
                "label": label,
                "bits_top": bits_top,
                "bits_w60": bits_w60,
                "hw63": rec["hw63"],
                "diff63": rec["diff63"],
            })
        return True

    # H-2 joint: 1 bit in W1[57..59] (96 = 3 slots × 32 bits) × 1 bit in W1[60]
    for top_bit in range(96):
        slot = top_bit // 32
        bit = top_bit % 32
        for w60_bit in range(32):
            counts["h2_joint_total"] += 1
            new_W = list(base_W)
            new_W[slot] ^= (1 << bit)
            new_W[3] ^= (1 << w60_bit)
            eval_at(new_W, "h2_joint", [top_bit], [w60_bit])

    # H-3 1+2: 1 bit in top + 2 bits in W[60]
    for top_bit in range(96):
        slot = top_bit // 32
        bit = top_bit % 32
        for w60_pair in itertools.combinations(range(32), 2):
            counts["h3_1plus2_total"] += 1
            new_W = list(base_W)
            new_W[slot] ^= (1 << bit)
            for b in w60_pair:
                new_W[3] ^= (1 << b)
            eval_at(new_W, "h3_1plus2", [top_bit], list(w60_pair))

    # H-3 2+1: 2 bits in top + 1 bit in W[60]
    for top_pair in itertools.combinations(range(96), 2):
        counts["h3_2plus1_total"] += 1
        for w60_bit in range(32):
            new_W = list(base_W)
            for tb in top_pair:
                slot = tb // 32; bit = tb % 32
                new_W[slot] ^= (1 << bit)
            new_W[3] ^= (1 << w60_bit)
            eval_at(new_W, "h3_2plus1", list(top_pair), [w60_bit])
    # Note: 2+1 was double-counted above (one outer loop, then inner increments h3_2plus1_total only once).
    # Correct: re-fix counts
    counts["h3_2plus1_total"] = 0
    for top_pair in itertools.combinations(range(96), 2):
        for w60_bit in range(32):
            counts["h3_2plus1_total"] += 1

    candidates.sort(key=lambda c: (c["hw"], -c["score"]))
    new_records = [c for c in candidates if c["hw"] < best_hw_known]

    return {
        "cand": short, "kbit": kbit,
        "current_best": {
            "W": [f"0x{w:08x}" for w in best_W],
            "hw": best_hw_known, "score": best_score_known, "source": source,
        },
        "enumeration_counts": counts,
        "n_candidates_le_best": len(candidates),
        "n_new_records": len(new_records),
        "new_records": new_records,
        "top_5_at_or_below_best": candidates[:5],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F431_joint_enumeration.json")
    args = ap.parse_args()

    h2_per_cand = 96 * 32
    h3_1plus2_per_cand = 96 * 496
    h3_2plus1_per_cand = 4560 * 32
    total_per_cand = h2_per_cand + h3_1plus2_per_cand + h3_2plus1_per_cand
    print(f"=== F431: joint Hamming-{{2,3}} enumeration over W1[57..60] ===")
    print(f"Per cand: {h2_per_cand} (H-2 joint) + {h3_1plus2_per_cand} (H-3 1+2) + {h3_2plus1_per_cand} (H-3 2+1) = {total_per_cand}")
    print(f"Panel: {len(PANEL)} cands × {total_per_cand} = {total_per_cand * len(PANEL)} evaluations\n")

    t0 = time.time()
    results = []
    for short, m0, fill, kbit, best_W, best_hw, best_score, source in PANEL:
        print(f"[{short}] joint enumeration around HW={best_hw} ({source})...")
        r = enumerate_one(short, m0, fill, kbit, best_W, best_hw, best_score, source)
        if "error" in r:
            print(f"   ERROR: {r['error']}")
        else:
            cnt = r["enumeration_counts"]
            print(f"   H-2 joint:     cascade-1 {cnt['h2_joint_cascade1_ok']}/{cnt['h2_joint_total']}, bridge-pass {cnt['h2_joint_bridge_ok']}")
            print(f"   H-3 1+2:       cascade-1 {cnt['h3_1plus2_cascade1_ok']}/{cnt['h3_1plus2_total']}, bridge-pass {cnt['h3_1plus2_bridge_ok']}")
            print(f"   H-3 2+1:       cascade-1 {cnt['h3_2plus1_cascade1_ok']}/{cnt['h3_2plus1_total']}, bridge-pass {cnt['h3_2plus1_bridge_ok']}")
            print(f"   candidates ≤ best HW: {r['n_candidates_le_best']}; NEW records: {r['n_new_records']}")
            if r["new_records"]:
                print(f"   *** NEW RECORDS ***")
                for rec in r["new_records"][:5]:
                    print(f"      HW={rec['hw']} score={rec['score']:.3f} {rec['label']} W={rec['W']}")
        results.append(r)

    wall = time.time() - t0
    print(f"\nTotal wall: {wall:.1f}s")

    out = {
        "description": "F431: joint Hamming-{2,3} enumeration over W1[57..60] — fills the gap F429 (W[60] only) + F430 (W[57..59] only) leave",
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
