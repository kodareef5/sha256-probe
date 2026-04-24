#!/usr/bin/env python3
"""
predict_hard_bits.py — Closed-form O(1) prediction of round-60 hard-residue bits.

Implements the algebraic predictions from:
- 20260424_algebraic_prediction.md  (h60 = de57)
- 20260424_f60_h60_prediction.md    (f60 = de59)

Verified empirically across 6 candidates. g60 = de58 is NOT closed-form yet
(Δe58 varies with w1_57); this script returns None for g60.

Usage:
    python3 predict_hard_bits.py --m0 0x17149975 --fill 0xffffffff --kernel-bit 31
    python3 predict_hard_bits.py --candidates-yaml /path/to/candidates.yaml
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, REPO)
from lib.sha256 import precompute_state, K, MASK, Sigma0, Sigma1, Ch, Maj


def predict(m0, fill, kbit):
    """Return dict with predicted h60, f60 hard-bit positions, plus the cascade
    constants used. g60 is None (not yet derivable in closed form)."""
    M1 = [m0] + [fill] * 15
    M2 = list(M1); M2[0] ^= 1 << kbit; M2[9] ^= 1 << kbit
    s1, _ = precompute_state(M1)
    s2, _ = precompute_state(M2)
    if s1[0] != s2[0]:
        return {"cascade_eligible": False}

    dh = (s1[7] - s2[7]) & MASK
    dSig1 = (Sigma1(s1[4]) - Sigma1(s2[4])) & MASK
    dCh = (Ch(s1[4], s1[5], s1[6]) - Ch(s2[4], s2[5], s2[6])) & MASK
    T2_1 = (Sigma0(s1[0]) + Maj(s1[0], s1[1], s1[2])) & MASK
    T2_2 = (Sigma0(s2[0]) + Maj(s2[0], s2[1], s2[2])) & MASK
    cw57 = (dh + dSig1 + dCh + (T2_1 - T2_2)) & MASK
    dd56 = (s1[3] - s2[3]) & MASK
    db56 = (s1[1] - s2[1]) & MASK

    # h60 = de57 = dd56 - dT2_56 = dd56 + dh + dSig1 + dCh - cw57 (modular)
    delta_e57 = (dd56 + dh + dSig1 + dCh - cw57) & MASK

    # f60 = de59 = db56 (cascade gives dT1_59 = 0)
    delta_e59 = db56

    def uniform_bits(delta, lo=0.45, hi=0.55):
        return [i for i in range(1, 32)
                if delta & ((1 << i) - 1) != 0
                and lo <= ((delta & ((1 << i) - 1)) / (1 << i)) <= hi]

    return {
        "cascade_eligible": True,
        "delta_e57": delta_e57,
        "delta_e59": delta_e59,
        "h60_uniform": uniform_bits(delta_e57),
        "f60_uniform": uniform_bits(delta_e59),
        "g60_uniform": None,  # not yet predictable in closed form
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--m0", default=None)
    ap.add_argument("--fill", default=None)
    ap.add_argument("--kernel-bit", type=int, default=None)
    ap.add_argument("--candidates-yaml", default=None,
                    help="Predict for every candidate in this YAML file")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    results = []
    if args.candidates_yaml:
        import yaml
        with open(args.candidates_yaml) as f:
            cands = yaml.safe_load(f)
        for c in cands:
            r = predict(int(c["m0"], 16), int(c["fill"], 16), c["kernel"]["bit"])
            r["id"] = c["id"]
            results.append(r)
    else:
        if args.m0 is None or args.fill is None or args.kernel_bit is None:
            print("ERROR: provide --m0, --fill, --kernel-bit OR --candidates-yaml",
                  file=sys.stderr)
            sys.exit(2)
        r = predict(int(args.m0, 16), int(args.fill, 16), args.kernel_bit)
        r["id"] = "manual"
        results.append(r)

    if args.json:
        import json
        # Convert to JSON-friendly form (hex for the deltas)
        out = []
        for r in results:
            d = dict(r)
            if r.get("cascade_eligible"):
                d["delta_e57"] = f"0x{r['delta_e57']:08x}"
                d["delta_e59"] = f"0x{r['delta_e59']:08x}"
            out.append(d)
        print(json.dumps(out, indent=2))
    else:
        # Pretty table
        elig = [r for r in results if r["cascade_eligible"]]
        print(f"Predicted hard-residue bits at round 60 (h60 + f60 only — g60 needs marginal model)")
        print(f"  Candidates: {len(elig)}/{len(results)} cascade-eligible\n")
        print(f"{'id':50s} {'h60':28s} {'f60':22s}  total")
        print("-" * 130)
        for r in elig:
            h_str = str(r["h60_uniform"])
            f_str = str(r["f60_uniform"])
            tot = len(set(f"h{b}" for b in r["h60_uniform"]) |
                       set(f"f{b}" for b in r["f60_uniform"]))
            print(f"{r['id'][:48]:50s} {h_str:28s} {f_str:22s}  {tot}")


if __name__ == "__main__":
    main()
