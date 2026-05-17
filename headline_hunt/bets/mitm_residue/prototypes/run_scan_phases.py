#!/usr/bin/env python3
"""Run a sequence of reduced-N MITM scan phases.

This is a thin supervisor around run_scan_batch.py and analyze_scan_structure.py.
It keeps phase directories/results uniform while letting long strided campaigns
continue without hand-launching each start-window.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path


def parse_int_list(raw: str) -> list[int]:
    values: list[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        values.append(int(part, 0))
    return values


def count_summary_rows(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8", errors="replace").splitlines() if line.strip())


def run_and_tee(command: list[str], log_path: Path) -> int:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.time()
    with log_path.open("w", encoding="utf-8") as log_file:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        assert proc.stdout is not None
        for line in proc.stdout:
            print(line, end="", flush=True)
            log_file.write(line)
        rc = proc.wait()
        log_file.write(f"\n# rc={rc} wall_seconds={time.time() - started:.3f}\n")
    return rc


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", default="/private/tmp/free_word_mitm_reducedn")
    parser.add_argument("--n", type=int, default=14)
    parser.add_argument("--prefix-limit", type=int, default=32768)
    parser.add_argument("--refine-budget", type=int, default=0)
    parser.add_argument("--refine-seed-cap", type=int, default=16)
    parser.add_argument("--mode", choices=("scan", "repair"), default="scan")
    parser.add_argument("--repair-hw-limit", type=int, default=1)
    parser.add_argument("--stride", type=int, default=256)
    parser.add_argument("--windows", type=int, default=32)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--start-windows", required=True, help="comma-separated start-window values")
    parser.add_argument("--phase-start", type=int, required=True, help="phase number for the first start-window")
    parser.add_argument("--out-prefix", required=True, help="phase output prefix, e.g. path/.../phase")
    parser.add_argument("--analyzer", default="headline_hunt/bets/mitm_residue/prototypes/analyze_scan_structure.py")
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()

    start_windows = parse_int_list(args.start_windows)
    if not start_windows:
        raise SystemExit("no start windows provided")

    out_prefix = Path(args.out_prefix)
    analyzer = Path(args.analyzer)
    overall_rc = 0

    for offset, start_window in enumerate(start_windows):
        phase = args.phase_start + offset
        out_dir = Path(f"{out_prefix}{phase}")
        summary_path = out_dir / "summaries.jsonl"
        if args.skip_existing and count_summary_rows(summary_path) >= args.windows:
            print(f"skip phase={phase} start_window={start_window} summaries={summary_path}", flush=True)
            continue

        print(f"phase={phase} start_window={start_window} out_dir={out_dir}", flush=True)
        batch_cmd = [
            sys.executable,
            "headline_hunt/bets/mitm_residue/prototypes/run_scan_batch.py",
            "--binary",
            args.binary,
            "--n",
            str(args.n),
            "--prefix-limit",
            str(args.prefix_limit),
            "--refine-budget",
            str(args.refine_budget),
            "--refine-seed-cap",
            str(args.refine_seed_cap),
            "--mode",
            args.mode,
            "--repair-hw-limit",
            str(args.repair_hw_limit),
            "--start-window",
            str(start_window),
            "--stride",
            str(args.stride),
            "--windows",
            str(args.windows),
            "--workers",
            str(args.workers),
            "--out-dir",
            str(out_dir),
        ]
        rc = run_and_tee(batch_cmd, out_dir / "phase_stdout.log")
        overall_rc = overall_rc or rc
        if rc != 0:
            print(f"phase={phase} batch_rc={rc}; stopping", flush=True)
            return overall_rc

        analysis_cmd = [
            sys.executable,
            str(analyzer),
            "--top",
            str(args.top),
            str(summary_path),
        ]
        rc = run_and_tee(analysis_cmd, out_dir / "analysis.txt")
        overall_rc = overall_rc or rc
        if rc != 0:
            print(f"phase={phase} analysis_rc={rc}; continuing", flush=True)

    return overall_rc


if __name__ == "__main__":
    raise SystemExit(main())
