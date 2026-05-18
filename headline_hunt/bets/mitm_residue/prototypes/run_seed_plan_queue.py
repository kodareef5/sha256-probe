#!/usr/bin/env python3
"""Run seed-refinement commands emitted by mine_registry_recombination.py.

The recombination report prints shell commands for exact seed-walk batches.
This helper turns that static plan into a small work queue so long campaigns
can keep a fixed number of workers busy without repeatedly hand-launching
individual batches.
"""

from __future__ import annotations

import argparse
import re
import shlex
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


BATCH_RE = re.compile(r"#\s+exact walk batch=(?P<batch>\d+)")
REDIRECT_RE = re.compile(r"\s+>\s+")
NONCE_WALK_RE = re.compile(r"_nonce\d+_walk\.log$")


@dataclass(frozen=True)
class PlanJob:
    batch: int
    command: list[str]
    log_path: Path


@dataclass
class RunningJob:
    job: PlanJob
    proc: subprocess.Popen[str]
    log_file: object
    started: float


def parse_budget_short(value: int) -> str:
    if value % 1_000_000_000 == 0:
        return f"{value // 1_000_000_000}b"
    if value % 1_000_000 == 0:
        return f"{value // 1_000_000}m"
    return str(value)


def split_command_line(line: str) -> tuple[list[str], Path] | None:
    pieces = REDIRECT_RE.split(line.strip(), maxsplit=1)
    if len(pieces) != 2:
        return None
    command = shlex.split(pieces[0])
    log_part = shlex.split(pieces[1])
    if len(log_part) != 1:
        raise ValueError(f"could not parse redirect target from line: {line}")
    return command, Path(log_part[0])


def parse_plan(path: Path) -> list[PlanJob]:
    jobs: list[PlanJob] = []
    current_batch: int | None = None
    for raw_line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = raw_line.strip()
        match = BATCH_RE.search(stripped)
        if match is not None:
            current_batch = int(match.group("batch"))
            continue
        if not stripped.startswith("/"):
            continue
        parsed = split_command_line(stripped)
        if parsed is None:
            continue
        if current_batch is None:
            raise ValueError(f"command appeared before batch marker: {raw_line}")
        command, log_path = parsed
        jobs.append(PlanJob(batch=current_batch, command=command, log_path=log_path))
    return jobs


def derive_ball_job(
    job: PlanJob,
    *,
    ball_binary: str,
    ball_budget: int,
    ball_seed_cap: int,
    ball_radius: int,
) -> PlanJob:
    command = job.command
    if len(command) < 8:
        raise ValueError(f"command too short for batch {job.batch}: {command}")
    n = command[1]
    mask_or_start = command[2]
    seeds = command[8:]
    ball_command = [
        ball_binary,
        n,
        mask_or_start,
        str(ball_budget),
        str(ball_seed_cap),
        str(ball_radius),
        "repair_seed_ball",
        "0",
        *seeds,
    ]
    budget_short = parse_budget_short(ball_budget)
    original = str(job.log_path)
    replacement = f"_radius{ball_radius}_budget{budget_short}_ball.log"
    if NONCE_WALK_RE.search(original):
        ball_log = Path(NONCE_WALK_RE.sub(replacement, original))
    else:
        ball_log = job.log_path.with_name(
            f"{job.log_path.stem}_radius{ball_radius}_budget{budget_short}_ball.log"
        )
    return PlanJob(batch=job.batch, command=ball_command, log_path=ball_log)


def replace_binary(job: PlanJob, binary: str | None) -> PlanJob:
    if not binary:
        return job
    command = [binary, *job.command[1:]]
    return PlanJob(batch=job.batch, command=command, log_path=job.log_path)


def add_log_suffix(job: PlanJob, suffix: str) -> PlanJob:
    if not suffix:
        return job
    path = job.log_path
    return PlanJob(
        batch=job.batch,
        command=job.command,
        log_path=path.with_name(f"{path.stem}{suffix}{path.suffix}"),
    )


def replace_mode(job: PlanJob, mode: str | None) -> PlanJob:
    if not mode:
        return job
    command = list(job.command)
    if len(command) < 7:
        raise ValueError(f"command too short to replace mode for batch {job.batch}: {command}")
    command[6] = mode
    return PlanJob(batch=job.batch, command=command, log_path=job.log_path)


def replace_command_index(job: PlanJob, index: int, value: int | None, label: str) -> PlanJob:
    if value is None:
        return job
    command = list(job.command)
    if len(command) <= index:
        raise ValueError(f"command too short to replace {label} for batch {job.batch}: {command}")
    command[index] = str(value)
    return PlanJob(batch=job.batch, command=command, log_path=job.log_path)


def log_has_summary(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        return "SUMMARY " in path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False


def last_summary(path: Path) -> str:
    if not path.exists():
        return ""
    summary = ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("SUMMARY "):
            summary = line
    return summary


def should_skip(job: PlanJob, *, skip_existing: bool, skip_completed: bool) -> str | None:
    if skip_completed and log_has_summary(job.log_path):
        return "completed"
    if skip_existing and job.log_path.exists():
        return "existing"
    return None


def launch(job: PlanJob) -> RunningJob:
    job.log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = job.log_path.open("w", encoding="utf-8")
    proc = subprocess.Popen(
        job.command,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return RunningJob(job=job, proc=proc, log_file=log_file, started=time.time())


def finish(running: RunningJob) -> int:
    rc = running.proc.wait()
    running.log_file.close()
    elapsed = time.time() - running.started
    summary = last_summary(running.job.log_path)
    print(
        f"done batch={running.job.batch} rc={rc} elapsed={elapsed:.1f}s "
        f"log={running.job.log_path}",
        flush=True,
    )
    if summary:
        print(f"  {summary}", flush=True)
    return rc


def bounded_jobs(jobs: list[PlanJob], start_batch: int, end_batch: int | None) -> list[PlanJob]:
    selected = [job for job in jobs if job.batch >= start_batch]
    if end_batch is not None:
        selected = [job for job in selected if job.batch <= end_batch]
    return selected


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plan", type=Path)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--start-batch", type=int, default=0)
    parser.add_argument("--end-batch", type=int)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--rerun-completed", action="store_true")
    parser.add_argument("--poll-seconds", type=float, default=2.0)
    parser.add_argument("--replace-binary", help="override the executable parsed from the plan")
    parser.add_argument("--replace-budget", type=int, help="override parsed refine budget")
    parser.add_argument("--replace-seed-cap", type=int, help="override parsed seed cap")
    parser.add_argument("--replace-repair-hw-limit", type=int, help="override parsed repair HW limit")
    parser.add_argument(
        "--replace-mode",
        choices=(
            "repair_seed",
            "repair_seed_walk",
            "repair_seed_joint_walk",
            "repair_seed_joint_energy_walk",
            "repair_seed_ball",
        ),
        help="override the repair mode parsed from exact-walk plan commands",
    )
    parser.add_argument("--log-suffix", default="", help="insert suffix before .log for derived runs")
    parser.add_argument("--derive-ball", action="store_true")
    parser.add_argument("--ball-binary", default="/private/tmp/free_word_mitm_reducedn_ball")
    parser.add_argument("--ball-budget", type=int, default=3_000_000_000)
    parser.add_argument("--ball-seed-cap", type=int, default=64)
    parser.add_argument("--ball-radius", type=int, default=9)
    args = parser.parse_args()

    if args.jobs < 1:
        raise SystemExit("--jobs must be >= 1")

    jobs = bounded_jobs(parse_plan(args.plan), args.start_batch, args.end_batch)
    if args.derive_ball:
        jobs = [
            derive_ball_job(
                job,
                ball_binary=args.ball_binary,
                ball_budget=args.ball_budget,
                ball_seed_cap=args.ball_seed_cap,
                ball_radius=args.ball_radius,
            )
            for job in jobs
        ]
    if args.replace_binary:
        jobs = [replace_binary(job, args.replace_binary) for job in jobs]
    if args.replace_budget is not None:
        jobs = [replace_command_index(job, 3, args.replace_budget, "budget") for job in jobs]
    if args.replace_seed_cap is not None:
        jobs = [replace_command_index(job, 4, args.replace_seed_cap, "seed cap") for job in jobs]
    if args.replace_mode:
        jobs = [replace_mode(job, args.replace_mode) for job in jobs]
    if args.replace_repair_hw_limit is not None:
        jobs = [
            replace_command_index(job, 7, args.replace_repair_hw_limit, "repair HW limit")
            for job in jobs
        ]
    if args.log_suffix:
        jobs = [add_log_suffix(job, args.log_suffix) for job in jobs]

    pending: list[PlanJob] = []
    skipped: dict[str, int] = {"completed": 0, "existing": 0}
    for job in jobs:
        reason = should_skip(
            job,
            skip_existing=args.skip_existing,
            skip_completed=not args.rerun_completed,
        )
        if reason is not None:
            skipped[reason] += 1
            continue
        pending.append(job)

    mode = "derived_ball" if args.derive_ball else "exact_walk"
    print(
        f"queue mode={mode} pending={len(pending)} skipped_completed={skipped['completed']} "
        f"skipped_existing={skipped['existing']} jobs={args.jobs}",
        flush=True,
    )

    running: list[RunningJob] = []
    overall_rc = 0
    while pending or running:
        while pending and len(running) < args.jobs:
            job = pending.pop(0)
            running_job = launch(job)
            running.append(running_job)
            print(f"launched batch={job.batch} pid={running_job.proc.pid} log={job.log_path}", flush=True)

        still_running: list[RunningJob] = []
        for running_job in running:
            rc = running_job.proc.poll()
            if rc is None:
                still_running.append(running_job)
                continue
            overall_rc = overall_rc or finish(running_job)
        running = still_running
        if running:
            time.sleep(args.poll_seconds)

    return overall_rc


if __name__ == "__main__":
    raise SystemExit(main())
