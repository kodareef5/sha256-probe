#!/usr/bin/env python3
"""Run reduced-N free-word MITM scan windows and persist summaries."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path


def parse_summary(text: str) -> dict[str, object] | None:
    for line in text.splitlines():
        if not line.startswith("SUMMARY "):
            continue
        record: dict[str, object] = {}
        for part in line.split()[1:]:
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            if "," in value:
                record[key] = value
            else:
                try:
                    record[key] = int(value, 0)
                except ValueError:
                    record[key] = value
        return record
    return None


def unique_log_path(out_dir: Path, n: int, sample_start: int) -> Path:
    base = out_dir / f"N{n}_start{sample_start}.log"
    if not base.exists():
        return base
    for rerun in range(1, 1000):
        path = out_dir / f"N{n}_start{sample_start}_r{rerun:03d}.log"
        if not path.exists():
            return path
    raise RuntimeError(f"too many reruns for sample_start={sample_start}")


def parse_window_list(raw: str) -> list[int]:
    windows: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        windows.append(int(part, 0))
    return windows


def launch(binary: Path, n: int, prefix_limit: int, refine_budget: int,
           refine_seed_cap: int, sample_start: int,
           out_dir: Path) -> tuple[subprocess.Popen[bytes], Path]:
    log_path = unique_log_path(out_dir, n, sample_start)
    log_file = log_path.open("wb")
    proc = subprocess.Popen(
        [
            str(binary),
            str(n),
            str(prefix_limit),
            str(refine_budget),
            str(refine_seed_cap),
            str(sample_start),
            "scan",
        ],
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )
    proc._scan_log_file = log_file  # type: ignore[attr-defined]
    return proc, log_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", default="/private/tmp/free_word_mitm_reducedn")
    parser.add_argument("--n", type=int, default=13)
    parser.add_argument("--prefix-limit", type=int, default=65536)
    parser.add_argument("--refine-budget", type=int, default=0)
    parser.add_argument("--refine-seed-cap", type=int, default=1)
    parser.add_argument("--start-window", type=int)
    parser.add_argument("--window-list", help="comma-separated absolute window indexes")
    parser.add_argument("--stride", type=int, default=1)
    parser.add_argument("--windows", type=int)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()

    binary = Path(args.binary)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "summaries.jsonl"

    if args.window_list:
        pending_windows = parse_window_list(args.window_list)
    else:
        if args.start_window is None or args.windows is None:
            raise SystemExit("either --window-list or both --start-window and --windows are required")
        pending_windows = [args.start_window + i * args.stride for i in range(args.windows)]
    pending = [window * args.prefix_limit for window in pending_windows]
    active: list[tuple[subprocess.Popen[bytes], Path, int, float]] = []
    completed = 0

    with summary_path.open("a", encoding="utf-8") as summaries:
        while pending or active:
            while pending and len(active) < args.workers:
                sample_start = pending.pop(0)
                proc, log_path = launch(binary, args.n, args.prefix_limit,
                                        args.refine_budget, args.refine_seed_cap,
                                        sample_start, out_dir)
                active.append((proc, log_path, sample_start, time.time()))
                print(f"launched sample_start={sample_start} pid={proc.pid}", flush=True)

            next_active: list[tuple[subprocess.Popen[bytes], Path, int, float]] = []
            for proc, log_path, sample_start, started_at in active:
                rc = proc.poll()
                if rc is None:
                    next_active.append((proc, log_path, sample_start, started_at))
                    continue
                proc._scan_log_file.close()  # type: ignore[attr-defined]
                text = log_path.read_text(encoding="utf-8", errors="replace")
                record = parse_summary(text)
                if record is None:
                    record = {"sample_start": sample_start, "parse_error": True}
                record["returncode"] = rc
                record["log"] = os.fspath(log_path)
                record["wall_seconds"] = round(time.time() - started_at, 3)
                summaries.write(json.dumps(record, sort_keys=True) + "\n")
                summaries.flush()
                completed += 1
                best_tail = record.get("best_tail")
                best_r61 = record.get("best_r61")
                print(
                    f"completed sample_start={sample_start} rc={rc} "
                    f"best_tail={best_tail} best_r61={best_r61}",
                    flush=True,
                )
            active = next_active
            if active:
                time.sleep(0.25)

    print(f"completed_windows={completed} summaries={summary_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
