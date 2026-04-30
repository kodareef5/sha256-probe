#!/usr/bin/env python3
"""
diff_cnf.py — compare two CNF files for structural compatibility.

When measuring a Δ% conflict-reduction (or any solver-output delta) across
two CNFs, you need them to be **structurally compatible**: same encoder
version, same n_vars (modulo small injection overhead), same n_clauses
(modulo prepended/appended injection clauses).

The 2026-04-30 F368 retraction was caused by old-encoder baselines
(12592 vars) being compared against new-encoder injected CNFs (13220 vars).
A 628-var difference contaminated the Δ%. This tool flags that pattern
*before* you measure.

Usage:
  python3 diff_cnf.py BASELINE.cnf TREATMENT.cnf
  python3 diff_cnf.py BASELINE.cnf TREATMENT.cnf --json

Exit codes:
  0 = compatible (var/clause diff within threshold; encoder header matches)
  1 = INCOMPATIBLE (structural mismatch likely confounds Δ%)
  2 = parse error or missing file
"""
import argparse
import json
import os
import re
import sys


def read_cnf_meta(path):
    """Returns dict with n_vars, n_clauses, encoder_header (1st `c` line),
    n_body_clauses (counted), and the first 8 clauses (for spot-check).
    """
    meta = {
        "path": path,
        "n_vars": None,
        "n_clauses_declared": None,
        "n_body_clauses_counted": 0,
        "encoder_header": None,
        "first_clauses": [],
    }
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        for L in f:
            s = L.rstrip("\n")
            if s.startswith("c") and meta["encoder_header"] is None:
                meta["encoder_header"] = s
                continue
            if s.startswith("p"):
                m = re.match(r"^p\s+cnf\s+(\d+)\s+(\d+)", s)
                if m:
                    meta["n_vars"] = int(m.group(1))
                    meta["n_clauses_declared"] = int(m.group(2))
                continue
            if not s or s.startswith("c"):
                continue
            meta["n_body_clauses_counted"] += 1
            if len(meta["first_clauses"]) < 8:
                meta["first_clauses"].append(s)
    return meta


def compare(b, t, var_threshold_pct=1.0):
    """Return (compatible: bool, findings: list[str]).
    var_threshold_pct: pct difference in n_vars above which to flag.
    """
    findings = []
    if b is None or t is None:
        return False, ["one or both files missing"]

    # n_vars check
    if b["n_vars"] is None or t["n_vars"] is None:
        findings.append(f"n_vars missing in {'baseline' if b['n_vars'] is None else 'treatment'} (no `p cnf` line)")
        return False, findings
    bv, tv = b["n_vars"], t["n_vars"]
    pct = abs(tv - bv) / bv * 100.0 if bv else 100.0
    if pct > var_threshold_pct:
        findings.append(
            f"n_vars MISMATCH: baseline={bv} treatment={tv} (Δ={tv-bv:+d}, {pct:.2f}% > {var_threshold_pct}% threshold) "
            f"— LIKELY ENCODER-VERSION CONFOUND"
        )
    elif tv != bv:
        findings.append(f"n_vars minor diff: baseline={bv} treatment={tv} (Δ={tv-bv:+d}, {pct:.2f}%) — within threshold")

    # n_clauses sanity (treatment may legitimately have a few extra injected clauses)
    bc, tc = b["n_clauses_declared"], t["n_clauses_declared"]
    if bc is not None and tc is not None:
        delta = tc - bc
        if delta < 0:
            findings.append(f"n_clauses: treatment has FEWER clauses ({tc}) than baseline ({bc}) — unexpected; investigate")
        elif delta > 200:
            findings.append(f"n_clauses: treatment has {delta} more clauses than baseline (large injection? legitimate but verify)")
        # else: small +Δ is normal for injection

    # body-clause count vs declared
    for label, m in [("baseline", b), ("treatment", t)]:
        if m["n_clauses_declared"] is not None and m["n_body_clauses_counted"] != m["n_clauses_declared"]:
            findings.append(f"{label}: declared {m['n_clauses_declared']} clauses but counted {m['n_body_clauses_counted']} body lines — DIMACS malformed")

    # encoder header comparison (soft warning unless both present and differ)
    bh = (b["encoder_header"] or "").strip()
    th = (t["encoder_header"] or "").strip()
    if bh and th and bh != th:
        findings.append(f"encoder_header DIFFERS: baseline='{bh[:60]}' treatment='{th[:60]}' — VERIFY same encoder version")
    elif (bh and not th) or (not bh and th):
        # one side stripped comments (common for clause-injected files); soft note
        which = "baseline" if not bh else "treatment"
        findings.append(f"note: encoder_header absent in {which} (likely clause-injected file with stripped comments) — not necessarily a confound if n_vars matches")

    # spot-check first clause body (informational unless n_vars also differs)
    if b["first_clauses"][:3] != t["first_clauses"][:3]:
        findings.append(
            "note: first 3 body clauses differ — expected if treatment uses different encoder OR if injection inserts at the front"
        )

    # decision: compatible iff no hard-fail findings.
    # Hard-fail keywords flag confounds; "note:" / "info:" / "minor diff" are soft.
    hard_fail_keywords = ("MISMATCH", "MALFORMED", "FEWER", "header DIFFERS")
    compatible = not any(any(kw in f for kw in hard_fail_keywords) for f in findings)
    return compatible, findings


def main():
    ap = argparse.ArgumentParser(description=__doc__.strip(), formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("baseline")
    ap.add_argument("treatment")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--var-threshold-pct", type=float, default=1.0,
                    help="pct n_vars difference above which to flag as MISMATCH (default 1.0)")
    args = ap.parse_args()

    b = read_cnf_meta(args.baseline)
    t = read_cnf_meta(args.treatment)
    compatible, findings = compare(b, t, args.var_threshold_pct)

    if args.json:
        print(json.dumps({
            "compatible": compatible,
            "baseline": b,
            "treatment": t,
            "findings": findings,
            "var_threshold_pct": args.var_threshold_pct,
        }, indent=2))
    else:
        print(f"baseline:  {args.baseline}")
        if b:
            print(f"  vars={b['n_vars']} clauses_declared={b['n_clauses_declared']} body_counted={b['n_body_clauses_counted']}")
            print(f"  header: {(b['encoder_header'] or '<none>')[:100]}")
        print(f"treatment: {args.treatment}")
        if t:
            print(f"  vars={t['n_vars']} clauses_declared={t['n_clauses_declared']} body_counted={t['n_body_clauses_counted']}")
            print(f"  header: {(t['encoder_header'] or '<none>')[:100]}")
        print()
        if not findings:
            print("VERDICT: compatible (no findings)")
        else:
            print("VERDICT:", "compatible" if compatible else "INCOMPATIBLE")
            hard_fail_keywords = ("MISMATCH", "MALFORMED", "FEWER", "header DIFFERS")
            for f in findings:
                marker = "FAIL" if any(kw in f for kw in hard_fail_keywords) else "info"
                print(f"  [{marker}] {f}")
    sys.exit(0 if compatible else 1)


if __name__ == "__main__":
    main()
