#!/usr/bin/env python3
"""
build_corpus.py — Generate block-1 near-collision residuals as JSONL.

Each residual is an (IV_1, IV_2) pair from a single forward run where the
round-63 register difference is below a HW threshold. These feed the Wang-
style trail-search engine that block2_wang needs to build.

Filter strategy (per writeups/multiblock_feasibility.md):
  - Theorem 4: da=de at r>=61. So the residual structure has da=de always
    (within numerical precision). Sanity-check this.
  - Minimum HW residuals (≤ 8 across abcd at round 63) are the highest-value
    candidates for trail search.
  - Cluster by (active_register_set, hw_per_register).

Output: JSONL, one record per residual that passes the filter.

Usage:
    python3 build_corpus.py --m0 0x17149975 --fill 0xffffffff --kernel-bit 31 \
        --samples 1000000 --hw-threshold 16 --out residuals_msb.jsonl
"""
import argparse
import json
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, REPO)
sys.path.insert(0, os.path.join(REPO, "headline_hunt", "bets",
                                 "mitm_residue", "prototypes"))
from lib.sha256 import (K, MASK, sigma0, sigma1, Sigma0, Sigma1, Ch, Maj, hw,
                        add, precompute_state)
from forward_table_builder import (cascade_step_offset, cascade2_offset,
                                    apply_round)


def run_full(s1_init, s2_init, W1_pre, W2_pre, w1_57, w1_58, w1_59, w1_60):
    """Like run_one but also returns the full final-state pair, not just diff."""
    cw57 = cascade_step_offset(s1_init, s2_init, 57)
    w2_57 = (w1_57 + cw57) & MASK
    s1_57 = apply_round(s1_init, w1_57, 57)
    s2_57 = apply_round(s2_init, w2_57, 57)

    cw58 = cascade_step_offset(s1_57, s2_57, 58)
    w2_58 = (w1_58 + cw58) & MASK
    s1_58 = apply_round(s1_57, w1_58, 58)
    s2_58 = apply_round(s2_57, w2_58, 58)

    cw59 = cascade_step_offset(s1_58, s2_58, 59)
    w2_59 = (w1_59 + cw59) & MASK
    s1_59 = apply_round(s1_58, w1_59, 59)
    s2_59 = apply_round(s2_58, w2_59, 59)

    if (s1_59[1] ^ s2_59[1]) or (s1_59[2] ^ s2_59[2]) or (s1_59[3] ^ s2_59[3]):
        return None

    cw60 = cascade2_offset(s1_59, s2_59)
    w2_60 = (w1_60 + cw60) & MASK
    s1_60 = apply_round(s1_59, w1_60, 60)
    s2_60 = apply_round(s2_59, w2_60, 60)

    if (s1_60[4] ^ s2_60[4]):
        return None

    W1 = list(W1_pre[:57]) + [w1_57, w1_58, w1_59, w1_60]
    W2 = list(W2_pre[:57]) + [w2_57, w2_58, w2_59, w2_60]
    for r in range(61, 64):
        W1.append(add(sigma1(W1[r-2]), W1[r-7], sigma0(W1[r-15]), W1[r-16]))
        W2.append(add(sigma1(W2[r-2]), W2[r-7], sigma0(W2[r-15]), W2[r-16]))

    s1, s2 = s1_60, s2_60
    for r in range(61, 64):
        s1 = apply_round(s1, W1[r], r)
        s2 = apply_round(s2, W2[r], r)

    return {
        "state1_63": s1, "state2_63": s2,
        "diff63": tuple(s1[i] ^ s2[i] for i in range(8)),
        "w_ms": (w1_57, w1_58, w1_59, w1_60),
        "w_ms_2": (w2_57, w2_58, w2_59, w2_60),
        "cascade_offsets": (cw57, cw58, cw59, cw60),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m0", default="0x17149975")
    ap.add_argument("--fill", default="0xffffffff")
    ap.add_argument("--kernel-bit", type=int, default=31)
    ap.add_argument("--samples", type=int, default=100_000)
    ap.add_argument("--hw-threshold", type=int, default=16,
                    help="Save only residuals with total HW <= threshold "
                         "(across all 8 registers at round 63). Default 16.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--w1-60", default="0xb6befe82")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    m0 = int(args.m0, 16)
    fill = int(args.fill, 16)
    diff = 1 << args.kernel_bit
    w1_60 = int(args.w1_60, 16)

    M1 = [m0] + [fill]*15
    M2 = list(M1); M2[0] ^= diff; M2[9] ^= diff
    s1_init, W1_pre = precompute_state(M1)
    s2_init, W2_pre = precompute_state(M2)
    if s1_init[0] != s2_init[0]:
        print("ERROR: not cascade-eligible", file=sys.stderr); sys.exit(2)

    rng = random.Random(args.seed)
    REGS = "abcdefgh"

    t0 = time.time()
    n_kept = 0
    n_below_threshold = 0
    n_da_eq_de = 0
    hw_distribution = {}

    with open(args.out, "w") as fout:
        for trial in range(args.samples):
            w1_57 = rng.getrandbits(32)
            w1_58 = rng.getrandbits(32)
            w1_59 = rng.getrandbits(32)
            r = run_full(s1_init, s2_init, W1_pre, W2_pre,
                         w1_57, w1_58, w1_59, w1_60)
            if r is None:
                continue
            n_kept += 1
            d = r["diff63"]
            hw_total = sum(hw(x) for x in d)
            hw_distribution[hw_total] = hw_distribution.get(hw_total, 0) + 1
            if hw_total > args.hw_threshold:
                continue
            n_below_threshold += 1
            # Theorem 4 sanity: da == de at r=61 (and propagated, da_r vs de_r at r>=61
            # have specific relationships). At r=63, this is messier; we just record.
            if d[0] == d[4]:
                n_da_eq_de += 1
            rec = {
                "candidate": {
                    "m0": args.m0, "fill": args.fill, "kernel_bit": args.kernel_bit,
                },
                "w1_57": f"0x{w1_57:08x}",
                "w1_58": f"0x{w1_58:08x}",
                "w1_59": f"0x{w1_59:08x}",
                "w1_60": f"0x{w1_60:08x}",
                "w2_57": f"0x{r['w_ms_2'][0]:08x}",
                "w2_58": f"0x{r['w_ms_2'][1]:08x}",
                "w2_59": f"0x{r['w_ms_2'][2]:08x}",
                "w2_60": f"0x{r['w_ms_2'][3]:08x}",
                "iv1_63": [f"0x{x:08x}" for x in r["state1_63"]],
                "iv2_63": [f"0x{x:08x}" for x in r["state2_63"]],
                "diff63": [f"0x{x:08x}" for x in d],
                "hw63": [hw(x) for x in d],
                "hw_total": hw_total,
                "active_regs": [REGS[i] for i in range(8) if d[i] != 0],
                "da_eq_de": d[0] == d[4],
            }
            fout.write(json.dumps(rec) + "\n")

    elapsed = time.time() - t0
    print(f"Done. {args.samples} attempts, {n_kept} cascade-held, "
          f"{n_below_threshold} below HW={args.hw_threshold} threshold, "
          f"{n_da_eq_de} with da==de.", file=sys.stderr)
    print(f"Throughput: {args.samples/elapsed:.0f} samples/sec ({elapsed:.1f}s)",
          file=sys.stderr)
    if hw_distribution:
        sorted_hw = sorted(hw_distribution.items())
        print("HW total distribution (top 10 buckets):", file=sys.stderr)
        for hwv, cnt in sorted_hw[:10]:
            print(f"  HW={hwv}: {cnt}", file=sys.stderr)
        print(f"  min HW: {min(hw_distribution)}, max HW: {max(hw_distribution)}",
              file=sys.stderr)


if __name__ == "__main__":
    main()
