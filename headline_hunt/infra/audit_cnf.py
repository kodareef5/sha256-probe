#!/usr/bin/env python3
"""
audit_cnf.py — CNF sr-level audit. The script that should have existed
before the 2026-04-18 disaster.

Usage:
  python3 audit_cnf.py <path/to/file.cnf> [--strict]

Output: structured report with sr_level inference and a confidence flag:
  CONFIRMED      — filename + fingerprint agree
  INFERRED       — filename only, no fingerprint match (need human review)
  CRITICAL_MISMATCH — filename and fingerprint disagree (DO NOT USE)
  UNKNOWN        — cannot determine

Exit codes:
  0 = CONFIRMED or INFERRED (both usable; INFERRED warns)
  1 = CRITICAL_MISMATCH or UNKNOWN (do not queue this CNF)

This is the gatekeeper. Trust the audit output, not the filename.
"""
import argparse
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required. pip install pyyaml", file=sys.stderr)
    sys.exit(2)


HERE = os.path.dirname(os.path.abspath(__file__))
FINGERPRINTS_PATH = os.path.join(HERE, "cnf_fingerprints.yaml")


FILENAME_PATTERNS = [
    # TRUE sr=61 N=32 enf0 encoding
    (re.compile(r"^sr61_n32_bit(?P<bit>\d+)_m(?P<m0>[0-9a-f]+)_fill(?P<fill>[0-9a-f]+)_enf0\.cnf$"),
     {"sr_level": 61, "n": 32, "encoder_variant": "cascade_enf0"}),
    # sr=61 with full enforcement (variant naming)
    (re.compile(r"^sr61_n32_bit(?P<bit>\d+)_m(?P<m0>[0-9a-f]+)_fill(?P<fill>[0-9a-f]+)_full\.cnf$"),
     {"sr_level": 61, "n": 32, "encoder_variant": "cascade_full"}),
    # sr=61 cascade explicit naming
    (re.compile(r"^sr61_cascade_m(?P<m0>[0-9a-f]+)_f(?P<fill>[0-9a-f]+)_bit(?P<bit>\d+)\.cnf$"),
     {"sr_level": 61, "n": 32, "encoder_variant": "cascade_explicit"}),
    # TRUE_sr61_* — explicit true sr=61 marking
    (re.compile(r"^TRUE_sr61_.*\.cnf$"),
     {"sr_level": 61, "n": 32, "encoder_variant": "true_sr61_explicit"}),
    # sr=60 patterns
    (re.compile(r"^sr60_.*\.cnf$"),
     {"sr_level": 60, "n": None, "encoder_variant": "sr60_unspecified"}),
]


def parse_filename(filename):
    """Return claimed-metadata dict from filename, or None if unrecognized."""
    for pat, base_meta in FILENAME_PATTERNS:
        m = pat.match(filename)
        if m:
            meta = dict(base_meta)
            for k, v in m.groupdict().items():
                if k in ("bit",):
                    meta[k] = int(v)
                elif k in ("m0", "fill"):
                    meta[k] = "0x" + v
                else:
                    meta[k] = v
            return meta
    return None


def parse_dimacs_header(path):
    """Return (n_vars, n_clauses) from the `p cnf` line, or (None, None)."""
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("c "):
                continue
            if line.startswith("p cnf"):
                parts = line.split()
                if len(parts) >= 4:
                    return int(parts[2]), int(parts[3])
                return None, None
            # Stop at first non-comment, non-p line
            if line and not line.startswith("c"):
                return None, None
    return None, None


def load_fingerprints():
    if not os.path.exists(FINGERPRINTS_PATH):
        return []
    with open(FINGERPRINTS_PATH) as f:
        data = yaml.safe_load(f)
    return data or []


def match_fingerprint(claimed, n_vars, n_clauses, fingerprints):
    """Return (best_match_or_none, list_of_alternative_matches)."""
    matches = []
    for fp in fingerprints:
        if fp.get("encoder_variant") != claimed.get("encoder_variant"):
            continue
        if fp.get("sr_level") != claimed.get("sr_level"):
            continue
        if claimed.get("n") is not None and fp.get("n") != claimed.get("n"):
            continue
        vmin, vmax = fp["vars_range"]
        cmin, cmax = fp["clauses_range"]
        if vmin <= n_vars <= vmax and cmin <= n_clauses <= cmax:
            matches.append(fp)
    # Also look for cross-sr-level matches that would be a disaster signal
    cross_matches = []
    for fp in fingerprints:
        if fp.get("sr_level") == claimed.get("sr_level"):
            continue
        vmin, vmax = fp["vars_range"]
        cmin, cmax = fp["clauses_range"]
        if vmin <= n_vars <= vmax and cmin <= n_clauses <= cmax:
            cross_matches.append(fp)
    return matches, cross_matches


def audit(path, strict=False):
    filename = os.path.basename(path)
    report = {
        "file": path,
        "filename": filename,
        "claimed": None,
        "n_vars": None,
        "n_clauses": None,
        "matched_fingerprints": [],
        "cross_sr_matches": [],
        "verdict": "UNKNOWN",
        "warnings": [],
    }

    claimed = parse_filename(filename)
    if claimed is None:
        report["verdict"] = "UNKNOWN"
        report["warnings"].append(f"Filename pattern not recognized: {filename}")
        return report
    report["claimed"] = claimed

    n_vars, n_clauses = parse_dimacs_header(path)
    if n_vars is None:
        report["warnings"].append("Could not parse `p cnf` header")
        report["verdict"] = "UNKNOWN"
        return report
    report["n_vars"] = n_vars
    report["n_clauses"] = n_clauses

    fingerprints = load_fingerprints()
    matches, cross_matches = match_fingerprint(claimed, n_vars, n_clauses, fingerprints)
    report["matched_fingerprints"] = [m["bucket_id"] for m in matches]
    report["cross_sr_matches"] = [m["bucket_id"] for m in cross_matches]

    if cross_matches:
        report["verdict"] = "CRITICAL_MISMATCH"
        report["warnings"].append(
            f"DANGER: var/clause count matches a DIFFERENT sr-level fingerprint "
            f"({[m['bucket_id'] for m in cross_matches]}). "
            f"Filename claims sr={claimed['sr_level']} but content suggests otherwise. "
            "DO NOT USE."
        )
    elif matches:
        report["verdict"] = "CONFIRMED"
    else:
        report["verdict"] = "INFERRED"
        report["warnings"].append(
            f"No fingerprint match for ({claimed['sr_level']}, {claimed.get('n')}, "
            f"{claimed.get('encoder_variant')}) at vars={n_vars}, clauses={n_clauses}. "
            "Add this combination to cnf_fingerprints.yaml after human review."
        )

    if strict and report["verdict"] != "CONFIRMED":
        report["warnings"].append("--strict mode: only CONFIRMED is acceptable.")

    return report


def main():
    ap = argparse.ArgumentParser(description="Audit a CNF for sr-level consistency")
    ap.add_argument("cnf", help="Path to .cnf file")
    ap.add_argument("--strict", action="store_true",
                    help="Exit non-zero unless verdict is CONFIRMED")
    ap.add_argument("--json", action="store_true",
                    help="Emit JSON instead of human-readable")
    args = ap.parse_args()

    if not os.path.exists(args.cnf):
        print(f"ERROR: file not found: {args.cnf}", file=sys.stderr)
        sys.exit(2)

    report = audit(args.cnf, strict=args.strict)

    if args.json:
        import json
        print(json.dumps(report, indent=2))
    else:
        print(f"Audit:  {report['file']}")
        if report["claimed"]:
            print(f"  Claimed: sr={report['claimed']['sr_level']}  "
                  f"n={report['claimed'].get('n')}  "
                  f"encoder={report['claimed'].get('encoder_variant')}  "
                  f"bit={report['claimed'].get('bit')}  "
                  f"m0={report['claimed'].get('m0')}  "
                  f"fill={report['claimed'].get('fill')}")
        print(f"  DIMACS:  vars={report['n_vars']}  clauses={report['n_clauses']}")
        if report["matched_fingerprints"]:
            print(f"  Matches: {report['matched_fingerprints']}")
        if report["cross_sr_matches"]:
            print(f"  CROSS-SR MATCHES (DISASTER FLAG): {report['cross_sr_matches']}")
        print(f"  VERDICT: {report['verdict']}")
        for w in report["warnings"]:
            print(f"  WARN: {w}")

    if report["verdict"] in ("CRITICAL_MISMATCH", "UNKNOWN"):
        sys.exit(1)
    if args.strict and report["verdict"] != "CONFIRMED":
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
