#!/usr/bin/env python3
"""
bridge_preflight_extended.py — Phase 2D pre-injection clause emitter.

Per F387/F388 (cascade_aux_encoding bet, 2026-05-01): the cascade-aux
CDCL proof contains a 31-rung Tseitin XOR ladder iff the cand satisfies
the F387 rule:

    ladder iff (m0_bit[31] = 1) OR (fill_bit[31] = 1 AND fill_HW > 1)

This tool implements the deterministic class-decision and emits the
appropriate clause set per cand:

  Class A (per F387 rule, 51 of 67 registry cands = 76%):
    F343 baseline (2 clauses: dW57[0] unit + W57[22:23] pair)
    + F384 ladder (31 size-3 Tseitin XOR triples + 8 size-2 equivalences)

  Class B (16 of 67 cands):
    F343 baseline only

For Class A cands: we mine the ladder from a one-shot cadical 30s LRAT
proof (since the var IDs depend on the encoder's allocation). Once
mined, the ladder spec is reusable for the same cand.

Usage:
    python3 bridge_preflight_extended.py \
        --cnf path/to/aux_force_sr60_n32_*.cnf \
        --varmap path/to/varmap.json \
        --out clauses.json

Output: JSON spec with:
  - cand: (m0, fill, kbit)
  - class_decision: "A" or "B"
  - class_decision_reason: "Path 1 (m0 bit-31)" / "Path 2 (fill rich)" / "Class B"
  - F343_clauses: [unit + pair, always]
  - F384_ladder_clauses: [size-3 + size-2, only if Class A]
  - total_clauses: count
  - mining_wall_seconds: cadical wall (only if Class A; 0 for B)

The output JSON can be ingested by an IPASIR-UP propagator's
cb_add_external_clause hook at solver init.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from collections import defaultdict


# -----------------------------------------------------------------------------
# F387 class decision (anchored at n=16)
# -----------------------------------------------------------------------------

def f387_class_decision(m0: int, fill: int) -> tuple[str, str]:
    """Returns (class_label, reason). Class label is "A" or "B"."""
    m0_b31 = (m0 >> 31) & 1
    fill_b31 = (fill >> 31) & 1
    fill_hw = bin(fill).count("1")

    if m0_b31 == 1:
        return ("A", f"Path 1 (m0_bit[31]=1; m0=0x{m0:08x})")
    if fill_b31 == 1 and fill_hw > 1:
        return ("A", f"Path 2 (fill_bit[31]=1 AND fill_HW={fill_hw}>1; fill=0x{fill:08x})")
    return ("B", f"both paths fail (m0_b31={m0_b31}, fill_b31={fill_b31}, fill_HW={fill_hw})")


# -----------------------------------------------------------------------------
# F343 baseline clause mining (delegates to preflight_clause_miner.py)
# -----------------------------------------------------------------------------

def mine_f343_baseline(cnf, varmap):
    """Run F343 preflight_clause_miner.py on (cnf, varmap). Returns
    (units, pairs) — lists of injectable clauses as int-literal lists."""
    here = os.path.dirname(os.path.abspath(__file__))
    miner = os.path.join(here, "preflight_clause_miner.py")
    if not os.path.exists(miner):
        return [], [], "preflight_clause_miner.py not found"

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        out_path = f.name

    try:
        r = subprocess.run([
            "python3", miner,
            "--cnf", cnf, "--varmap", varmap,
            "--budget", "5",
            "--rounds", "57",
            "--out", out_path,
        ], capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            return [], [], f"preflight failed: {r.stderr[:200]}"
        spec = json.load(open(out_path))
        units = []
        pairs = []
        for u in spec.get("unit_clauses", []):
            units.append([u["inject_unit"]])
        for p in spec.get("pair_clauses", []):
            pairs.append(p["inject_pair"])
        return units, pairs, None
    finally:
        try: os.unlink(out_path)
        except OSError: pass


# -----------------------------------------------------------------------------
# F384 ladder mining (one-shot cadical 30s LRAT proof + classifier extraction)
# -----------------------------------------------------------------------------

XOR_EVEN = {(1,1,0), (1,0,1), (0,1,1), (0,0,0)}


def parse_drat_proof(path, max_lines=5_000_000):
    """Parse cadical's --binary=false LRAT/DRAT proof. Returns list of
    (var_triple, polarity_set) for size-3 derived clauses."""
    triples = defaultdict(set)
    with open(path) as f:
        for i, line in enumerate(f):
            if i > max_lines: break
            if line.startswith("d "): continue
            toks = line.split()
            try: zero_idx = toks.index("0")
            except ValueError: continue
            lits = [int(t) for t in toks[:zero_idx]]
            if len(lits) != 3: continue
            ls = sorted(lits, key=abs)
            vs = tuple(abs(l) for l in ls)
            sgns = tuple(1 if l > 0 else 0 for l in ls)
            triples[vs].add(sgns)
    return [(t, p) for t, p in triples.items() if p == XOR_EVEN]


def find_ladder(xor_triples):
    """Find longest contiguous run of (aux_i, dw_a, dw_a+2)-shape EVEN triples
    where the next triple is (aux_i+1, dw_a+5, dw_a+5+2). Returns the run
    of triples (in order) or empty list if no length-≥5 run found."""
    triple_set = {t: p for t, p in xor_triples}
    longest_run = []
    for t, p in xor_triples:
        a, b, c = t
        if not (b - a > 100 and c - b == 2): continue
        run = [(t, p)]
        cur = t
        while True:
            nxt = (cur[0]+1, cur[1]+5, cur[2]+5)
            if triple_set.get(nxt) == p:
                run.append((nxt, p))
                cur = nxt
            else: break
        if len(run) > len(longest_run):
            longest_run = run
    return longest_run if len(longest_run) >= 5 else []


def mine_f384_ladder(cnf, budget=30):
    """One-shot mining: run cadical with LRAT proof, extract the F384 ladder.
    Returns (size3_clauses, size2_equiv_clauses, mining_wall_seconds, error)."""
    with tempfile.NamedTemporaryFile(suffix=".lrat", delete=False) as f:
        proof_path = f.name

    t0 = time.time()
    try:
        r = subprocess.run([
            "cadical", "-t", str(budget), "--seed=0", "-q", "--binary=false",
            cnf, proof_path,
        ], capture_output=True, text=True, timeout=budget+15)
        wall = time.time() - t0
        if not os.path.exists(proof_path):
            return [], [], wall, "cadical didn't produce proof"

        xor = parse_drat_proof(proof_path)
        run = find_ladder(xor)
        if not run:
            return [], [], wall, "no ladder found in proof"

        # Convert run to injectable clauses
        size3_clauses = []
        size2_clauses = []
        for t, p in run:
            # EVEN polarities: (1,1,0), (1,0,1), (0,1,1), (0,0,0)
            for s in p:  # 4 polarity tuples per triple
                lits = [v if s_i == 1 else -v for v, s_i in zip(t, s)]
                size3_clauses.append(lits)
        # Plus the size-2 equivalences: aux_i ⇔ dW_(a+1) where t = (aux_i, dw_a, dw_a+2)
        # So size-2 clauses are on (aux_i, dw_(a+1)) pairs.
        # We don't extract these from the proof directly here; future iteration.
        # For now: just emit the size-3 ladder.

        return size3_clauses, size2_clauses, wall, None
    finally:
        try: os.unlink(proof_path)
        except OSError: pass


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def parse_cand_filename(cnf_path):
    """Extract (m0, fill, kbit) from an aux_force_sr*_n32_*_m*_fill*.cnf path."""
    base = os.path.basename(cnf_path)
    m = re.search(r"bit(?P<kbit>\d+)_m(?P<m0>[0-9a-f]+)_fill(?P<fill>[0-9a-f]+)", base)
    if m:
        return int(m["m0"], 16), int(m["fill"], 16), int(m["kbit"])
    m = re.search(r"msb_m(?P<m0>[0-9a-f]+)_fill(?P<fill>[0-9a-f]+)", base)
    if m:
        return int(m["m0"], 16), int(m["fill"], 16), 31
    return None, None, None


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip(), formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--cnf", required=True, help="aux_force or aux_expose CNF")
    ap.add_argument("--varmap", help="varmap JSON (auto-detected if absent)")
    ap.add_argument("--out", default="-", help="output JSON path (default stdout)")
    ap.add_argument("--m0", help="override m0 (hex)")
    ap.add_argument("--fill", help="override fill (hex)")
    ap.add_argument("--mine-ladder", action="store_true",
                    help="actually run cadical to mine the ladder (Class A only)")
    ap.add_argument("--ladder-budget", type=int, default=30, help="cadical seconds for ladder mining")
    args = ap.parse_args()

    if not os.path.exists(args.cnf):
        print(f"ERROR: CNF not found: {args.cnf}", file=sys.stderr); sys.exit(2)

    varmap = args.varmap or args.cnf + ".varmap.json"
    if not os.path.exists(varmap):
        print(f"WARNING: varmap not found at {varmap}; F343 baseline mining will skip", file=sys.stderr)
        varmap = None

    if args.m0 and args.fill:
        m0 = int(args.m0, 16); fill = int(args.fill, 16); kbit = None
    else:
        m0, fill, kbit = parse_cand_filename(args.cnf)
        if m0 is None:
            print(f"ERROR: can't parse cand from filename {args.cnf} and no --m0/--fill given", file=sys.stderr)
            sys.exit(2)

    cls, reason = f387_class_decision(m0, fill)
    print(f"# bridge_preflight_extended on {os.path.basename(args.cnf)}", file=sys.stderr)
    print(f"#   cand: m0=0x{m0:08x} fill=0x{fill:08x} kbit={kbit}", file=sys.stderr)
    print(f"#   F387 class: {cls} ({reason})", file=sys.stderr)

    # F343 baseline (always)
    f343_units = []
    f343_pairs = []
    f343_err = None
    if varmap:
        f343_units, f343_pairs, f343_err = mine_f343_baseline(args.cnf, varmap)
        if f343_err:
            print(f"#   F343 mining failed: {f343_err}", file=sys.stderr)
        else:
            print(f"#   F343 baseline: {len(f343_units)} units + {len(f343_pairs)} pairs", file=sys.stderr)

    # F384 ladder (Class A only, if --mine-ladder)
    ladder3 = []
    ladder2 = []
    ladder_wall = 0.0
    ladder_err = None
    if cls == "A" and args.mine_ladder:
        print(f"#   mining F384 ladder (cadical {args.ladder_budget}s)...", file=sys.stderr)
        ladder3, ladder2, ladder_wall, ladder_err = mine_f384_ladder(args.cnf, args.ladder_budget)
        if ladder_err:
            print(f"#   F384 mining failed: {ladder_err}", file=sys.stderr)
        else:
            print(f"#   F384 ladder: {len(ladder3)} size-3 clauses (over {len(ladder3)//4} XOR triples)", file=sys.stderr)

    out = {
        "cnf": args.cnf,
        "cand": {"m0": f"0x{m0:08x}", "fill": f"0x{fill:08x}", "kernel_bit": kbit},
        "class_decision": cls,
        "class_decision_reason": reason,
        "F343_baseline": {
            "n_units": len(f343_units),
            "n_pairs": len(f343_pairs),
            "units": f343_units,
            "pairs": f343_pairs,
            "error": f343_err,
        },
        "F384_ladder": {
            "applicable": cls == "A",
            "mined": cls == "A" and args.mine_ladder,
            "n_size3_clauses": len(ladder3),
            "n_size2_equivalences": len(ladder2),
            "size3_clauses": ladder3,
            "size2_equivalences": ladder2,
            "mining_wall_seconds": round(ladder_wall, 2),
            "error": ladder_err,
        },
        "total_clauses_to_inject": len(f343_units) + len(f343_pairs) + len(ladder3) + len(ladder2),
    }

    text = json.dumps(out, indent=2)
    if args.out == "-":
        print(text)
    else:
        with open(args.out, "w") as f:
            f.write(text)
        print(f"# wrote {args.out}", file=sys.stderr)
    print(f"# total clauses to inject: {out['total_clauses_to_inject']}", file=sys.stderr)


if __name__ == "__main__":
    main()
