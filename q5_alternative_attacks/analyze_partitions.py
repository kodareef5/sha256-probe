#!/usr/bin/env python3
"""
analyze_partitions.py — Analyze partition solver results as they come in.

Reads the partition log file and produces real-time statistics:
- How many partitions resolved (SAT/UNSAT/TIMEOUT)?
- What's the UNSAT rate? (If high → problem is likely UNSAT overall)
- What's the average solve time for resolved partitions?
- Are some partition values faster than others? (structure detection)

Usage: python3 analyze_partitions.py <log_file>
"""

import sys, re
from collections import Counter


def analyze(logfile):
    results = []
    with open(logfile) as f:
        for line in f:
            m = re.match(r'\s*\[\s*(\d+)/(\d+)\]\s+(\w+)\s+in\s+([\d.]+)s', line)
            if m:
                pval = int(m.group(1))
                total = int(m.group(2))
                status = m.group(3)
                time_s = float(m.group(4))
                results.append((pval, status, time_s))

    if not results:
        print("No results yet.")
        return

    total = max(r[0] for r in results) + 1 if results else 0
    n_total = len(results)
    counts = Counter(r[1] for r in results)

    print(f"Partition Analysis: {n_total} resolved")
    print(f"  SAT:     {counts.get('SAT', 0)}")
    print(f"  UNSAT:   {counts.get('UNSAT', 0)}")
    print(f"  TIMEOUT: {counts.get('TIMEOUT', 0)}")
    print()

    if counts.get('SAT', 0) > 0:
        print("*** SAT FOUND! Check log for collision details. ***")
        sat_results = [r for r in results if r[1] == 'SAT']
        for pval, _, t in sat_results:
            print(f"  Partition {pval}: SAT in {t:.1f}s")
        return

    unsats = [r for r in results if r[1] == 'UNSAT']
    timeouts = [r for r in results if r[1] == 'TIMEOUT']

    if unsats:
        avg_unsat_time = sum(r[2] for r in unsats) / len(unsats)
        print(f"  UNSAT avg time: {avg_unsat_time:.1f}s")
        print(f"  UNSAT fastest: {min(r[2] for r in unsats):.1f}s")
        print(f"  UNSAT slowest: {max(r[2] for r in unsats):.1f}s")

    if timeouts:
        print(f"  TIMEOUT at: {timeouts[0][2]:.0f}s")

    unsat_rate = counts.get('UNSAT', 0) / n_total if n_total > 0 else 0
    print(f"\n  UNSAT rate: {unsat_rate:.1%}")
    if unsat_rate > 0.9:
        print("  High UNSAT rate suggests the overall problem is likely UNSAT.")
    elif unsat_rate > 0.5:
        print("  Mixed results — some partitions harder than others.")
    elif unsat_rate < 0.1 and counts.get('TIMEOUT', 0) > 0:
        print("  Mostly timeouts — partitions too large, need more bits.")

    # Check for structure: are partition values near each other similar?
    if len(unsats) > 3:
        vals = sorted(r[0] for r in unsats)
        print(f"\n  UNSAT partition values: {vals[:20]}{'...' if len(vals)>20 else ''}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_partitions.py <log_file>")
        sys.exit(1)
    analyze(sys.argv[1])
