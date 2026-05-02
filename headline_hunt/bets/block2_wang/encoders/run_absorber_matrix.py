#!/usr/bin/env python3
"""Run a block2 absorber probe matrix over manifest residuals.

This is an orchestration wrapper around prototypes/block2_absorber_probe.c.
It exports selected manifest ranks to residual JSONL, optionally builds the C
probe, runs a rounds x seeds matrix, and writes a compact summary ranking.
"""

import argparse
import csv
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
DEFAULT_SOURCE = REPO / "headline_hunt/bets/block2_wang/prototypes/block2_absorber_probe.c"
DEFAULT_BINARY = Path("/tmp/block2_absorber_probe")

sys.path.insert(0, str(HERE))
from export_manifest_residuals import load_json, seed_to_row  # noqa: E402


def parse_int_list(raw: str) -> list[int]:
    return [int(part, 0) for part in raw.split(",") if part.strip()]


def parse_rank_filter(raw: str) -> set[int] | None:
    if not raw:
        return None
    return {int(part) for part in raw.split(",") if part.strip()}


def build_probe(source: Path, binary: Path) -> None:
    cmd = [
        "gcc",
        "-O3",
        "-march=native",
        "-Wall",
        "-Wextra",
        str(source),
        "-o",
        str(binary),
    ]
    subprocess.run(cmd, check=True)


def export_rows(manifest: Path, out_jsonl: Path, ranks: set[int] | None, top: int | None) -> list[dict[str, Any]]:
    payload = load_json(manifest)
    seeds = payload.get("seeds", [])
    if top is not None:
        seeds = seeds[:top]

    rows = []
    for seed in seeds:
        if ranks is not None and seed.get("rank") not in ranks:
            continue
        row = seed_to_row(seed, manifest)
        if row is not None:
            rows.append(row)

    out_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with out_jsonl.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    return rows


def run_probe(binary: Path, residuals: Path, rounds: int, iterations: int, seed: int, count: int, out_csv: Path) -> str:
    cmd = [str(binary), str(residuals), str(rounds), str(iterations), hex(seed), str(count)]
    proc = subprocess.run(cmd, check=True, text=True, capture_output=True)
    out_csv.write_text(proc.stdout, encoding="utf-8")
    return proc.stderr.strip()


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write_summary(
    out_json: Path,
    out_md: Path,
    residual_rows: list[dict[str, Any]],
    run_files: list[dict[str, Any]],
) -> None:
    row_by_record = {idx: row for idx, row in enumerate(residual_rows, start=1)}
    aggregate: dict[int, dict[str, Any]] = {}
    observations = []

    for run in run_files:
        for raw in load_csv(Path(run["csv"])):
            record_idx = int(raw["record"])
            source = row_by_record[record_idx]
            rank = int(source["source_rank"])
            best_hw = int(raw["best_hw"])
            obs = {
                "rank": rank,
                "rounds": run["rounds"],
                "seed": run["seed"],
                "block1_hw": int(raw["input_hw"]),
                "bridge_score": source.get("score"),
                "start_hw": int(raw["start_hw"]),
                "best_hw": best_hw,
                "improvement": int(raw["improvement"]),
                "W": [source.get(f"w_{slot}") for slot in range(57, 61)],
            }
            observations.append(obs)
            stats = aggregate.setdefault(rank, {
                "rank": rank,
                "block1_hw": obs["block1_hw"],
                "bridge_score": obs["bridge_score"],
                "best_hw_min": best_hw,
                "best_hw_sum": 0,
                "runs": 0,
                "W": obs["W"],
            })
            stats["best_hw_min"] = min(stats["best_hw_min"], best_hw)
            stats["best_hw_sum"] += best_hw
            stats["runs"] += 1

    ranking = []
    for stats in aggregate.values():
        stats = dict(stats)
        stats["best_hw_mean"] = round(stats["best_hw_sum"] / stats["runs"], 3)
        del stats["best_hw_sum"]
        ranking.append(stats)
    ranking.sort(key=lambda row: (row["best_hw_min"], row["best_hw_mean"], row["block1_hw"], row["rank"]))

    payload = {
        "description": "absorber matrix summary",
        "run_files": run_files,
        "ranking": ranking,
        "observations": observations,
    }
    out_json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Absorber Matrix Summary",
        "",
        "| Rank | Block-1 HW | Bridge Score | Min Best HW | Mean Best HW | Runs | W57..W60 |",
        "|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in ranking[:20]:
        words = ",".join(str(w) for w in row["W"])
        lines.append(
            f"| {row['rank']} | {row['block1_hw']} | {row['bridge_score']} | "
            f"{row['best_hw_min']} | {row['best_hw_mean']} | {row['runs']} | `{words}` |"
        )
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--label", default="absorber_matrix")
    ap.add_argument("--rounds", default="12,16,20,24")
    ap.add_argument("--seeds", default="0x20260502")
    ap.add_argument("--iterations", type=int, default=5_000_000)
    ap.add_argument("--ranks", default="")
    ap.add_argument("--top", type=int, default=None)
    ap.add_argument("--binary", default=str(DEFAULT_BINARY))
    ap.add_argument("--source", default=str(DEFAULT_SOURCE))
    ap.add_argument("--compile", action="store_true")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    binary = Path(args.binary)
    source = Path(args.source)
    if args.compile:
        build_probe(source, binary)

    rounds = parse_int_list(args.rounds)
    seeds = parse_int_list(args.seeds)
    ranks = parse_rank_filter(args.ranks)
    residuals = out_dir / f"{args.label}_residuals.jsonl"
    residual_rows = export_rows(Path(args.manifest), residuals, ranks, args.top)
    if not residual_rows:
        raise SystemExit("no residual rows selected")

    run_files = []
    for round_count in rounds:
        for seed in seeds:
            csv_path = out_dir / f"{args.label}_r{round_count}_seed{seed:08x}_{args.iterations}.csv"
            stderr = run_probe(binary, residuals, round_count, args.iterations, seed, len(residual_rows), csv_path)
            print(stderr)
            run_files.append({
                "rounds": round_count,
                "seed": seed,
                "iterations": args.iterations,
                "csv": str(csv_path),
            })

    write_summary(
        out_dir / f"{args.label}_summary.json",
        out_dir / f"{args.label}_summary.md",
        residual_rows,
        run_files,
    )
    print(f"wrote {out_dir / f'{args.label}_summary.md'}")


if __name__ == "__main__":
    main()
