#!/usr/bin/env python3
"""
verify_from_model.py — bridge a solver model back to the independent oracle.

Rebuilds the exact CNF for a config (to recover free-variable IDs), parses the
saved kissat model (v-lines), reconstructs the free-word assignment for both
messages, and hands it to verify_lever_collision.verify (which shares no schedule
/ round code with the encoder). A SAT model is only a real result if this prints
a verified collision at the claimed sr.

Usage:
  verify_from_model.py <model_file> --m0 0x.. --fill 0x.. --free 54,55,56,57 \
      [--kernel-bit 31] [--tail-start 54] [--claimed-sr 60]
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "encoders"))

from lever_gap_encoder import build_lever_gap_cnf
from verify_lever_collision import verify


def parse_model(path):
    assign = {}
    with open(path) as f:
        for line in f:
            if line.startswith("v "):
                for tok in line[2:].split():
                    v = int(tok)
                    if v != 0:
                        assign[abs(v)] = (v > 0)
    return assign


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--m0", required=True)
    ap.add_argument("--fill", required=True)
    ap.add_argument("--free", required=True)
    ap.add_argument("--kernel-bit", type=int, default=31)
    ap.add_argument("--tail-start", type=int, default=None)
    ap.add_argument("--claimed-sr", type=int, default=None)
    args = ap.parse_args()

    m0 = int(args.m0, 16)
    fill = int(args.fill, 16)
    free = {int(x) for x in args.free.split(",")}

    # Rebuild the CNF to recover the free-variable -> name map (deterministic).
    cnf, summary, _ = build_lever_gap_cnf(
        m0, fill, free, kernel_bit=args.kernel_bit, tail_start=args.tail_start)
    inv = cnf.free_var_names  # var -> "W1_57[3]"

    assign = parse_model(args.model)

    # Reconstruct free words per message.
    free1, free2 = {}, {}
    for var, name in inv.items():
        # name like "W1_57[3]"
        msg_pos, bit = name.split("[")
        bit = int(bit.rstrip("]"))
        msg, pos = msg_pos.split("_")
        pos = int(pos)
        if var not in assign:
            print(f"WARN: free var {var} ({name}) not in model; assuming 0")
        val = assign.get(var, False)
        target = free1 if msg == "W1" else free2
        if val:
            target[pos] = target.get(pos, 0) | (1 << bit)
        else:
            target.setdefault(pos, 0)

    claimed = args.claimed_sr if args.claimed_sr is not None else summary["sr"]
    print(f"Reconstructed free words from model {os.path.basename(args.model)}:")
    for p in sorted(free):
        print(f"  W1[{p}]=0x{free1.get(p,0):08x}  W2[{p}]=0x{free2.get(p,0):08x}")
    print()
    res = verify(m0, fill, args.kernel_bit, free1, free2, claimed_sr=claimed)
    sys.exit(0 if res["collision"] else 1)


if __name__ == "__main__":
    main()
