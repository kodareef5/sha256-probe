#!/usr/bin/env python3
"""Enumerate a Hamming ball around a W1[57..60] witness.

This is the general version of the F429/F430/F431/F433 one-off
enumerators. It checks all bit flips up to a requested radius over the
128-bit W vector, evaluates cascade-1, applies bridge_score as a filter,
and records whether any neighbor ties or improves the input HW.
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

from block2_bridge_beam import CANDS, setup_cand, evaluate
from bridge_score import bridge_score


def parse_w(words: str) -> tuple[int, int, int, int]:
    parts = [p.strip() for p in words.split(",")]
    if len(parts) != 4:
        raise ValueError("--init-W must contain exactly 4 comma-separated words")
    return tuple(int(p, 16) & 0xFFFFFFFF for p in parts)


def flip_bits(base_w: tuple[int, int, int, int], bits: tuple[int, ...]) -> tuple[int, int, int, int]:
    out = list(base_w)
    for idx in bits:
        slot = idx // 32
        bit = idx % 32
        out[slot] ^= 1 << bit
    return tuple(out)


def find_cand(short: str) -> tuple[str, int, int, int]:
    for cand in CANDS:
        if cand[0] == short:
            return cand
    raise ValueError(f"unknown candidate: {short}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidate", required=True, help="Candidate short name, e.g. bit13_m916a56aa")
    ap.add_argument("--init-W", required=True, help="Comma-separated hex W1[57..60]")
    ap.add_argument("--init-hw", type=int, required=True, help="HW of the input witness")
    ap.add_argument("--max-radius", type=int, default=3)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    if args.max_radius < 1:
        raise SystemExit("--max-radius must be >= 1")

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

    counts = {
        "total": 0,
        "cascade1": 0,
        "bridge": 0,
        "hw_le_init": 0,
        "hw_lt_init": 0,
    }
    by_radius = {}
    new_records = []
    best_seen = {
        "hw_total": init_rec["hw_total"],
        "score": bridge_score(init_rec, kbit)["score"],
        "bits": [],
        "W": [f"0x{x:08x}" for x in base_w],
        "record": init_rec,
    }

    print(
        f"=== enumerate_hamming_ball.py: {short} radius<= {args.max_radius} "
        f"around HW={args.init_hw} ==="
    )
    t0 = time.time()
    for radius in range(1, args.max_radius + 1):
        r_counts = {"total": 0, "cascade1": 0, "bridge": 0, "hw_le_init": 0, "hw_lt_init": 0}
        for bits in combinations(range(128), radius):
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
            if hw < best_seen["hw_total"] or (
                hw == best_seen["hw_total"] and score["score"] > best_seen["score"]
            ):
                best_seen = {
                    "hw_total": hw,
                    "score": score["score"],
                    "bits": list(bits),
                    "W": [f"0x{x:08x}" for x in w],
                    "record": rec,
                }
            if hw <= args.init_hw:
                counts["hw_le_init"] += 1
                r_counts["hw_le_init"] += 1
                entry = {
                    "radius": radius,
                    "bits": list(bits),
                    "hw_total": hw,
                    "score": score["score"],
                    "W": [f"0x{x:08x}" for x in w],
                    "record": rec,
                }
                new_records.append(entry)
            if hw < args.init_hw:
                counts["hw_lt_init"] += 1
                r_counts["hw_lt_init"] += 1
        by_radius[str(radius)] = r_counts
        print(
            f"  r{radius}: total={r_counts['total']} cascade1={r_counts['cascade1']} "
            f"bridge={r_counts['bridge']} hw<=init={r_counts['hw_le_init']} "
            f"hw<init={r_counts['hw_lt_init']}"
        )

    wall = time.time() - t0
    payload = {
        "description": f"{args.label}: Hamming ball enumeration" if args.label else "Hamming ball enumeration",
        "candidate": short,
        "init_W": [f"0x{x:08x}" for x in base_w],
        "init_hw": args.init_hw,
        "max_radius": args.max_radius,
        "counts": counts,
        "by_radius": by_radius,
        "best_seen": best_seen,
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
