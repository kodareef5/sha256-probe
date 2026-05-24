#!/usr/bin/env python3
"""Summarize second-stage local-refinement logs."""

from __future__ import annotations

import argparse
import glob
import re
from pathlib import Path
from typing import Iterable


SUMMARY_RE = re.compile(r"^SUMMARY (?P<body>.*)$")
REFINE_BUDGET_RE = re.compile(
    r"\s+budget=(?P<budget>\d+) tested=(?P<tested>\d+) D60=0=(?P<d0>\d+) "
    r"collisions=(?P<collisions>\d+) seed_inserts=(?P<seed_inserts>\d+) "
    r"prefix_enums=(?P<prefix_enums>\d+)"
)
REFINED_TAIL_RE = re.compile(
    r"\s+best refined tail HW: (?P<refined>\d+) "
    r"\(scan best (?P<scan>\d+), improvements=(?P<improvements>\d+)\)"
)
REFINED_R61_RE = re.compile(
    r"\s+best refined r61 HW: (?P<refined>\d+) "
    r"\(scan best (?P<scan>\d+), improvements=(?P<improvements>\d+)\)"
)
R61_W1_RE = re.compile(r"\s+best refined r61 W1\[57\.\.59\]=(?P<w1>[0-9a-fA-Fx,]+)")
R61_W2_RE = re.compile(r"\s+best refined r61 W2\[57\.\.59\]=(?P<w2>[0-9a-fA-Fx,]+)")
TAIL_W1_RE = re.compile(r"\s+best refined tail W1\[57\.\.59\]=(?P<w1>[0-9a-fA-Fx,]+)")
TAIL_W2_RE = re.compile(r"\s+best refined tail W2\[57\.\.59\]=(?P<w2>[0-9a-fA-Fx,]+)")
WITNESS0_RE = re.compile(
    r"\s+witness\[00\] tail=(?P<tail>\d+) r61=(?P<r61>\d+) "
    r"gh60=(?P<gh60>0x[0-9a-fA-F]+) W1=(?P<w1>[0-9a-fA-Fx,]+) "
    r"W2=(?P<w2>[0-9a-fA-Fx,]+)"
)
R61_WITNESS0_RE = re.compile(
    r"\s+r61_witness\[00\] r61=(?P<r61>\d+) tail=(?P<tail>\d+) "
    r"gh60=(?P<gh60>0x[0-9a-fA-F]+) W1=(?P<w1>[0-9a-fA-Fx,]+) "
    r"W2=(?P<w2>[0-9a-fA-Fx,]+)"
)


def parse_summary_body(body: str) -> dict[str, object]:
    row: dict[str, object] = {}
    for part in body.split():
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


def parse_log(path: Path) -> dict[str, object]:
    row: dict[str, object] = {"log": str(path)}
    in_refine = False
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if match := SUMMARY_RE.match(line):
            row.update(parse_summary_body(match.group("body")))
            continue
        if line == "Second-stage local refinement":
            in_refine = True
            continue
        if in_refine and (match := REFINE_BUDGET_RE.match(line)):
            row["budget"] = int(match.group("budget"))
            row["tested"] = int(match.group("tested"))
            row["refine_d0"] = int(match.group("d0"))
            row["collisions"] = int(match.group("collisions"))
            row["seed_inserts"] = int(match.group("seed_inserts"))
            row["prefix_enums"] = int(match.group("prefix_enums"))
            continue
        if in_refine and (match := REFINED_TAIL_RE.match(line)):
            row["refined_tail"] = int(match.group("refined"))
            row["scan_tail"] = int(match.group("scan"))
            row["tail_improvements"] = int(match.group("improvements"))
            continue
        if in_refine and (match := TAIL_W1_RE.match(line)):
            row["refined_tail_W1"] = match.group("w1")
            continue
        if in_refine and (match := TAIL_W2_RE.match(line)):
            row["refined_tail_W2"] = match.group("w2")
            continue
        if in_refine and (match := REFINED_R61_RE.match(line)):
            row["refined_r61"] = int(match.group("refined"))
            row["scan_r61"] = int(match.group("scan"))
            row["r61_improvements"] = int(match.group("improvements"))
            continue
        if in_refine and (match := R61_W1_RE.match(line)):
            row["refined_r61_W1"] = match.group("w1")
            continue
        if in_refine and (match := R61_W2_RE.match(line)):
            row["refined_r61_W2"] = match.group("w2")
            continue
        if match := WITNESS0_RE.match(line):
            row["registry_tail"] = int(match.group("tail"))
            row["registry_tail_r61"] = int(match.group("r61"))
            row["registry_tail_gh60"] = match.group("gh60")
            row["registry_tail_W1"] = match.group("w1")
            row["registry_tail_W2"] = match.group("w2")
            continue
        if match := R61_WITNESS0_RE.match(line):
            row["registry_r61"] = int(match.group("r61"))
            row["registry_r61_tail"] = int(match.group("tail"))
            row["registry_r61_gh60"] = match.group("gh60")
            row["registry_r61_W1"] = match.group("w1")
            row["registry_r61_W2"] = match.group("w2")
    return row


def collect_paths(raw_paths: Iterable[str]) -> list[Path]:
    paths: list[Path] = []
    for raw_path in raw_paths:
        matches = glob.glob(raw_path)
        if matches:
            paths.extend(Path(match) for match in matches)
        else:
            paths.append(Path(raw_path))
    return sorted(set(paths))


def as_int(row: dict[str, object], key: str, default: int = 999) -> int:
    value = row.get(key, default)
    return value if isinstance(value, int) else default


def window_of(row: dict[str, object]) -> int | str:
    sample_start = row.get("sample_start")
    prefixes = row.get("prefixes")
    if isinstance(sample_start, int) and isinstance(prefixes, int) and prefixes:
        return sample_start // prefixes
    return "?"


def print_row(row: dict[str, object]) -> None:
    r61_w1 = str(row.get("refined_r61_W1", "?"))
    r61_w2 = str(row.get("refined_r61_W2", "?"))
    if r61_w1 == "?" and row.get("registry_r61") == row.get("refined_r61"):
        r61_w1 = str(row.get("registry_r61_W1", "?"))
        r61_w2 = str(row.get("registry_r61_W2", "?"))
    print(
        f"  window={window_of(row)} sample_start={row.get('sample_start', '?')} "
        f"refined_tail={row.get('refined_tail', '?')} scan_tail={row.get('scan_tail', '?')} "
        f"tail_improvements={row.get('tail_improvements', '?')} "
        f"refined_r61={row.get('refined_r61', '?')} scan_r61={row.get('scan_r61', '?')} "
        f"r61_improvements={row.get('r61_improvements', '?')} "
        f"registry_tail={row.get('registry_tail', '?')}/{row.get('registry_tail_r61', '?')} "
        f"registry_r61={row.get('registry_r61', '?')}/{row.get('registry_r61_tail', '?')}"
    )
    print(
        f"    tail_W1={row.get('refined_tail_W1', row.get('registry_tail_W1', '?'))} "
        f"tail_W2={row.get('refined_tail_W2', row.get('registry_tail_W2', '?'))} "
        f"r61_W1={r61_w1} r61_W2={r61_w2}"
    )
    print(f"    log={row['log']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+")
    parser.add_argument("--top", type=int, default=12)
    args = parser.parse_args()

    rows = [parse_log(path) for path in collect_paths(args.logs) if path.exists()]
    rows = [row for row in rows if "refined_tail" in row or "refined_r61" in row]
    if not rows:
        raise SystemExit("no local-refinement rows")

    improved = [
        row for row in rows
        if as_int(row, "tail_improvements", 0) > 0 or as_int(row, "r61_improvements", 0) > 0
    ]
    print(f"rows={len(rows)} improved_rows={len(improved)}")

    print("\nbest_refined_tail:")
    for row in sorted(rows, key=lambda r: (as_int(r, "refined_tail"), as_int(r, "refined_r61")))[:args.top]:
        print_row(row)

    print("\nbest_refined_r61:")
    for row in sorted(rows, key=lambda r: (as_int(r, "refined_r61"), as_int(r, "refined_tail")))[:args.top]:
        print_row(row)

    print("\nimprovements:")
    for row in sorted(
        improved,
        key=lambda r: (
            -as_int(r, "tail_improvements", 0) - as_int(r, "r61_improvements", 0),
            as_int(r, "refined_tail"),
            as_int(r, "refined_r61"),
        ),
    )[:args.top]:
        print_row(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
