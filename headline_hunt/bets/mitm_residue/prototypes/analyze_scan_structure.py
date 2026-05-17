#!/usr/bin/env python3
"""Analyze structural signals in reduced-N free-word MITM scan logs."""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Iterable


D0_RE = re.compile(r"D60=0 matches: (?P<d0>\d+)")
PREFIX_RE = re.compile(r"prefixes with D60=0: (?P<prefixes>\d+)")
MAX_FIBER_RE = re.compile(
    r"max D60=0 fiber per prefix: (?P<max_fiber>\d+) "
    r"at W57=(?P<w57>0x[0-9a-fA-F]+) W58=(?P<w58>0x[0-9a-fA-F]+)"
)
LARGEST_BUCKET_RE = re.compile(
    r"largest D60 bucket: D=(?P<bucket_d>0x[0-9a-fA-F]+) count=(?P<bucket_count>\d+)"
)
HW_HIST_RE = re.compile(r"D60 HW histogram: (?P<hist>.*)")
TAIL_WIT_RE = re.compile(
    r"\s+witness\[(?P<idx>\d+)\] tail=(?P<tail>\d+) r61=(?P<r61>\d+) "
    r"gh60=(?P<gh60>0x[0-9a-fA-F]+) W1=(?P<w1>[0-9a-fA-Fx,]+) "
    r"W2=(?P<w2>[0-9a-fA-Fx,]+)"
)
R61_WIT_RE = re.compile(
    r"\s+r61_witness\[(?P<idx>\d+)\] r61=(?P<r61>\d+) tail=(?P<tail>\d+) "
    r"gh60=(?P<gh60>0x[0-9a-fA-F]+) W1=(?P<w1>[0-9a-fA-Fx,]+) "
    r"W2=(?P<w2>[0-9a-fA-Fx,]+)"
)
REPAIR_WIT_RE = re.compile(
    r"\s+repair_witness\[(?P<idx>\d+)\] tail=(?P<tail>\d+) r61=(?P<r61>\d+) "
    r"d60=(?P<d60>0x[0-9a-fA-F]+) d60_hw=(?P<d60_hw>\d+) "
    r"gh60=(?P<gh60>0x[0-9a-fA-F]+) W1=(?P<w1>[0-9a-fA-Fx,]+) "
    r"W2=(?P<w2>[0-9a-fA-Fx,]+)"
)
REPAIR_R61_WIT_RE = re.compile(
    r"\s+repair_r61_witness\[(?P<idx>\d+)\] r61=(?P<r61>\d+) tail=(?P<tail>\d+) "
    r"d60=(?P<d60>0x[0-9a-fA-F]+) d60_hw=(?P<d60_hw>\d+) "
    r"gh60=(?P<gh60>0x[0-9a-fA-F]+) W1=(?P<w1>[0-9a-fA-Fx,]+) "
    r"W2=(?P<w2>[0-9a-fA-Fx,]+)"
)
REPAIR_CAND_RE = re.compile(r"\s+repair_candidates=(?P<count>\d+) d60_hw_limit=(?P<limit>\d+)")


def load_rows(paths: Iterable[Path], *, dedupe: bool = True) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    seen: set[tuple[int, int]] = set()
    for path in paths:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            sample_start = int(row["sample_start"])
            key = (int(row["N"]), sample_start)
            if dedupe and key in seen:
                continue
            seen.add(key)
            rows.append(row)
    return rows


def parse_hist(raw: str) -> dict[int, int]:
    hist: dict[int, int] = {}
    for part in raw.split():
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        hist[int(key)] = int(value)
    return hist


def parse_log(path: Path) -> dict[str, object]:
    out: dict[str, object] = {
        "tail_registry": [],
        "r61_registry": [],
        "repair_registry": [],
        "repair_r61_registry": [],
    }
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        if match := D0_RE.search(line):
            out["d0"] = int(match.group("d0"))
        elif match := PREFIX_RE.search(line):
            out["d0_prefixes"] = int(match.group("prefixes"))
        elif match := MAX_FIBER_RE.search(line):
            out["max_fiber"] = int(match.group("max_fiber"))
            out["max_fiber_w57"] = int(match.group("w57"), 16)
            out["max_fiber_w58"] = int(match.group("w58"), 16)
        elif match := LARGEST_BUCKET_RE.search(line):
            out["largest_bucket_d"] = int(match.group("bucket_d"), 16)
            out["largest_bucket_count"] = int(match.group("bucket_count"))
        elif match := HW_HIST_RE.search(line):
            out["d60_hw_hist"] = parse_hist(match.group("hist"))
        elif match := TAIL_WIT_RE.search(line):
            out["tail_registry"].append({
                "idx": int(match.group("idx")),
                "tail": int(match.group("tail")),
                "r61": int(match.group("r61")),
                "gh60": int(match.group("gh60"), 16),
                "W1": match.group("w1"),
                "W2": match.group("w2"),
            })
        elif match := R61_WIT_RE.search(line):
            out["r61_registry"].append({
                "idx": int(match.group("idx")),
                "r61": int(match.group("r61")),
                "tail": int(match.group("tail")),
                "gh60": int(match.group("gh60"), 16),
                "W1": match.group("w1"),
                "W2": match.group("w2"),
            })
        elif match := REPAIR_CAND_RE.search(line):
            out["repair_candidates"] = int(match.group("count"))
            out["repair_d60_hw_limit"] = int(match.group("limit"))
        elif match := REPAIR_WIT_RE.search(line):
            out["repair_registry"].append({
                "idx": int(match.group("idx")),
                "tail": int(match.group("tail")),
                "r61": int(match.group("r61")),
                "d60": int(match.group("d60"), 16),
                "d60_hw": int(match.group("d60_hw")),
                "gh60": int(match.group("gh60"), 16),
                "W1": match.group("w1"),
                "W2": match.group("w2"),
            })
        elif match := REPAIR_R61_WIT_RE.search(line):
            out["repair_r61_registry"].append({
                "idx": int(match.group("idx")),
                "r61": int(match.group("r61")),
                "tail": int(match.group("tail")),
                "d60": int(match.group("d60"), 16),
                "d60_hw": int(match.group("d60_hw")),
                "gh60": int(match.group("gh60"), 16),
                "W1": match.group("w1"),
                "W2": match.group("w2"),
            })
    return out


def pearson(rows: list[dict[str, object]], x_key: str, y_key: str) -> float | None:
    pairs = [
        (float(row[x_key]), float(row[y_key]))
        for row in rows
        if x_key in row and y_key in row
    ]
    if len(pairs) < 2:
        return None
    xs = [x for x, _ in pairs]
    ys = [y for _, y in pairs]
    mx = mean(xs)
    my = mean(ys)
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0.0 or vy == 0.0:
        return None
    return sum((x - mx) * (y - my) for x, y in pairs) / math.sqrt(vx * vy)


def fmt_corr(value: float | None) -> str:
    return "n/a" if value is None else f"{value:+.4f}"


def print_rows(title: str, rows: list[dict[str, object]], limit: int, *, witness: str) -> None:
    w1_key = "r61_W1" if witness == "r61" else "tail_W1"
    w2_key = "r61_W2" if witness == "r61" else "tail_W2"
    print(f"\n{title}:")
    for row in rows[:limit]:
        sample_start = int(row["sample_start"])
        if witness == "r61" and row.get("r61_registry"):
            tail_label = "r61_tail"
            tail_value = row["r61_registry"][0]["tail"]  # type: ignore[index]
        else:
            tail_label = "tail"
            tail_value = row["best_tail"]
        print(
            f"  sample_start={sample_start} window={sample_start // int(row['prefixes'])} "
            f"{tail_label}={tail_value} window_tail={row['best_tail']} tail_r61={row['tail_r61']} "
            f"best_r61={row['best_r61']} d0={row.get('d0', '?')} "
            f"max_fiber={row.get('max_fiber', '?')} bucket={row.get('largest_bucket_count', '?')} "
            f"W1={row[w1_key]} W2={row[w2_key]}"
        )


def print_registry_rows(title: str, rows: list[dict[str, object]], limit: int) -> None:
    print(f"\n{title}:")
    for row in rows[:limit]:
        d60 = ""
        if "d60" in row:
            d60 = f" d60=0x{int(row['d60']):x} d60_hw={row['d60_hw']}"
        print(
            f"  sample_start={row['sample_start']} window={row['window']} idx={row['idx']} "
            f"tail={row['tail']} r61={row['r61']}{d60} gh60=0x{int(row['gh60']):x} "
            f"W1={row['W1']} W2={row['W2']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("summary_jsonl", nargs="+")
    parser.add_argument("--prior-windows", type=int, default=0)
    parser.add_argument("--top", type=int, default=12)
    parser.add_argument(
        "--keep-reruns",
        action="store_true",
        help="keep duplicate (N, sample_start) rows, useful for comparing repair modes",
    )
    args = parser.parse_args()

    rows = load_rows((Path(path) for path in args.summary_jsonl), dedupe=not args.keep_reruns)
    if not rows:
        raise SystemExit("no rows")

    enriched: list[dict[str, object]] = []
    for row in rows:
        merged = dict(row)
        log_path = row.get("log")
        if isinstance(log_path, str) and log_path:
            path = Path(log_path)
            if path.exists():
                merged.update(parse_log(path))
        enriched.append(merged)

    prefix_limit = int(enriched[0]["prefixes"])
    n = int(enriched[0]["N"])
    prefix_space = 1 << (2 * n)
    windows = len(enriched)
    covered = windows * prefix_limit
    total_with_prior = (windows + args.prior_windows) * prefix_limit
    print(f"N={n}")
    print(f"logged_windows={windows}")
    print(f"prior_windows={args.prior_windows}")
    print(f"logged_prefixes={covered}/{prefix_space} ({100.0 * covered / prefix_space:.2f}%)")
    print(f"total_prefixes_with_prior={total_with_prior}/{prefix_space} ({100.0 * total_with_prior / prefix_space:.2f}%)")
    print(f"triples={sum(int(row['total']) for row in enriched)}")

    tail_counts = Counter(int(row["best_tail"]) for row in enriched)
    r61_counts = Counter(int(row["best_r61"]) for row in enriched)
    print("\nbest_tail_hist:")
    print("  " + " ".join(f"{k}:{tail_counts[k]}" for k in sorted(tail_counts)))
    print("\nbest_r61_hist:")
    print("  " + " ".join(f"{k}:{r61_counts[k]}" for k in sorted(r61_counts)))

    print("\ncorrelations_vs_best_tail:")
    for key in ("best_r61", "tail_r61", "d0", "d0_prefixes", "max_fiber", "largest_bucket_count"):
        print(f"  {key}: {fmt_corr(pearson(enriched, key, 'best_tail'))}")

    low_tail = [row for row in enriched if int(row["best_tail"]) <= 13]
    low_r61 = [row for row in enriched if int(row["best_r61"]) <= 8]
    print(f"\nlow_tail_windows_tail_le_13={len(low_tail)}")
    print(f"low_r61_windows_r61_le_8={len(low_r61)}")

    tail_registry_rows: list[dict[str, object]] = []
    r61_registry_rows: list[dict[str, object]] = []
    repair_registry_rows: list[dict[str, object]] = []
    repair_r61_registry_rows: list[dict[str, object]] = []
    for row in enriched:
        sample_start = int(row["sample_start"])
        window = sample_start // int(row["prefixes"])
        for entry in row.get("tail_registry", []):
            merged = dict(entry)
            merged["sample_start"] = sample_start
            merged["window"] = window
            tail_registry_rows.append(merged)
        for entry in row.get("r61_registry", []):
            merged = dict(entry)
            merged["sample_start"] = sample_start
            merged["window"] = window
            r61_registry_rows.append(merged)
        for entry in row.get("repair_registry", []):
            merged = dict(entry)
            merged["sample_start"] = sample_start
            merged["window"] = window
            repair_registry_rows.append(merged)
        for entry in row.get("repair_r61_registry", []):
            merged = dict(entry)
            merged["sample_start"] = sample_start
            merged["window"] = window
            repair_r61_registry_rows.append(merged)

    print(f"tail_registry_entries={len(tail_registry_rows)}")
    print(f"r61_registry_entries={len(r61_registry_rows)}")
    if repair_registry_rows or repair_r61_registry_rows:
        print(f"repair_registry_entries={len(repair_registry_rows)}")
        print(f"repair_r61_registry_entries={len(repair_r61_registry_rows)}")
        print(f"repair_candidates={sum(int(row.get('repair_candidates', 0)) for row in enriched)}")

    print("\nband_summary:")
    band_count = 16
    for band in range(band_count):
        lo = band * prefix_space // band_count
        hi = (band + 1) * prefix_space // band_count
        band_rows = [row for row in enriched if lo <= int(row["sample_start"]) < hi]
        if not band_rows:
            continue
        best_tail = min(int(row["best_tail"]) for row in band_rows)
        best_r61 = min(int(row["best_r61"]) for row in band_rows)
        avg_tail = mean(int(row["best_tail"]) for row in band_rows)
        low = sum(1 for row in band_rows if int(row["best_tail"]) <= 13)
        print(
            f"  band={band:02d} windows={len(band_rows):3d} "
            f"best_tail={best_tail:2d} avg_tail={avg_tail:5.2f} "
            f"best_r61={best_r61:2d} tail_le13={low}"
        )

    print_rows(
        "best_tail_rows",
        sorted(enriched, key=lambda r: (int(r["best_tail"]), int(r["tail_r61"]), int(r["best_r61"]))),
        args.top,
        witness="tail",
    )
    print_rows(
        "best_r61_rows",
        sorted(enriched, key=lambda r: (int(r["best_r61"]), int(r["best_tail"]))),
        args.top,
        witness="r61",
    )
    print_rows(
        "best_joint_rows",
        sorted(enriched, key=lambda r: (int(r["best_tail"]) + int(r["best_r61"]), int(r["best_tail"]))),
        args.top,
        witness="tail",
    )
    if tail_registry_rows:
        print_registry_rows(
            "registry_tail_rows",
            sorted(tail_registry_rows, key=lambda r: (int(r["tail"]), int(r["r61"]))),
            args.top,
        )
    if r61_registry_rows:
        print_registry_rows(
            "registry_r61_rows",
            sorted(r61_registry_rows, key=lambda r: (int(r["r61"]), int(r["tail"]))),
            args.top,
        )
    if repair_registry_rows:
        print_registry_rows(
            "repair_registry_tail_rows",
            sorted(repair_registry_rows, key=lambda r: (int(r["tail"]), int(r["r61"]), int(r["d60_hw"]))),
            args.top,
        )
    if repair_r61_registry_rows:
        print_registry_rows(
            "repair_registry_r61_rows",
            sorted(repair_r61_registry_rows, key=lambda r: (int(r["r61"]), int(r["tail"]), int(r["d60_hw"]))),
            args.top,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
