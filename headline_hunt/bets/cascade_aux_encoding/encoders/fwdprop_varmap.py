#!/usr/bin/env python3
"""
fwdprop_varmap.py — bridge the current cascade_aux encoder to the (older)
q5_alternative_attacks/forward_propagator.cpp varmap format.

forward_propagator.cpp watches the 8 free schedule words and expects a varmap
with keys "W1_57".."W1_60","W2_57".."W2_60", each a 32-int array of SAT var IDs.
The current encoder's sidecar uses a different schema (aux_reg/aux_W/actual_p*),
so the propagator could never be wired up (per the reopen-candidate memo). This
adapter recovers the free-word var IDs from CNFBuilder.free_var_names and emits
exactly the format forward_propagator parses, alongside the matching CNF.

Only valid for sr=60 (n_free=4 -> 8 free words). Usage:
    python3 fwdprop_varmap.py --m0 0x17149975 --fill 0xffffffff \
        --kernel-bit 31 --mode expose --out-cnf X.cnf --out-varmap X.varmap.json
"""
import argparse
import json
import re
import sys

from cascade_aux_encoder import build_cascade_aux_cnf, write_dimacs_with_header


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m0", required=True)
    ap.add_argument("--fill", required=True)
    ap.add_argument("--kernel-bit", type=int, default=31)
    ap.add_argument("--mode", choices=["expose", "force"], default="expose")
    ap.add_argument("--out-cnf", required=True)
    ap.add_argument("--out-varmap", required=True)
    args = ap.parse_args()

    m0 = int(args.m0, 16)
    fill = int(args.fill, 16)

    cnf, summary, *_ = build_cascade_aux_cnf(60, m0, fill, args.kernel_bit, args.mode)
    n_vars, n_clauses = write_dimacs_with_header(cnf, summary, args.out_cnf)

    # Invert free_var_names: name "W1_57[3]" -> var id, grouped by word.
    pat = re.compile(r"^(W[12]_\d+)\[(\d+)\]$")
    words = {}
    for var, name in cnf.free_var_names.items():
        m = pat.match(name)
        if not m:
            continue
        word, bit = m.group(1), int(m.group(2))
        words.setdefault(word, {})[bit] = var

    expected = [f"W1_{57+i}" for i in range(4)] + [f"W2_{57+i}" for i in range(4)]
    out = {}
    for w in expected:
        if w not in words or len(words[w]) != 32:
            print(f"ERROR: word {w} missing or not 32 bits "
                  f"(got {len(words.get(w, {}))})", file=sys.stderr)
            sys.exit(2)
        out[w] = [words[w][b] for b in range(32)]

    with open(args.out_varmap, "w") as f:
        json.dump(out, f)
    print(f"Wrote {args.out_cnf}: {n_vars} vars, {n_clauses} clauses")
    print(f"Wrote {args.out_varmap}: 8 free words "
          f"(W1_57..60, W2_57..60), 32 bits each")


if __name__ == "__main__":
    main()
