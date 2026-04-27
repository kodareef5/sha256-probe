#!/usr/bin/env python3
"""
build_certpin.py — append W-witness pinning unit clauses to a base
cascade_aux_expose Mode A CNF.

Reads the base CNF + its varmap.json sidecar. Appends 128 unit clauses
(32 bits × 4 W words [57..60]) that pin W1[57..60] to the user-provided
W-witness values.

Usage:
    python3 build_certpin.py --base BASE_CNF --varmap VARMAP_JSON \
        --w57 0x... --w58 0x... --w59 0x... --w60 0x... --out OUT_CNF
"""
import argparse
import json


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="Base cascade_aux Mode A CNF")
    ap.add_argument("--varmap", required=True, help="Varmap JSON sidecar")
    ap.add_argument("--w57", required=True)
    ap.add_argument("--w58", required=True)
    ap.add_argument("--w59", required=True)
    ap.add_argument("--w60", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--header-comment", default="cert-pin: W1[57..60] pinned to specified witness")
    args = ap.parse_args()

    w_values = {
        "57": int(args.w57, 16),
        "58": int(args.w58, 16),
        "59": int(args.w59, 16),
        "60": int(args.w60, 16),
    }

    varmap = json.load(open(args.varmap))
    aux_W = varmap["aux_W"]

    # Read base CNF
    with open(args.base) as f:
        base_lines = f.readlines()

    # Find the p line and update vars/clauses count
    p_idx = None
    n_vars = n_clauses = None
    for i, line in enumerate(base_lines):
        if line.startswith("p cnf "):
            parts = line.split()
            n_vars = int(parts[2])
            n_clauses = int(parts[3])
            p_idx = i
            break
    if p_idx is None:
        raise RuntimeError(f"No 'p cnf' line in {args.base}")

    # Build pinning unit clauses
    pin_clauses = []
    for slot in ("57", "58", "59", "60"):
        wval = w_values[slot]
        bits = aux_W[slot]
        if len(bits) != 32:
            raise RuntimeError(f"aux_W[{slot}] has {len(bits)} vars, expected 32")
        for i in range(32):
            var = bits[i]
            if (wval >> i) & 1:
                pin_clauses.append(f"{var} 0\n")
            else:
                pin_clauses.append(f"-{var} 0\n")

    # Write output: header comment, updated p line, base body, pin clauses
    new_clauses = n_clauses + len(pin_clauses)
    with open(args.out, "w") as f:
        f.write(f"c {args.header_comment}\n")
        f.write(f"c W1[57]=0x{w_values['57']:08x} W1[58]=0x{w_values['58']:08x} "
                f"W1[59]=0x{w_values['59']:08x} W1[60]=0x{w_values['60']:08x}\n")
        f.write(f"p cnf {n_vars} {new_clauses}\n")
        # Skip the base CNF's first comment + its p-line; write its body
        for i, line in enumerate(base_lines):
            if i == p_idx:
                continue
            if line.startswith("c ") and i < p_idx:
                continue
            f.write(line)
        # Append pin clauses
        for c in pin_clauses:
            f.write(c)
    print(f"Wrote {args.out}: {n_vars} vars, {new_clauses} clauses (+ {len(pin_clauses)} unit pins)")


if __name__ == "__main__":
    main()
