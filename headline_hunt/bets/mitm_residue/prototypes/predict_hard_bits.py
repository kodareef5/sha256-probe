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
    """Return dict with predicted h60, f60 hard-bit positions (closed-form exact),
    plus a lower-bound prediction for g60 (HW(db56_xor) carrier set + 0-3 carry
    extras empirically). See results/20260424_g60_lower_bound.md."""
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
    db56_mod = (s1[1] - s2[1]) & MASK
    db56_xor = s1[1] ^ s2[1]

    # h60 = de57 = dd56 - dT2_56 = dd56 + dh + dSig1 + dCh - cw57 (modular)
    delta_e57 = (dd56 + dh + dSig1 + dCh - cw57) & MASK

    # f60 = de59 = db56_mod (cascade gives dT1_59 = 0)
    delta_e59 = db56_mod

    # g60 = de58 — closed-form lower bound:
    # dMaj_xor = (a57 ⊕ b57) AND db56_xor → uniform iff db56_xor[i] = 1.
    # g60_uniform_LOWER_BOUND = {i : db56_xor[i] = 1}.
    # Empirically the actual g60 set is this LOWER BOUND ∪ {0..3 carry extras}.
    g60_lower = [i for i in range(32) if (db56_xor >> i) & 1]

    def uniform_bits(delta, lo=0.45, hi=0.55):
        return [i for i in range(1, 32)
                if delta & ((1 << i) - 1) != 0
                and lo <= ((delta & ((1 << i) - 1)) / (1 << i)) <= hi]

    h60 = uniform_bits(delta_e57)
    f60 = uniform_bits(delta_e59)
    return {
        "cascade_eligible": True,
        "delta_e57": delta_e57,
        "delta_e59": delta_e59,
        "db56_xor": db56_xor,
        "h60_uniform": h60,
        "f60_uniform": f60,
        "g60_uniform_lower_bound": g60_lower,
        "g60_uniform_count_lb": len(g60_lower),
        "total_hard_bits_lower_bound": len(h60) + len(f60) + len(g60_lower),
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
        out = []
        for r in results:
            d = dict(r)
            if r.get("cascade_eligible"):
                d["delta_e57"] = f"0x{r['delta_e57']:08x}"
                d["delta_e59"] = f"0x{r['delta_e59']:08x}"
                d["db56_xor"]  = f"0x{r['db56_xor']:08x}"
            out.append(d)
        print(json.dumps(out, indent=2))
    else:
        elig = [r for r in results if r["cascade_eligible"]]
        print(f"Predicted hard-residue bits at round 60 (closed-form: h60+f60 exact, g60 lower bound)")
        print(f"  Candidates: {len(elig)}/{len(results)} cascade-eligible\n")
        # Sort by total lower bound
        elig_sorted = sorted(elig, key=lambda r: r["total_hard_bits_lower_bound"])
        print(f"{'id':52s} {'h60':>4s} {'f60':>4s} {'g60_lb':>6s}  {'total_lb':>8s}")
        print("-" * 95)
        for r in elig_sorted:
            print(f"{r['id'][:50]:52s} "
                  f"{len(r['h60_uniform']):>4d} "
                  f"{len(r['f60_uniform']):>4d} "
                  f"{r['g60_uniform_count_lb']:>6d}  "
                  f"{r['total_hard_bits_lower_bound']:>8d}")


if __name__ == "__main__":
    main()
