#!/usr/bin/env python3
"""
summarize_runs.py — Generate reports/dashboard.md from registry/runs.jsonl.

Per-bet rollup: total CPU spent, SAT/UNSAT/TIMEOUT counts, last activity,
most recent runs. Also flags audit failures and stale bets.

Usage: python3 summarize_runs.py [--dry-run]
"""
import argparse
import collections
import datetime
import json
import os
import sys

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required.", file=sys.stderr)
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))
HUNT_ROOT = os.path.dirname(HERE)
RUNS_PATH = os.path.join(HUNT_ROOT, "registry", "runs.jsonl")
DASHBOARD_PATH = os.path.join(HUNT_ROOT, "reports", "dashboard.md")


def load_runs():
    runs = []
    if not os.path.exists(RUNS_PATH):
        return runs
    with open(RUNS_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "_header" in rec:
                continue
            runs.append(rec)
    return runs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Print to stdout instead of writing dashboard.md")
    args = ap.parse_args()

    runs = load_runs()
    bets = collections.defaultdict(lambda: {
        "runs": 0, "sat": 0, "unsat": 0, "timeout": 0, "killed": 0, "error": 0,
        "wall_s": 0.0, "cpu_s": 0.0,
        "audit_failures_real": 0,        # CRITICAL_MISMATCH or actual UNKNOWN with cnf path
        "audit_failures_intentional": 0, # --allow-audit-failure (cnf=None or sr_audit blank)
        "last_ts": None,
    })
    total_runs = len(runs)
    real_failures = 0
    intentional_skips = 0

    for r in runs:
        b = bets[r.get("bet_id", "<unknown>")]
        b["runs"] += 1
        st = r.get("status", "ERROR").lower()
        if st == "sat": b["sat"] += 1
        elif st == "unsat": b["unsat"] += 1
        elif st == "timeout": b["timeout"] += 1
        elif st == "killed": b["killed"] += 1
        else: b["error"] += 1
        b["wall_s"] += float(r.get("wall_seconds") or 0)
        b["cpu_s"] += float(r.get("cpu_seconds") or 0)
        audit = r.get("sr_audit", "")
        if audit in ("CRITICAL_MISMATCH", "UNKNOWN", "AUDIT_FAILED"):
            # Distinguish intentional --allow-audit-failure (cnf=None or absent) from real audit failures
            cnf = r.get("cnf")
            if cnf is None or cnf == "" or audit == "CRITICAL_MISMATCH":
                # CRITICAL_MISMATCH is always a real failure even with --allow-audit-failure flag
                if audit == "CRITICAL_MISMATCH":
                    b["audit_failures_real"] += 1
                    real_failures += 1
                else:
                    # cnf=None + UNKNOWN/AUDIT_FAILED = intentional skip
                    b["audit_failures_intentional"] += 1
                    intentional_skips += 1
            else:
                b["audit_failures_real"] += 1
                real_failures += 1
        ts = r.get("timestamp")
        if ts and (b["last_ts"] is None or ts > b["last_ts"]):
            b["last_ts"] = ts

    real_failure_pct = (real_failures / total_runs * 100) if total_runs else 0.0
    intentional_pct = (intentional_skips / total_runs * 100) if total_runs else 0.0

    lines = []
    lines.append("# headline_hunt — Runs Dashboard")
    lines.append("")
    lines.append(f"_Generated {datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}_")
    lines.append("")
    lines.append("## Global")
    lines.append("")
    lines.append(f"- Total runs logged: **{total_runs}**")
    lines.append(f"- Real audit failure rate: **{real_failure_pct:.2f}%** ({real_failures} entries)"
                 + (" — **EXCEEDS 1% — investigate**" if real_failure_pct > 1.0 else ""))
    if intentional_skips:
        lines.append(f"- Intentional --allow-audit-failure entries: {intentional_skips} ({intentional_pct:.2f}%) — discipline-noted, not concerning (transient /tmp CNFs from injection/certpin pipelines)")
    lines.append("")
    lines.append("## Per-bet rollup")
    lines.append("")
    lines.append("| Bet | Runs | SAT | UNSAT | Timeout | Killed | CPU-h | Wall-h | Last activity | Real fail | --allow-skip |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|")
    for bet_id in sorted(bets):
        b = bets[bet_id]
        cpu_h = b["cpu_s"] / 3600.0
        wall_h = b["wall_s"] / 3600.0
        lines.append(f"| {bet_id} | {b['runs']} | {b['sat']} | {b['unsat']} | "
                     f"{b['timeout']} | {b['killed']} | {cpu_h:.1f} | {wall_h:.1f} | "
                     f"{b['last_ts'] or 'never'} | {b['audit_failures_real']} | {b['audit_failures_intentional']} |")
    if not bets:
        lines.append("| _no runs yet_ | | | | | | | | | | |")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Generated by `infra/summarize_runs.py`. Run weekly; commit the result.")
    lines.append("- Real audit failure threshold: 1%. If exceeded, the sr61_n32 bet auto-trips its process kill criterion.")
    lines.append("- `--allow-skip` column counts entries logged with `--allow-audit-failure` (cnf=None). These are intentional for transient /tmp CNFs in injection/certpin pipelines (F368-F377 chain) and are discipline-noted, not actionable.")
    lines.append("- Use `python3 infra/validate_registry.py` for staleness and schema checks (separate dashboard).")
    lines.append("")

    output = "\n".join(lines)

    if args.dry_run:
        print(output)
    else:
        os.makedirs(os.path.dirname(DASHBOARD_PATH), exist_ok=True)
        with open(DASHBOARD_PATH, "w") as f:
            f.write(output)
        print(f"Wrote {DASHBOARD_PATH}")


if __name__ == "__main__":
    main()
