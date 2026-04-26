#!/usr/bin/env python3
"""locked_bit_hint_wrapper.py — Mode A + locked-bit / de58-only hints encoder.

Wraps cascade_aux_encoder.build_cascade_aux_cnf to inject de58 unit
clauses on aux_reg[("e", 58)]. Two hint variants:

  default (--hint-mode marginal-locked, the 13-bit variant):
    Compute de58 image marginals over a 1M-sample image, fix bits whose
    marginal is exactly 0 or 1. Cand-level constraint, no W57 needed.
    Median speedup ~1.16x at 50k (n=18, commit c110556).

  --hint-mode de58-at-w57 (the 32-bit variant; STRONGER):
    User supplies a W57. Compute the SINGLE de58 value that all such
    chambers produce (per-chamber de58_size = 1, verified). Inject all
    32 de58 bits as unit clauses. Median speedup 1.56x on n=4 cands
    (commit 3bc3da9, this memo). Strictly more information than
    marginal-locked.

Usage (marginal-locked, default):
  python3 locked_bit_hint_wrapper.py --m0 0xMMM --fill 0xFFF --bit B \\
                                     --mode expose --out OUT.cnf

Usage (de58-at-w57):
  python3 locked_bit_hint_wrapper.py --m0 0xMMM --fill 0xFFF --bit B \\
                                     --hint-mode de58-at-w57 \\
                                     --w57 0xWWWWWWWW \\
                                     --mode expose --out OUT.cnf

Or from registry:
  python3 locked_bit_hint_wrapper.py --cand-id <cand_n32_...> --mode expose --out OUT.cnf

NAMING CONVENTION (for audit_cnf.py compatibility):
  marginal-locked: `aux_<mode>_sr61_n32_bit<B>_m<M0>_fill<FILL>_lbh.cnf`
  de58-at-w57:     `aux_<mode>_sr61_n32_bit<B>_m<M0>_fill<FILL>_de58w<W57>.cnf`
  - The `aux_<mode>_sr61_*` prefix matches existing cascade_aux audit pattern
  - The `_lbh` / `_de58w<...>` suffix denotes the hint variant
  - Output CNFs share the cascade_aux_<mode> fingerprint range
    (vars ~13360-14000, clauses ~55400-56500)

Behavior:
  - marginal-locked: compute de58 image marginals → fix locked bits.
  - de58-at-w57: compute de58 = round58(... W57 ...) once → fix all 32 bits.

Important caveats (read before deploying):
  - Speedup is preprocessing-only — gone by ~500k conflicts.
  - High seed-variance for marginal-locked: ~25% regression rate.
    de58-at-w57 has not been measured at n=18 yet; treat as preliminary.
  - Marginal-locked speedup scales inversely with de58_size — use only
    on cands with small de58 image (<10k).
  - de58-at-w57 requires a W57. Yale's GPU off58 chart scan provides
    HW4-reaching W57s for many cands; the canonical W57 is also valid
    (it just uses a different chamber's de58 value).
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
from lib.sha256 import K, MASK, Sigma0, Sigma1, Ch, Maj, precompute_state


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


def _cascade1_offset(s1, s2):
    dh = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    T2_1 = (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & MASK
    T2_2 = (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & MASK
    return (dh + dSig1 + dCh + T2_1 - T2_2) & MASK


def _sha_round(s, k, w):
    a, b, c, d, e, f, g, h = s
    T1 = (h + Sigma1(e) + Ch(e, f, g) + k + w) & MASK
    T2 = (Sigma0(a) + Maj(a, b, c)) & MASK
    return [(T1 + T2) & MASK, a, b, c, (d + T1) & MASK, e, f, g]


def compute_de58_at_w57(m0, fill, kernel_bit, w57):
    """Compute the (single) de58 value at fixed W57.

    Per-chamber de58_size = 1, so this is well-defined: any choice of
    W58 that extends cascade-1 from this slot-57 state will produce
    the same de58.
    """
    M1 = [m0] + [fill] * 15
    M2 = list(M1)
    M2[0] ^= (1 << kernel_bit)
    M2[9] ^= (1 << kernel_bit)
    s1, _ = precompute_state(M1)
    s2, _ = precompute_state(M2)
    cw57 = _cascade1_offset(s1, s2)
    w57_2 = (w57 + cw57) & MASK
    s1_57 = _sha_round(s1, K[57], w57)
    s2_57 = _sha_round(s2, K[57], w57_2)
    cw58 = _cascade1_offset(s1_57, s2_57)
    s1_58 = _sha_round(s1_57, K[58], 0)
    s2_58 = _sha_round(s2_57, K[58], cw58)
    return (s1_58[4] - s2_58[4]) & MASK


def get_de58_at_w57_bits(m0, fill, kernel_bit, w57):
    """Return list of (bit_position, locked_value) for ALL 32 de58 bits at fixed W57.

    Returns: (locked_bits_list, de58_value, virtual_image_size=1).
    """
    de58 = compute_de58_at_w57(m0, fill, kernel_bit, w57)
    locked = [(bit, (de58 >> bit) & 1) for bit in range(32)]
    return locked, de58, 1


def cand_from_id(cand_id):
    """Look up (m0, fill, kernel_bit) from registry by cand id."""
    import yaml
    with open(os.path.join(REPO, "headline_hunt/registry/candidates.yaml")) as f:
        cands = yaml.safe_load(f)
    for c in cands:
        if c["id"] == cand_id:
            return (int(c["m0"], 16), int(c["fill"], 16), c["kernel"]["bit"])
    raise KeyError(f"cand_id {cand_id} not found")


def write_cnf(out_path, cnf, locked_bits, aux_reg, m0, fill, kernel_bit, mode,
              img_size, hint_mode="marginal-locked", w57=None, de58_value=None):
    """Write CNF with locked-bit unit clauses prepended."""
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
        f.write(f"c locked_bit_hint_wrapper v2 — 2026-04-26\n")
        f.write(f"c base_mode={mode}, hint_mode={hint_mode}\n")
        f.write(f"c m0=0x{m0:08x}  fill=0x{fill:08x}  kernel_bit={kernel_bit}\n")
        if hint_mode == "de58-at-w57":
            f.write(f"c W57=0x{w57:08x}  de58_value=0x{de58_value:08x}  "
                    f"32-bit per-chamber hint\n")
            f.write(f"c source: per-chamber de58_size=1 finding "
                    f"(commit 3bc3da9, 20260426_de58_only_per_chamber_hints.md)\n")
            f.write(f"c CAVEAT: 1.31-2.20x on n=4 cands; n=18 deployment pending\n")
        else:
            f.write(f"c de58 image size={img_size}, locked bits found={len(locked_bits)}, "
                    f"unit clauses added={len(unit_clauses)} (skipped {skipped} const/missing)\n")
            f.write(f"c source: D2 finding (commit 505859b) + locked-bit-hint deployment "
                    f"(commits 795bfb3, 88eb025, 557fc42, a95a267)\n")
            f.write(f"c CAVEAT: median speedup ~1.16x n=18 at 50k kissat, "
                    f"high seed-variance, degrades to ~1x by 500k\n")
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
    ap.add_argument("--hint-mode", choices=["marginal-locked", "de58-at-w57"],
                    default="marginal-locked",
                    help="hint variant: marginal-locked (default, ~13 hints) or "
                         "de58-at-w57 (32 hints; requires --w57)")
    ap.add_argument("--w57", help="W57 value (hex; required with --hint-mode de58-at-w57)")
    ap.add_argument("--out", required=True, help="output CNF path")
    ap.add_argument("--samples", type=int, default=1 << 20,
                    help="de58 image samples (marginal-locked only)")
    args = ap.parse_args()

    if args.cand_id:
        m0, fill, kernel_bit = cand_from_id(args.cand_id)
    else:
        if not (args.fill and args.bit is not None):
            ap.error("--m0 requires --fill and --bit")
        m0 = int(args.m0, 16)
        fill = int(args.fill, 16)
        kernel_bit = args.bit

    if args.hint_mode == "de58-at-w57" and args.w57 is None:
        ap.error("--hint-mode de58-at-w57 requires --w57 0xHEX")

    print(f"locked_bit_hint_wrapper: m0=0x{m0:08x} fill=0x{fill:08x} bit={kernel_bit} "
          f"sr={args.sr} mode={args.mode} hint_mode={args.hint_mode}")

    w57_val = None
    de58_value = None
    if args.hint_mode == "de58-at-w57":
        w57_val = int(args.w57, 16)
        locked_bits, de58_value, img_size = get_de58_at_w57_bits(
            m0, fill, kernel_bit, w57_val
        )
        print(f"  W57=0x{w57_val:08x} → de58=0x{de58_value:08x} "
              f"(HW={bin(de58_value).count('1')}); injecting all 32 bits")
    else:
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
        args.mode, img_size, hint_mode=args.hint_mode,
        w57=w57_val, de58_value=de58_value,
    )
    print(f"  Wrote {args.out}: {n_vars} vars, {n_clauses} clauses "
          f"({n_units} hints + {len(cnf.clauses)} base; skipped {n_skipped} hints)")
    if args.hint_mode == "marginal-locked" and img_size > 10000:
        print(f"  NOTE: de58 image size {img_size} > 10k — marginal-locked speedup "
              f"likely small per scaling test (88eb025). Consider --hint-mode de58-at-w57.")


if __name__ == "__main__":
    main()
