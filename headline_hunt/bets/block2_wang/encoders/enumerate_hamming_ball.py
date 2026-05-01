#!/usr/bin/env python3
"""Enumerate a Hamming ball around a W1[57..60] witness.

This is the general version of the F429/F430/F431/F433 one-off
enumerators. It checks all bit flips up to a requested radius over the
selected W vector slots, evaluates cascade-1, applies bridge_score as a
filter, and records whether any neighbor ties or improves the input HW.
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


def parse_slots(slots: str) -> tuple[int, ...]:
    """Parse W slot selectors.

    Accepts either local slot numbers 0..3 or SHA schedule words 57..60.
    Output is always local slot numbers into W1[57..60].
    """
    parsed = []
    for raw in slots.split(","):
        raw = raw.strip()
        if not raw:
            continue
        val = int(raw, 10)
        if 57 <= val <= 60:
            val -= 57
        if not 0 <= val <= 3:
            raise ValueError("--slots entries must be 0..3 or 57..60")
        parsed.append(val)
    if not parsed:
        raise ValueError("--slots must select at least one W slot")
    return tuple(dict.fromkeys(parsed))


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
    ap.add_argument(
        "--slots",
        default="57,58,59,60",
        help="Comma-separated W slots to enumerate. Accepts 57..60 or local 0..3; default all.",
    )
    ap.add_argument(
        "--relax-bridge",
        action="store_true",
        help="Count cascade-valid records even when bridge_score rejects them.",
    )
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    args = ap.parse_args()

    if args.max_radius < 1:
        raise SystemExit("--max-radius must be >= 1")
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

    counts = {
        "total": 0,
        "cascade1": 0,
        "bridge": 0,
        "bridge_reject": 0,
        "hw_le_init": 0,
        "hw_lt_init": 0,
    }
    by_radius = {}
    new_records = []
    best_seen = {
        "hw_total": init_rec["hw_total"],
        "score": bridge_score(init_rec, kbit)["score"],
        "bridge_pass": True,
        "reject_reason": None,
        "bits": [],
        "W": [f"0x{x:08x}" for x in base_w],
        "record": init_rec,
    }

    print(
        f"=== enumerate_hamming_ball.py: {short} radius<= {args.max_radius} "
        f"around HW={args.init_hw}; slots W{','.join(str(57 + s) for s in slots)} ==="
    )
    if args.relax_bridge:
        print("    bridge relaxed: HW ties/improvements count even if bridge_score rejects")
    t0 = time.time()
    for radius in range(1, args.max_radius + 1):
        r_counts = {
            "total": 0,
            "cascade1": 0,
            "bridge": 0,
            "bridge_reject": 0,
            "hw_le_init": 0,
            "hw_lt_init": 0,
        }
        for bits in combinations(bit_domain, radius):
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
                counts["bridge_reject"] += 1
                r_counts["bridge_reject"] += 1
                if not args.relax_bridge:
                    continue
            else:
                counts["bridge"] += 1
                r_counts["bridge"] += 1
            hw = rec["hw_total"]
            rank_score = score["score"] if score["score"] is not None else -1e9
            best_rank_score = best_seen["score"] if best_seen["score"] is not None else -1e9
            if hw < best_seen["hw_total"] or (hw == best_seen["hw_total"] and rank_score > best_rank_score):
                best_seen = {
                    "hw_total": hw,
                    "score": score["score"],
                    "bridge_pass": score["score"] is not None,
                    "reject_reason": score["reject_reason"],
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
                    "bridge_pass": score["score"] is not None,
                    "reject_reason": score["reject_reason"],
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
            f"bridge={r_counts['bridge']} bridge_reject={r_counts['bridge_reject']} "
            f"hw<=init={r_counts['hw_le_init']} "
            f"hw<init={r_counts['hw_lt_init']}"
        )

    wall = time.time() - t0
    payload = {
        "description": f"{args.label}: Hamming ball enumeration" if args.label else "Hamming ball enumeration",
        "candidate": short,
        "init_W": [f"0x{x:08x}" for x in base_w],
        "init_hw": args.init_hw,
        "max_radius": args.max_radius,
        "slots": [57 + s for s in slots],
        "bit_domain_size": len(bit_domain),
        "relax_bridge": args.relax_bridge,
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
