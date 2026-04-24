#!/usr/bin/env python3
"""
append_run.py — Append a single run event to registry/runs.jsonl.

Computes git commit hash, timestamp, CNF sha256, and machine name automatically.
Validates bet_id and candidate_id against the registries.
Runs audit_cnf.py on the CNF and refuses to append if audit reports CRITICAL_MISMATCH.

Usage:
  python3 append_run.py \
    --bet sr61_n32 \
    --candidate cand_n32_bit10_m3304caa0_fill80000000 \
    --cnf cnfs_n32/sr61_n32_bit10_m3304caa0_fill80000000_enf0.cnf \
    --solver kissat \
    --solver-version 4.0.4 \
    --seed 5 \
    --status TIMEOUT \
    --wall 183600 \
    [--cpu 183100] \
    [--log path/to/log] \
    [--notes "free text"] \
    [--dry-run]
"""
import argparse
import datetime
import hashlib
import json
import os
import socket
import subprocess
import sys
import uuid

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required.", file=sys.stderr)
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
HUNT_ROOT = os.path.dirname(HERE)
REPO_ROOT = os.path.dirname(HUNT_ROOT)
RUNS_PATH = os.path.join(HUNT_ROOT, "registry", "runs.jsonl")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit():
    try:
        return subprocess.check_output(
            ["git", "-C", REPO_ROOT, "rev-parse", "HEAD"],
            stderr=subprocess.DEVNULL,
        ).decode().strip()
    except subprocess.CalledProcessError:
        return "unknown"


def load_yaml(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return yaml.safe_load(f)


def run_audit(cnf_path):
    """Returns the verdict string from audit_cnf.py."""
    audit_script = os.path.join(HERE, "audit_cnf.py")
    try:
        result = subprocess.run(
            [sys.executable, audit_script, cnf_path, "--json"],
            capture_output=True, text=True, timeout=30,
        )
        report = json.loads(result.stdout)
        return report["verdict"], report
    except Exception as e:
        return "AUDIT_FAILED", {"error": str(e)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bet", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--cnf", required=True)
    ap.add_argument("--solver", required=True)
    ap.add_argument("--solver-version", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--status", required=True,
                    choices=["SAT", "UNSAT", "TIMEOUT", "KILLED", "ERROR"])
    ap.add_argument("--wall", type=float, required=True, help="wall seconds")
    ap.add_argument("--cpu", type=float, default=None, help="CPU seconds")
    ap.add_argument("--encoder", default="unknown", help="encoder name/version")
    ap.add_argument("--kernel", default=None, help="kernel_id (looked up if omitted)")
    ap.add_argument("--log", default=None)
    ap.add_argument("--notes", default="")
    ap.add_argument("--allow-audit-failure", action="store_true",
                    help="Append even if audit returns CRITICAL_MISMATCH or UNKNOWN")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    # Validate cross-references
    mechanisms = load_yaml(os.path.join(HUNT_ROOT, "registry", "mechanisms.yaml")) or []
    candidates = load_yaml(os.path.join(HUNT_ROOT, "registry", "candidates.yaml")) or []
    bet_yaml_path = os.path.join(HUNT_ROOT, "bets", args.bet, "BET.yaml")
    if not os.path.exists(bet_yaml_path):
        print(f"ERROR: bet not found at {bet_yaml_path}", file=sys.stderr)
        sys.exit(2)
    candidate_ids = {c["id"] for c in candidates if isinstance(c, dict) and "id" in c}
    if args.candidate not in candidate_ids:
        print(f"ERROR: candidate `{args.candidate}` not found in candidates.yaml", file=sys.stderr)
        sys.exit(2)
    if not os.path.exists(args.cnf):
        cnf_abs = os.path.join(REPO_ROOT, args.cnf)
        if os.path.exists(cnf_abs):
            args.cnf = cnf_abs
        else:
            print(f"ERROR: CNF not found at {args.cnf}", file=sys.stderr)
            sys.exit(2)

    # Run audit on the CNF
    audit_verdict, audit_report = run_audit(args.cnf)
    if audit_verdict in ("CRITICAL_MISMATCH", "UNKNOWN") and not args.allow_audit_failure:
        print(f"AUDIT FAIL: verdict={audit_verdict}", file=sys.stderr)
        print(json.dumps(audit_report, indent=2), file=sys.stderr)
        print("Refusing to append. Pass --allow-audit-failure to override (NOT RECOMMENDED).",
              file=sys.stderr)
        sys.exit(1)

    # Compute auto fields
    cnf_sha = sha256_file(args.cnf)
    machine = socket.gethostname()
    git_sha = git_commit()
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    rid_short = uuid.uuid4().hex[:8]
    run_id = f"run_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{args.bet}_{args.solver}_seed{args.seed}_{rid_short}"

    record = {
        "run_id":         run_id,
        "timestamp":      ts,
        "bet_id":         args.bet,
        "candidate_id":   args.candidate,
        "kernel_id":      args.kernel,
        "command":        f"{args.solver} --seed={args.seed} {os.path.basename(args.cnf)}",
        "machine":        machine,
        "git_commit":     git_sha,
        "encoder":        args.encoder,
        "cnf_sha256":     cnf_sha,
        "sr_audit":       audit_verdict,
        "solver":         args.solver,
        "solver_version": args.solver_version,
        "seed":           args.seed,
        "status":         args.status,
        "wall_seconds":   args.wall,
        "cpu_seconds":    args.cpu,
        "artifacts":      [args.log] if args.log else [],
        "notes":          args.notes,
    }

    if args.dry_run:
        print("--dry-run, would append:")
        print(json.dumps(record, indent=2))
        sys.exit(0)

    with open(RUNS_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")
    print(f"Appended {run_id}")


if __name__ == "__main__":
    main()
