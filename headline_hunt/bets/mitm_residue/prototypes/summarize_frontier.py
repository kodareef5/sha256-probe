#!/usr/bin/env python3
"""Summarize reduced-N frontier records from scan summaries and seed logs."""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Iterable


def parse_summary_line(line: str) -> dict[str, object] | None:
    if not line.startswith("SUMMARY "):
        return None
    row: dict[str, object] = {}
    for part in line.split()[1:]:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        if "," in value:
            row[key] = value
            continue
        try:
            row[key] = int(value, 0)
        except ValueError:
            row[key] = value
    return row


def load_scan_rows(summary_globs: Iterable[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[tuple[object, object, str]] = set()
    for pattern in summary_globs:
        for filename in glob.glob(pattern):
            path = Path(filename)
            try:
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            except OSError:
                continue
            for line in lines:
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                key = (row.get("N"), row.get("sample_start"), str(row.get("log", "")))
                if key in seen:
                    continue
                seen.add(key)
                row["source"] = "scan"
                row["record"] = str(path)
                rows.append(row)
    return rows


def load_seed_rows(log_globs: Iterable[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for pattern in log_globs:
        for filename in glob.glob(pattern):
            path = Path(filename)
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            summary: dict[str, object] | None = None
            for line in text.splitlines():
                parsed = parse_summary_line(line)
                if parsed is not None:
                    summary = parsed
            if summary is None:
                continue
            summary["source"] = "seed"
            summary["record"] = str(path)
            rows.append(summary)
    return rows


def as_int(row: dict[str, object], key: str, default: int = 999) -> int:
    value = row.get(key, default)
    return value if isinstance(value, int) else default


def row_label(row: dict[str, object]) -> str:
    record = str(row.get("record", "?"))
    source = row.get("source", "?")
    n = row.get("N", "?")
    sample = row.get("sample_start", "?")
    return f"{source} N={n} sample_start={sample} {record}"


def print_rows(title: str, rows: list[dict[str, object]], keys: tuple[str, ...], limit: int) -> None:
    print(f"\n{title}:")
    if not rows:
        print("  none")
        return
    for row in rows[:limit]:
        metrics = " ".join(f"{key}={row.get(key, '?')}" for key in keys)
        tail_w1 = row.get("tail_W1", "?")
        joint_w1 = row.get("joint_W1", "?")
        r61_w1 = row.get("r61_W1", "?")
        print(f"  {metrics} tail_W1={tail_w1} joint_W1={joint_w1} r61_W1={r61_w1}")
        print(f"    {row_label(row)}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--summary-glob",
        action="append",
        default=["headline_hunt/bets/mitm_residue/results/runs/*/summaries.jsonl"],
    )
    parser.add_argument(
        "--log-glob",
        action="append",
        default=["headline_hunt/bets/mitm_residue/results/runs/*.log"],
    )
    parser.add_argument("--only-n", type=int, default=14)
    parser.add_argument("--top", type=int, default=12)
    args = parser.parse_args()

    rows = load_scan_rows(args.summary_glob) + load_seed_rows(args.log_glob)
    rows = [row for row in rows if as_int(row, "N") == args.only_n]
    seed_rows = [row for row in rows if row.get("source") == "seed"]
    joint_rows = [row for row in seed_rows if "best_joint" in row]

    print(f"rows={len(rows)} scan_rows={len(rows) - len(seed_rows)} seed_rows={len(seed_rows)}")
    print(f"joint_rows={len(joint_rows)}")

    print_rows(
        "best_tail",
        sorted(rows, key=lambda row: (as_int(row, "best_tail"), as_int(row, "tail_r61"))),
        ("best_tail", "tail_r61", "best_r61"),
        args.top,
    )
    print_rows(
        "best_r61",
        sorted(rows, key=lambda row: (as_int(row, "best_r61"), as_int(row, "best_tail"))),
        ("best_r61", "best_tail", "tail_r61"),
        args.top,
    )
    print_rows(
        "best_true_joint_seed",
        sorted(
            joint_rows,
            key=lambda row: (
                as_int(row, "best_joint"),
                as_int(row, "joint_max"),
                as_int(row, "joint_tail"),
                as_int(row, "joint_r61"),
            ),
        ),
        ("best_joint", "joint_max", "joint_tail", "joint_r61"),
        args.top,
    )
    print_rows(
        "best_tail_witness_joint",
        sorted(
            rows,
            key=lambda row: (
                as_int(row, "best_tail") + as_int(row, "tail_r61"),
                max(as_int(row, "best_tail"), as_int(row, "tail_r61")),
            ),
        ),
        ("best_tail", "tail_r61", "best_r61"),
        args.top,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
