#!/usr/bin/env python3
"""Summarize reduced-N free-word MITM scan JSONL output."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable


R61_WIT_RE = re.compile(r"\s+r61_witness\[00\] r61=(?P<r61>\d+) tail=(?P<tail>\d+)")


def enrich_from_log(row: dict[str, object]) -> None:
    log_path = row.get("log")
    if not isinstance(log_path, str):
        return
    path = Path(log_path)
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = R61_WIT_RE.match(line)
        if not match:
            continue
        row["r61_tail"] = int(match.group("tail"))
        row["r61_registry_hw"] = int(match.group("r61"))
        return


def load_rows(paths: Iterable[Path]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[tuple[int, int]] = set()
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            sample_start = int(row["sample_start"])
            key = (int(row["N"]), sample_start)
            if key in seen:
                continue
            seen.add(key)
            enrich_from_log(row)
            rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("summary_jsonl", nargs="+")
    parser.add_argument("--prior-windows", type=int, default=0)
    parser.add_argument("--prefix-space", type=int, default=1 << 26)
    parser.add_argument("--top", type=int, default=8)
    args = parser.parse_args()

    rows = load_rows(Path(path) for path in args.summary_jsonl)
    if not rows:
        raise SystemExit("no summary rows found")

    prefix_limit = int(rows[0]["prefixes"])
    logged_windows = len(rows)
    total_windows = args.prior_windows + logged_windows
    covered_prefixes = total_windows * prefix_limit
    covered_pct = 100.0 * covered_prefixes / args.prefix_space
    triples = sum(int(row["total"]) for row in rows) + (
        args.prior_windows * int(rows[0]["total"])
    )

    print(f"logged_windows={logged_windows}")
    print(f"prior_windows={args.prior_windows}")
    print(f"total_windows={total_windows}")
    print(f"covered_prefixes={covered_prefixes}/{args.prefix_space} ({covered_pct:.2f}%)")
    print(f"triples={triples}")
    print(f"logged_window_range={min(int(r['sample_start']) // prefix_limit for r in rows)}.."
          f"{max(int(r['sample_start']) // prefix_limit for r in rows)}")

    print("\nbest_tail:")
    for row in sorted(rows, key=lambda r: (int(r["best_tail"]), int(r["best_r61"])))[:args.top]:
        print(
            f"  sample_start={row['sample_start']} tail={row['best_tail']} "
            f"tail_r61={row['tail_r61']} best_r61={row['best_r61']} "
            f"W1={row['tail_W1']} W2={row['tail_W2']}"
        )

    print("\nbest_r61:")
    for row in sorted(rows, key=lambda r: (int(r["best_r61"]), int(r["best_tail"])))[:args.top]:
        r61_tail = row.get("r61_tail", "?")
        print(
            f"  sample_start={row['sample_start']} r61={row['best_r61']} "
            f"r61_tail={r61_tail} window_tail={row['best_tail']} "
            f"W1={row['r61_W1']} W2={row['r61_W2']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
