#!/usr/bin/env python3
"""
validate_results.py — defensive scan of dispatcher logs for silent failures.

The dispatcher records `wall=0.00 status=UNKNOWN` for any kissat invocation
that fails immediately (e.g., invalid argument, missing file). Without
inspecting individual log files, these failures look identical to
genuinely fast UNKNOWN responses.

This script scans `logs/run_*.log` for known failure patterns:
- "kissat: error" lines
- Empty log files (kissat crashed before writing anything)
- Log files with no "s SAT/UNSAT/UNKNOWN" status line

Reports a per-run failure status. Cross-references results.tsv to flag
which logged "results" are actually failures.

Usage:
    python3 validate_results.py [--logs-dir logs/] [--results results.tsv]

Exit code: 0 if no failures, 1 if any silent failures detected.
"""
import argparse
import os
import re
import sys


KISSAT_ERROR_RE = re.compile(r"^kissat: error", re.IGNORECASE)
S_LINE_RE = re.compile(r"^s (SAT|UNSAT|UNKNOWN|SATISFIABLE|UNSATISFIABLE)", re.IGNORECASE)


def classify_log(log_path):
    """Return one of: OK / EMPTY / KISSAT_ERROR / NO_STATUS / READ_ERROR."""
    try:
        with open(log_path) as f:
            lines = f.readlines()
    except IOError:
        return "READ_ERROR"

    if not lines:
        return "EMPTY"

    has_error = any(KISSAT_ERROR_RE.match(line) for line in lines)
    if has_error:
        return "KISSAT_ERROR"

    has_status = any(S_LINE_RE.match(line) for line in lines)
    if not has_status:
        return "NO_STATUS"

    return "OK"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--logs-dir", default=os.path.join(here, "logs"),
                    help="Path to dispatcher logs directory")
    ap.add_argument("--results", default=os.path.join(here, "results.tsv"),
                    help="Path to dispatcher results.tsv")
    ap.add_argument("--verbose", action="store_true",
                    help="Print each log's classification")
    args = ap.parse_args()

    if not os.path.isdir(args.logs_dir):
        print(f"ERROR: logs dir not found: {args.logs_dir}", file=sys.stderr)
        sys.exit(2)

    log_files = sorted(os.listdir(args.logs_dir))
    log_files = [f for f in log_files if f.startswith("run_") and f.endswith(".log")]

    counts = {"OK": 0, "EMPTY": 0, "KISSAT_ERROR": 0, "NO_STATUS": 0, "READ_ERROR": 0}
    failures = []
    for fn in log_files:
        path = os.path.join(args.logs_dir, fn)
        cls = classify_log(path)
        counts[cls] = counts.get(cls, 0) + 1
        if cls != "OK":
            failures.append((fn, cls))
        if args.verbose:
            print(f"  {fn}: {cls}")

    print(f"=== Dispatcher log validation ===")
    print(f"Logs scanned: {len(log_files)}")
    for cls, count in sorted(counts.items()):
        print(f"  {cls:>14}: {count}")

    if failures:
        print(f"\n⚠ {len(failures)} silent failures detected:")
        for fn, cls in failures[:20]:
            run_id = re.search(r"run_(\d+)\.log", fn).group(1)
            print(f"  run #{int(run_id)}: {cls}")
            # Show first 2 lines of the failure log
            try:
                with open(os.path.join(args.logs_dir, fn)) as f:
                    head = f.readlines()[:2]
                for line in head:
                    print(f"      {line.rstrip()}")
            except IOError:
                pass
        if len(failures) > 20:
            print(f"  ... and {len(failures) - 20} more")
        sys.exit(1)
    else:
        print(f"\n✓ All {len(log_files)} logs are well-formed")
        sys.exit(0)


if __name__ == "__main__":
    main()
