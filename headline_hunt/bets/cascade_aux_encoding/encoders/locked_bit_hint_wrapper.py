#!/usr/bin/env python3
"""locked_bit_hint_wrapper.py — Mode A + locked-bit hints encoder.

Wraps cascade_aux_encoder.build_cascade_aux_cnf to inject de58 locked-bit
unit clauses on aux_reg[("e", 58)]. Provides a Mode A → Mode-B-equivalent
preprocessing speedup at 50k kissat conflicts WITHOUT restricting the
solution set the way Mode B's force clauses do.

Discovery context: 2026-04-26 D2 follow-up (commits 795bfb3, 88eb025,
557fc42, a95a267). Multi-seed verified; speedup is ~1.5x median at 50k,
inversely scales with de58_size; high seed-variance (0.7x to 1.75x).

Usage:
  python3 locked_bit_hint_wrapper.py --m0 0xMMM --fill 0xFFF --bit B \\
                                     --mode expose|force --out OUT.cnf

Or from registry:
  python3 locked_bit_hint_wrapper.py --cand-id <cand_n32_...> --mode expose --out OUT.cnf

NAMING CONVENTION (for audit_cnf.py compatibility):
  Use filename `aux_<mode>_sr61_n32_bit<B>_m<M0>_fill<FILL>_lbh.cnf`
  - The `aux_<mode>_sr61_*` prefix matches existing cascade_aux audit pattern
  - The `_lbh` suffix denotes "locked-bit hints"
  - Output CNFs share the cascade_aux_<mode> fingerprint range
    (vars ~13360-14000, clauses ~55400-56500)
  Example:
    aux_expose_sr61_n32_bit19_m51ca0b34_fill55555555_lbh.cnf

Behavior:
  - Computes de58 image marginals (1M-sample image).
  - Identifies fully-locked bits (marginal exactly 0 or 1).
  - Emits cascade_aux Mode A or B CNF + unit clauses fixing those bits.

Important caveats (read before deploying):
  - Speedup is preprocessing-only — gone by ~500k conflicts.
  - High seed-variance: ~25% chance of regression on any single seed.
    Prefer multi-seed averaging for honest deployment.
  - Speedup scales inversely with de58_size — use only on cands with
    small de58 image (<10k); diminishing returns beyond.
  - DO NOT encode the full 256-image as a Tseitin disjunction; it's
    SLOWER than simple unit clauses.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
if REPO not in sys.path:
    sys.path.insert(0, REPO)
SR61_DIR = os.path.join(REPO, "headline_hunt", "bets", "sr61_n32")
if SR61_DIR not in sys.path:
    sys.path.insert(0, SR61_DIR)
sys.path.insert(0, HERE)

from cascade_aux_encoder import build_cascade_aux_cnf
from de58_disjoint_check import candidate_de58_image


def get_locked_bits(m0, fill, kernel_bit, n_samples=1 << 20):
    """Compute fully-locked bits in the de58 image.

    Returns: list of (bit_position, locked_value) for bits where marginal == 0 or 1.
    """
    img = candidate_de58_image(m0, fill, kernel_bit, n_samples=n_samples)
    locked = []
    for bit in range(32):
        ones = sum(1 for v in img if (v >> bit) & 1)
        if ones == 0:
            locked.append((bit, 0))
        elif ones == len(img):
            locked.append((bit, 1))
    return locked, len(img)


def cand_from_id(cand_id):
    """Look up (m0, fill, kernel_bit) from registry by cand id."""
    import yaml
    with open(os.path.join(REPO, "headline_hunt/registry/candidates.yaml")) as f:
        cands = yaml.safe_load(f)
    for c in cands:
        if c["id"] == cand_id:
            return (int(c["m0"], 16), int(c["fill"], 16), c["kernel"]["bit"])
    raise KeyError(f"cand_id {cand_id} not found")


def write_cnf(out_path, cnf, locked_bits, aux_reg, m0, fill, kernel_bit, mode, img_size):
    """Write CNF with optional locked-bit unit clauses prepended."""
    de58_lits = aux_reg.get(("e", 58))
    if de58_lits is None:
        raise RuntimeError("aux_reg[('e',58)] not exposed by encoder")

    unit_clauses = []
    skipped = 0
    for bit_pos, locked_val in locked_bits:
        lit = de58_lits[bit_pos]
        if not isinstance(lit, int):
            skipped += 1
            continue
        if lit == 1 or lit == -1:
            skipped += 1  # constant literal (already fixed)
            continue
        if locked_val == 1:
            unit_clauses.append([lit])
        else:
            unit_clauses.append([-lit])

    n_vars = cnf.next_var - 1
    n_clauses = len(cnf.clauses) + len(unit_clauses)

    with open(out_path, "w") as f:
        f.write(f"c locked_bit_hint_wrapper v1 — 2026-04-26\n")
        f.write(f"c base_mode={mode}, locked-bit-hints=YES\n")
        f.write(f"c m0=0x{m0:08x}  fill=0x{fill:08x}  kernel_bit={kernel_bit}\n")
        f.write(f"c de58 image size={img_size}, locked bits found={len(locked_bits)}, "
                f"unit clauses added={len(unit_clauses)} (skipped {skipped} const/missing)\n")
        f.write(f"c source: D2 finding (commit 505859b) + locked-bit-hint deployment "
                f"(commits 795bfb3, 88eb025, 557fc42, a95a267)\n")
        f.write(f"c CAVEAT: median speedup ~1.5x at 50k kissat, high seed-variance, "
                f"degrades to ~1x by 500k\n")
        f.write(f"p cnf {n_vars} {n_clauses}\n")
        for clause in unit_clauses:
            f.write(" ".join(str(x) for x in clause) + " 0\n")
        for clause in cnf.clauses:
            f.write(" ".join(str(x) for x in clause) + " 0\n")

    return n_vars, n_clauses, len(unit_clauses), skipped


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--cand-id", help="candidate id from candidates.yaml")
    src.add_argument("--m0", help="message word 0 (hex)")
    ap.add_argument("--fill", help="fill word (hex; required with --m0)")
    ap.add_argument("--bit", type=int, help="kernel bit (required with --m0)")
    ap.add_argument("--sr", type=int, default=61, help="schedule level (60 or 61)")
    ap.add_argument("--mode", choices=["expose", "force"], default="expose",
                    help="cascade_aux base mode (default: expose)")
    ap.add_argument("--out", required=True, help="output CNF path")
    ap.add_argument("--samples", type=int, default=1 << 20, help="de58 image samples")
    args = ap.parse_args()

    if args.cand_id:
        m0, fill, kernel_bit = cand_from_id(args.cand_id)
    else:
        if not (args.fill and args.bit is not None):
            ap.error("--m0 requires --fill and --bit")
        m0 = int(args.m0, 16)
        fill = int(args.fill, 16)
        kernel_bit = args.bit

    print(f"locked_bit_hint_wrapper: m0=0x{m0:08x} fill=0x{fill:08x} bit={kernel_bit} "
          f"sr={args.sr} mode={args.mode}")
    print(f"  Computing de58 image marginals ({args.samples} samples)...")
    locked_bits, img_size = get_locked_bits(m0, fill, kernel_bit, args.samples)
    print(f"  de58 image size: {img_size}")
    print(f"  locked bits: {len(locked_bits)}")
    if locked_bits:
        for bit, val in locked_bits[:10]:
            print(f"    de58[{bit}] = {val}")
        if len(locked_bits) > 10:
            print(f"    ... and {len(locked_bits) - 10} more")

    if not locked_bits:
        print(f"  WARNING: no locked bits found — wrapper will produce control CNF (no hints)")

    print(f"  Building cascade_aux base CNF (mode={args.mode}, sr={args.sr})...")
    result = build_cascade_aux_cnf(sr=args.sr, m0=m0, fill=fill,
                                   kernel_bit=kernel_bit, mode=args.mode)
    cnf = result[0]
    aux_reg = result[2]

    n_vars, n_clauses, n_units, n_skipped = write_cnf(
        args.out, cnf, locked_bits, aux_reg, m0, fill, kernel_bit,
        args.mode, img_size,
    )
    print(f"  Wrote {args.out}: {n_vars} vars, {n_clauses} clauses "
          f"({n_units} hints + {len(cnf.clauses)} base; skipped {n_skipped} hints)")
    if img_size > 10000:
        print(f"  NOTE: de58 image size {img_size} > 10k — locked-bit-hint speedup "
              f"likely small per scaling test (88eb025).")


if __name__ == "__main__":
    main()
