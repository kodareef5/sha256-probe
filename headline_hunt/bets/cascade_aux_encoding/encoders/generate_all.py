#!/usr/bin/env python3
"""
generate_all.py — Drive cascade_aux_encoder.py across every candidate in the
registry. For each (candidate, mode) pair, build the CNF, audit it, and write
a manifest row. Output: a markdown table the fleet can use as the baseline
for what the encoder produces today.

Use cases:
  - Smoke test the encoder breadth (catches candidates the encoder rejects
    or candidates that produce out-of-fingerprint sizes).
  - Reference manifest committed to the repo so encoder drift becomes a
    visible diff.
  - Pre-flight: when a fleet machine wants to run a kissat sweep across
    candidates, this produces all the aux CNFs in one go.

Default behavior:
  - Reads candidates from headline_hunt/registry/candidates.yaml.
  - Generates both expose and force modes for each candidate.
  - Writes CNFs to a tmp dir (not committed) — the artifact is the manifest.
  - Audits each CNF and records verdict.
  - Writes manifest to bets/cascade_aux_encoding/results/aux_encoder_manifest.md.

Usage:
    python3 generate_all.py [--keep-cnfs DIR]   # default: tmp dir, deleted at end
    python3 generate_all.py --candidates ID1 ID2 ...    # subset
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required.", file=sys.stderr); sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
ENCODER = os.path.join(HERE, "cascade_aux_encoder.py")
AUDIT = os.path.join(REPO, "headline_hunt", "infra", "audit_cnf.py")
CANDIDATES = os.path.join(REPO, "headline_hunt", "registry", "candidates.yaml")
DEFAULT_MANIFEST = os.path.join(REPO, "headline_hunt", "bets",
                                "cascade_aux_encoding", "results",
                                "aux_encoder_manifest.md")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def encode_one(cand, mode, out_dir):
    """Generate one aux CNF. Returns (path, summary_dict) or (None, error_str)."""
    bit = cand["kernel"]["bit"]
    m0 = cand["m0"]
    fill = cand["fill"]
    # sr level: MSB candidates here are sr=60 verified, true_sr61 candidates are sr=61.
    # Use the candidate's id prefix to infer.
    sr = 60 if cand["id"].startswith("cand_n32_msb_") else 61

    # Filename must start with `aux_<mode>_sr<sr>` so audit_cnf.py's pattern catches it.
    out_path = os.path.join(out_dir, f"aux_{mode}_sr{sr}_{cand['id']}.cnf")
    cmd = [sys.executable, ENCODER,
           "--sr", str(sr),
           "--m0", m0,
           "--fill", fill,
           "--kernel-bit", str(bit),
           "--mode", mode,
           "--out", out_path,
           "--quiet"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return None, "TIMEOUT"
    if r.returncode != 0:
        return None, f"ENCODER_FAILED: {r.stderr.strip()[:200]}"
    return out_path, {"sr": sr}


def audit_one(path):
    """Returns audit JSON dict or None on failure."""
    try:
        r = subprocess.run([sys.executable, AUDIT, path, "--json"],
                           capture_output=True, text=True, timeout=30)
        return json.loads(r.stdout)
    except Exception as e:
        return {"verdict": "AUDIT_FAILED", "error": str(e)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-cnfs", default=None,
                    help="Directory to save CNFs in (default: tmp, deleted at end)")
    ap.add_argument("--candidates", nargs="*", default=None,
                    help="Restrict to these candidate IDs (default: all)")
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST,
                    help=f"Output manifest path (default: {DEFAULT_MANIFEST})")
    ap.add_argument("--modes", nargs="+", default=["expose", "force"],
                    choices=["expose", "force"])
    args = ap.parse_args()

    with open(CANDIDATES) as f:
        candidates = yaml.safe_load(f)

    if args.candidates:
        candidates = [c for c in candidates if c["id"] in args.candidates]

    out_dir = args.keep_cnfs or tempfile.mkdtemp(prefix="aux_gen_")
    os.makedirs(out_dir, exist_ok=True)
    cleanup = args.keep_cnfs is None

    print(f"Generating {len(candidates)} candidates × {len(args.modes)} modes "
          f"= {len(candidates) * len(args.modes)} CNFs into {out_dir}",
          file=sys.stderr)

    rows = []
    failures = 0
    confirmed = 0
    inferred = 0
    other = 0

    for cand in candidates:
        for mode in args.modes:
            path, info = encode_one(cand, mode, out_dir)
            if path is None:
                rows.append({
                    "id": cand["id"], "mode": mode, "sr": "?",
                    "vars": "-", "clauses": "-", "verdict": "ENCODE_FAIL",
                    "matches": info, "sha": "-",
                })
                failures += 1
                continue
            audit = audit_one(path)
            verdict = audit.get("verdict", "?")
            if verdict == "CONFIRMED": confirmed += 1
            elif verdict == "INFERRED": inferred += 1
            else: other += 1
            rows.append({
                "id": cand["id"], "mode": mode, "sr": info["sr"],
                "vars": audit.get("n_vars", "-"),
                "clauses": audit.get("n_clauses", "-"),
                "verdict": verdict,
                "matches": ",".join(audit.get("matched_fingerprints", [])) or "-",
                "sha": sha256_file(path)[:12],
            })

    # Write manifest
    os.makedirs(os.path.dirname(args.manifest), exist_ok=True)
    import datetime
    with open(args.manifest, "w") as f:
        f.write(f"# Cascade-aux encoder manifest — {datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}\n\n")
        f.write(f"Generated by `generate_all.py` over `registry/candidates.yaml`. "
                f"This is the **baseline** of what the encoder produces today; "
                f"future runs that drift size or verdict show up in the diff.\n\n")
        f.write(f"- Candidates: {len(candidates)}\n")
        f.write(f"- Modes: {', '.join(args.modes)}\n")
        f.write(f"- Total CNFs generated: {len(rows)}\n")
        f.write(f"- CONFIRMED: {confirmed}\n")
        f.write(f"- INFERRED:  {inferred}\n")
        f.write(f"- ENCODE_FAIL / OTHER: {failures + other}\n\n")
        f.write("| Candidate | Mode | sr | vars | clauses | Verdict | Matches | sha256 (12) |\n")
        f.write("|---|---|---:|---:|---:|---|---|---|\n")
        for r in rows:
            f.write(f"| `{r['id']}` | {r['mode']} | {r['sr']} | {r['vars']} | {r['clauses']} | "
                    f"{r['verdict']} | {r['matches']} | `{r['sha']}` |\n")

    print(f"Wrote {args.manifest}", file=sys.stderr)
    print(f"  CONFIRMED: {confirmed}  INFERRED: {inferred}  OTHER/FAIL: {failures + other}",
          file=sys.stderr)

    if cleanup:
        import shutil
        shutil.rmtree(out_dir, ignore_errors=True)

    sys.exit(0 if (failures + inferred + other) == 0 else 1)


if __name__ == "__main__":
    main()
