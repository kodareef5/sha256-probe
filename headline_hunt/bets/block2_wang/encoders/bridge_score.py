#!/usr/bin/env python3
"""
bridge_score.py — score W-witnesses for bridge-guided block2 search.

Consumes empirical structure findings from F374/F376/F377 and yale's F378-F384:

  Hard constraints (auto-reject if violated):
    1. active_regs == [a,b,c,e,f,g]  (F374/F376 universal cascade-1 fingerprint)
    2. da_63 != de_63                (F374/F376 universal: 100% of 447k records have da≠de)
    3. dW57[22:23] != forbidden_pair_for_kbit  (yale F383/F384 bridge core, F377 kbit-table)

  Soft score (higher = better candidate for further cancellation toward collision):
    A. distance_below_mode = max(0, 95 - hw_total)  (deeper tail scores higher; F101 mode at HW 90-99)
    B. expected_asymmetry_match  (reward records that match the HW-band-dependent c/g vs a/b/e/f asymmetry per F376)
    C. cluster_dominance_bonus  (bit3/bit2/bit28 deep-tail concentrators per F374 finding 4)

Usage:
    # Score one record
    python3 bridge_score.py --record '{"hw63": [11,7,8,0,12,8,9,0], "w1_57": "0x...", ..., "kernel_bit": 3, "active_regs": ["a","b","c","e","f","g"], "da_eq_de": false}'

    # Score all records in a corpus, rank top-K
    python3 bridge_score.py --corpus path/to/corpus.jsonl --top 20

    # Validate: does it rank known sub-65 above controls?
    python3 bridge_score.py --validate

References:
    F374: 4 structural signatures of sub-65 cascade-1 residuals
    F376: HW-band-dependent c/g vs a/b/e/f asymmetry (mode at 90-99 is crossing point)
    F377: 9-cand kbit→polarity table (falsified F340's fill-bit-31 rule)
"""
import argparse
import glob
import json
import os
import sys
from typing import Optional

# F377 kbit → forbidden W57[22:23] polarity table
# (0, 1) for kbit ∈ {0, 10, 17, 31}, (0, 0) for kbit ∈ {2, 11, 13, 28}
# Tentative HW(kbit) parity rule for unprobed kbits: HW(kbit) odd → (0, 0); even → (0, 1)
F377_KBIT_TABLE = {
    0:  (0, 1), 10: (0, 1), 17: (0, 1), 31: (0, 1),
    2:  (0, 0), 11: (0, 0), 13: (0, 0), 28: (0, 0),
}

def predicted_forbidden_for_kbit(kbit: int):
    """Returns the predicted W57[22:23] forbidden polarity for a kbit.
    Uses F377 measured table when available; falls back to HW(kbit) parity rule."""
    if kbit in F377_KBIT_TABLE:
        return F377_KBIT_TABLE[kbit]
    # HW(kbit) parity fallback (tentative per F377)
    hw = bin(kbit).count("1")
    return (0, 0) if hw % 2 == 1 else (0, 1)

# F376 HW-band-dependent c/g vs a/b/e/f gap (positive = a/b/e/f heavier)
# Used to compute "expected_asymmetry" so we can reward records that exceed it
F376_BAND_GAP = [
    (60,   None,  +25.7),   # <60   gap +13.9% but small sample; treated as 60-64 band
    (60,   65,    +25.7),
    (65,   70,    +21.5),
    (70,   80,    +11.4),
    (80,   90,    +5.7),
    (90,   100,   -0.1),
    (100,  110,   -2.3),
    (110,  None,  -2.6),
]

def expected_cg_abef_gap_pct(hw_total):
    """Returns the F376 expected c/g vs a/b/e/f gap percent for the given HW band."""
    for lo, hi, gap in F376_BAND_GAP:
        if hi is None:
            if hw_total >= lo: return gap
        elif lo <= hw_total < hi:
            return gap
    return 0.0

# F374 finding 4: deep-tail dominator cands (54% of sub-65 records)
F374_DOMINATORS = {"bit3_m33ec77ca", "bit2_ma896ee41", "bit28_md1acca79"}


def bridge_score(record: dict, kbit: Optional[int] = None) -> dict:
    """Score a W-witness record.

    Returns dict with: score (float or None if rejected), components, reject_reason.
    Higher score = better candidate.
    """
    out = {"score": None, "components": {}, "reject_reason": None}

    # --- Hard constraints ---

    # 1. Active register set must match cascade-1
    active = sorted(record.get("active_regs", []))
    if active != ["a", "b", "c", "e", "f", "g"]:
        out["reject_reason"] = f"active_regs {active} != cascade-1 fingerprint"
        return out

    # 2. da_63 != de_63 must hold (F374/F376 universal)
    if record.get("da_eq_de") is True:
        out["reject_reason"] = "da_63 == de_63 (excluded by F374/F376 universal)"
        return out

    # 3. Bridge polarity: dW57[22:23] != forbidden_pair_for_kbit
    if kbit is None:
        kbit = record.get("kernel_bit") or record.get("candidate", {}).get("kernel_bit")
    if kbit is not None:
        try:
            w1_57 = int(record["w1_57"], 16)
            w2_57 = int(record["w2_57"], 16)
            dw57 = w1_57 ^ w2_57
            b22 = (dw57 >> 22) & 1
            b23 = (dw57 >> 23) & 1
            forbidden = predicted_forbidden_for_kbit(kbit)
            if (b22, b23) == forbidden:
                out["reject_reason"] = (
                    f"bridge polarity dW57[22:23]={(b22, b23)} matches forbidden pair "
                    f"for kbit={kbit} per F377 table"
                )
                return out
            out["components"]["bridge_polarity_ok"] = True
            out["components"]["dW57_22_23"] = [b22, b23]
            out["components"]["forbidden_for_kbit"] = list(forbidden)
        except (KeyError, ValueError):
            out["components"]["bridge_polarity_ok"] = "unknown (W vectors missing or malformed)"

    # --- Soft score components (higher = better) ---

    hw_total = record.get("hw_total")
    if hw_total is None:
        out["reject_reason"] = "hw_total missing"
        return out

    hw63 = record.get("hw63", [0]*8)
    # indices: a=0, b=1, c=2, d=3, e=4, f=5, g=6, h=7
    cg = hw63[2] + hw63[6]
    abef = hw63[0] + hw63[1] + hw63[4] + hw63[5]

    # A. Distance below mode (HW 90-99 is the natural cascade-1 mode per F101)
    A = max(0, 95 - hw_total)

    # B. Expected asymmetry match
    # F376 says: at sub-80 c/g should be lighter than a/b/e/f (gap positive).
    # A record with stronger-than-expected asymmetry is more "structurally extreme".
    # We reward records whose actual gap exceeds the expected band gap.
    expected_gap = expected_cg_abef_gap_pct(hw_total)  # in pct
    if abef > 0:
        actual_gap = 100.0 * (abef/4.0 - cg/2.0) / (abef/4.0)
    else:
        actual_gap = 0.0
    # B = (actual_gap - expected_gap), positive when more asymmetric than expected
    B = actual_gap - expected_gap

    # C. Cluster dominance bonus: bit3/bit2/bit28 are F374's deep-tail concentrators
    cand_id = record.get("_cand", "") or record.get("candidate", {}).get("name", "")
    C = 0.0
    if any(d in cand_id for d in F374_DOMINATORS):
        C = 5.0  # flat bonus

    # Combined score
    score = A + 0.3 * B + C
    out["score"] = round(score, 3)
    out["components"]["A_distance_below_mode"] = round(A, 2)
    out["components"]["B_excess_cg_asymmetry_pct"] = round(B, 2)
    out["components"]["C_dominator_bonus"] = round(C, 2)
    out["components"]["hw_total"] = hw_total
    out["components"]["cg_hw"] = cg
    out["components"]["abef_hw"] = abef
    return out


def score_corpus(path: str, kbit: Optional[int] = None):
    """Score every record in a corpus, return list of (score, record) tuples."""
    out = []
    cand_short = os.path.basename(path)[len("corpus_"):-len(".jsonl")]
    with open(path) as f:
        for line in f:
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            r["_cand"] = cand_short
            kb = kbit if kbit is not None else r.get("candidate", {}).get("kernel_bit")
            s = bridge_score(r, kb)
            out.append((s, r))
    return out


def validate():
    """Validate the score: does it rank known sub-65 records above typical-HW controls?"""
    corpus_dir = "headline_hunt/bets/block2_wang/residuals/by_candidate"
    corpora = sorted(glob.glob(os.path.join(corpus_dir, "corpus_*.jsonl")))
    if not corpora:
        print(f"ERROR: no corpora at {corpus_dir}", file=sys.stderr)
        sys.exit(2)

    # Score everything; collect (score, hw_total, cand) tuples
    all_scores = []
    rejected = 0
    accepted = 0
    for path in corpora:
        for s, r in score_corpus(path):
            if s["score"] is None:
                rejected += 1
            else:
                accepted += 1
                all_scores.append((s["score"], r["hw_total"], r.get("_cand", "?"), s))

    print(f"Validation: {accepted} accepted, {rejected} rejected (hard constraints)")
    print(f"Reject rate: {100*rejected/(accepted+rejected):.2f}%")

    all_scores.sort(key=lambda t: -t[0])  # high score first

    print(f"\n=== Top 20 by bridge_score ===")
    for sc, hw, cand, info in all_scores[:20]:
        bo = info["components"].get("bridge_polarity_ok", "?")
        print(f"  score={sc:6.2f}  hw={hw:3d}  cand={cand:40s}  bridge_ok={bo}")

    print(f"\n=== Bottom 5 (sanity) ===")
    for sc, hw, cand, info in all_scores[-5:]:
        print(f"  score={sc:6.2f}  hw={hw:3d}  cand={cand:40s}")

    # Discriminative test: are top-scored records actually sub-65?
    top100 = all_scores[:100]
    top100_sub65 = sum(1 for sc, hw, _, _ in top100 if hw < 65)
    print(f"\n=== Discriminative test ===")
    print(f"top-100 by score: {top100_sub65} are sub-65 ({100*top100_sub65/100:.0f}%)")

    # F371 4 sub-floor witnesses — what scores do they get?
    target_cands = ["bit3_m33ec77ca", "bit2_ma896ee41", "bit28_md1acca79", "bit13_m4e560940"]
    print(f"\n=== F371 4 sub-floor witnesses scores ===")
    for tc in target_cands:
        cand_scores = [(sc, hw) for sc, hw, c, info in all_scores if tc in c]
        if cand_scores:
            cand_scores.sort(key=lambda t: -t[0])
            sc, hw = cand_scores[0]
            rank = next(i for i, (s_, _, c, _) in enumerate(all_scores) if tc in c) + 1
            print(f"  {tc}: top score={sc:.2f} hw={hw} rank=#{rank}/{len(all_scores)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip(), formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--record", help="JSON record (single W-witness)")
    ap.add_argument("--corpus", help="Path to corpus JSONL")
    ap.add_argument("--kbit", type=int, help="kernel_bit override")
    ap.add_argument("--top", type=int, default=10, help="Top-K to print (corpus mode)")
    ap.add_argument("--validate", action="store_true", help="Run validation suite")
    args = ap.parse_args()

    if args.validate:
        validate()
        return

    if args.record:
        r = json.loads(args.record)
        s = bridge_score(r, args.kbit)
        print(json.dumps(s, indent=2))
        return

    if args.corpus:
        scored = score_corpus(args.corpus, args.kbit)
        scored.sort(key=lambda x: -(x[0]["score"] or -1e9))
        print(f"Top {args.top}:")
        for s, r in scored[:args.top]:
            print(f"  score={s['score']}  hw={r.get('hw_total')}  reject={s['reject_reason']}")
        return

    ap.print_help()


if __name__ == "__main__":
    main()
