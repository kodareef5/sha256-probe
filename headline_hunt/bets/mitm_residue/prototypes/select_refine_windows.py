#!/usr/bin/env python3
"""Select reduced-N scan windows for second-stage local refinement."""

from __future__ import annotations

import argparse
import glob
import json
import re
import shlex
from pathlib import Path
from typing import Callable, Iterable


R61_WIT_RE = re.compile(r"\s+r61_witness\[00\] r61=(?P<r61>\d+) tail=(?P<tail>\d+)")


def as_int(row: dict[str, object], key: str, default: int = 999) -> int:
    value = row.get(key, default)
    return value if isinstance(value, int) else default


def load_rows(paths: Iterable[Path], *, only_n: int | None) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[tuple[int, int, str]] = set()
    for path in paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            n = as_int(row, "N")
            if only_n is not None and n != only_n:
                continue
            sample_start = as_int(row, "sample_start", -1)
            key = (n, sample_start, str(row.get("log", "")))
            if key in seen:
                continue
            seen.add(key)
            row["record"] = str(path)
            enrich_from_log(row)
            rows.append(row)
    return rows


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
        return


def collect_paths(args: argparse.Namespace) -> list[Path]:
    paths = [Path(path) for path in args.summary_jsonl]
    for pattern in args.summary_glob:
        paths.extend(Path(path) for path in glob.glob(pattern))
    return sorted(set(paths))


def window_of(row: dict[str, object]) -> int:
    return as_int(row, "sample_start") // as_int(row, "prefixes", 1)


Ranker = tuple[str, Callable[[dict[str, object]], tuple[int, ...]]]


def ranking_specs() -> list[Ranker]:
    return [
        (
            "tail",
            lambda row: (
                as_int(row, "best_tail"),
                as_int(row, "tail_r61"),
                as_int(row, "best_r61"),
                as_int(row, "sample_start"),
            ),
        ),
        (
            "r61",
            lambda row: (
                as_int(row, "best_r61"),
                as_int(row, "r61_tail"),
                as_int(row, "best_tail"),
                as_int(row, "sample_start"),
            ),
        ),
        (
            "tail+r61",
            lambda row: (
                as_int(row, "best_tail") + as_int(row, "tail_r61"),
                max(as_int(row, "best_tail"), as_int(row, "tail_r61")),
                as_int(row, "best_r61"),
                as_int(row, "sample_start"),
            ),
        ),
        (
            "balanced",
            lambda row: (
                max(as_int(row, "best_tail"), as_int(row, "best_r61")),
                as_int(row, "best_tail") + as_int(row, "best_r61"),
                as_int(row, "tail_r61"),
                as_int(row, "sample_start"),
            ),
        ),
    ]


def select_rows(rows: list[dict[str, object]], *, limit: int, top_per_rank: int) -> list[dict[str, object]]:
    selected: list[dict[str, object]] = []
    seen_windows: set[tuple[int, int]] = set()

    def add(row: dict[str, object], reason: str) -> None:
        key = (as_int(row, "N"), window_of(row))
        if key in seen_windows or len(selected) >= limit:
            return
        seen_windows.add(key)
        out = dict(row)
        out["select_reason"] = reason
        selected.append(out)

    for reason, key_fn in ranking_specs():
        for row in sorted(rows, key=key_fn)[:top_per_rank]:
            add(row, reason)
            if len(selected) >= limit:
                break
        if len(selected) >= limit:
            break
    return selected


def shell_join(parts: list[object]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def print_rows(rows: list[dict[str, object]]) -> None:
    for idx, row in enumerate(rows):
        r61_tail = row.get("r61_tail", "?")
        print(
            f"{idx:02d} reason={row['select_reason']} window={window_of(row)} "
            f"sample_start={row['sample_start']} best_tail={row.get('best_tail')} "
            f"tail_r61={row.get('tail_r61')} best_r61={row.get('best_r61')} "
            f"r61_tail={r61_tail} tail_W1={row.get('tail_W1')} r61_W1={row.get('r61_W1')}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("summary_jsonl", nargs="*")
    parser.add_argument("--summary-glob", action="append", default=[])
    parser.add_argument("--only-n", type=int, default=14)
    parser.add_argument("--limit", type=int, default=16)
    parser.add_argument("--top-per-rank", type=int, default=8)
    parser.add_argument("--binary", default="/private/tmp/free_word_mitm_reducedn_refine")
    parser.add_argument("--prefix-limit", type=int, default=32768)
    parser.add_argument("--refine-budget", type=int, default=500_000_000)
    parser.add_argument("--refine-seed-cap", type=int, default=128)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--mode", choices=("scan", "repair"), default="scan")
    parser.add_argument("--out-dir", help="emit a run_scan_batch command for this output directory")
    args = parser.parse_args()

    rows = load_rows(collect_paths(args), only_n=args.only_n)
    if not rows:
        raise SystemExit("no rows")

    selected = select_rows(rows, limit=args.limit, top_per_rank=args.top_per_rank)
    windows = [window_of(row) for row in selected]
    sample_starts = [as_int(row, "sample_start") for row in selected]

    print(f"loaded_rows={len(rows)} selected_windows={len(windows)}")
    print_rows(selected)
    print(f"windows_csv={','.join(str(window) for window in windows)}")
    print(f"sample_starts_csv={','.join(str(sample) for sample in sample_starts)}")

    if args.out_dir:
        command = [
            "python3",
            "headline_hunt/bets/mitm_residue/prototypes/run_scan_batch.py",
            "--binary",
            args.binary,
            "--n",
            args.only_n,
            "--prefix-limit",
            args.prefix_limit,
            "--refine-budget",
            args.refine_budget,
            "--refine-seed-cap",
            args.refine_seed_cap,
            "--mode",
            args.mode,
            "--window-list",
            ",".join(str(window) for window in windows),
            "--workers",
            args.workers,
            "--out-dir",
            args.out_dir,
        ]
        print(f"command={shell_join(command)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
