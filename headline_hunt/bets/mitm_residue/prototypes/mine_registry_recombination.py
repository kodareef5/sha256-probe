#!/usr/bin/env python3
"""Mine retained scan registries for cross-window recombination leads."""

from __future__ import annotations

import argparse
import json
import re
import shlex
from collections import defaultdict
from pathlib import Path
from typing import Iterable


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


def parse_registry(path: Path, row: dict[str, object]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    n = int(row["N"])
    sample_start = int(row["sample_start"])
    prefix_limit = int(row["prefixes"])
    window = sample_start // prefix_limit
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = TAIL_WIT_RE.match(line)
        kind = "tail"
        if match is None:
            match = R61_WIT_RE.match(line)
            kind = "r61"
        if match is None:
            continue
        entries.append({
            "kind": kind,
            "N": n,
            "sample_start": sample_start,
            "window": window,
            "idx": int(match.group("idx")),
            "tail": int(match.group("tail")),
            "r61": int(match.group("r61")),
            "gh60": int(match.group("gh60"), 16),
            "W1": match.group("w1"),
            "W2": match.group("w2"),
            "log": str(path),
        })
    return entries


def load_entries(paths: Iterable[Path]) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    seen_logs: set[str] = set()
    seen_entries: set[tuple[object, ...]] = set()
    for summary_path in paths:
        for line in summary_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            log_path = row.get("log")
            if not isinstance(log_path, str) or log_path in seen_logs:
                continue
            seen_logs.add(log_path)
            path = Path(log_path)
            if path.exists():
                for entry in parse_registry(path, row):
                    key = (
                        entry["N"],
                        entry["kind"],
                        entry["sample_start"],
                        entry["tail"],
                        entry["r61"],
                        entry["gh60"],
                        entry["W1"],
                        entry["W2"],
                    )
                    if key in seen_entries:
                        continue
                    seen_entries.add(key)
                    entries.append(entry)
    return entries


def gh60_hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def fmt_entry(entry: dict[str, object]) -> str:
    return (
        f"N={entry['N']} kind={entry['kind']} sample_start={entry['sample_start']} "
        f"window={entry['window']} idx={entry['idx']} tail={entry['tail']} "
        f"r61={entry['r61']} gh60=0x{int(entry['gh60']):x} "
        f"W1={entry['W1']} W2={entry['W2']}"
    )


def seed_slug(seed: str) -> str:
    return seed.lower().replace("0x", "").replace(",", "_")


def shell_join(parts: Iterable[object]) -> str:
    return " ".join(shlex.quote(str(part)) for part in parts)


def dedupe_seeds(entries: Iterable[dict[str, object]]) -> list[str]:
    seeds: list[str] = []
    seen: set[str] = set()
    for entry in entries:
        seed = str(entry["W1"])
        key = seed.lower()
        if key in seen:
            continue
        seen.add(key)
        seeds.append(seed)
    return seeds


def chunked(values: list[str], size: int) -> Iterable[list[str]]:
    for idx in range(0, len(values), size):
        yield values[idx:idx + size]


def emit_seed_batches(
    *,
    entries: list[dict[str, object]],
    n: int,
    global_seeds: list[str],
    batch_size: int,
    top: int,
    near_tail: int,
    near_r61: int,
    walk_binary: str,
    ball_binary: str,
    out_dir: Path,
    run_tag: str,
    nonce_start: int,
    walk_budget: int,
    walk_seed_cap: int,
    ball_radius: int,
    ball_budget: int,
    ball_seed_cap: int,
) -> None:
    rows = [entry for entry in entries if int(entry["N"]) == n]
    if not rows:
        return

    tail_entries = [entry for entry in rows if entry["kind"] == "tail"]
    r61_entries = [entry for entry in rows if entry["kind"] == "r61"]
    ranked_entries = (
        sorted(tail_entries, key=lambda e: (int(e["tail"]), int(e["r61"]), int(e["sample_start"])))[:top]
        + sorted(r61_entries, key=lambda e: (int(e["r61"]), int(e["tail"]), int(e["sample_start"])))[:top]
        + sorted(rows, key=lambda e: (int(e["tail"]) + int(e["r61"]), int(e["tail"]), int(e["r61"])))[:top]
        + sorted(
            [
                entry for entry in rows
                if int(entry["tail"]) <= near_tail or int(entry["r61"]) <= near_r61
            ],
            key=lambda e: (
                min(int(e["tail"]), near_tail + 1),
                min(int(e["r61"]), near_r61 + 1),
                int(e["tail"]) + int(e["r61"]),
            ),
        )[:top]
    )
    candidate_seeds = dedupe_seeds(ranked_entries)
    base_seeds = dedupe_seeds({"W1": seed} for seed in global_seeds)
    usable_batch_size = max(1, batch_size - len(base_seeds))
    if not candidate_seeds:
        return

    print(f"\nseed_refinement_batches_N{n}:")
    print(f"  selected_candidate_seeds={len(candidate_seeds)} global_seeds={len(base_seeds)}")
    for offset, group in enumerate(chunked(candidate_seeds, usable_batch_size)):
        nonce = nonce_start + offset
        seeds = base_seeds + group
        label = f"{run_tag}_n{n}_batch{offset:02d}_{seed_slug(group[0])}"
        walk_log = out_dir / f"{label}_nonce{nonce}_walk.log"
        walk_cmd = [
            walk_binary,
            n,
            0,
            walk_budget,
            walk_seed_cap,
            nonce,
            "repair_seed_walk",
            0,
            *seeds,
        ]
        print(f"  # exact walk batch={offset} seeds={len(seeds)}")
        print(f"  {shell_join(walk_cmd)} > {shlex.quote(str(walk_log))}")
        if ball_radius > 0:
            ball_log = out_dir / f"{label}_radius{ball_radius}_ball.log"
            ball_cmd = [
                ball_binary,
                n,
                0,
                ball_budget,
                ball_seed_cap,
                ball_radius,
                "repair_seed_ball",
                0,
                *seeds,
            ]
            print(f"  # hamming ball batch={offset} seeds={len(seeds)} radius={ball_radius}")
            print(f"  {shell_join(ball_cmd)} > {shlex.quote(str(ball_log))}")


def print_entries(title: str, entries: list[dict[str, object]], limit: int) -> None:
    print(f"\n{title}:")
    for entry in entries[:limit]:
        print(f"  {fmt_entry(entry)}")


def exact_pair_sort_key(row: tuple[int, int, int, int, dict[str, object], dict[str, object]]) -> tuple[int, int, int, int, int]:
    score, n, gh60, _count, best_tail, best_r61 = row
    return (score, int(best_tail["tail"]), int(best_r61["r61"]), n, gh60)


def print_exact_pairs(title: str, rows: list[tuple[int, int, int, int, dict[str, object], dict[str, object]]], limit: int) -> None:
    print(f"\n{title}:")
    for score, n, gh60, count, best_tail, best_r61 in sorted(rows, key=exact_pair_sort_key)[:limit]:
        print(
            f"  score={score} N={n} gh60=0x{gh60:x} count={count}\n"
            f"    tail: {fmt_entry(best_tail)}\n"
            f"    r61 : {fmt_entry(best_r61)}"
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("summary_jsonl", nargs="+")
    parser.add_argument("--top", type=int, default=16)
    parser.add_argument("--near-tail", type=int, default=20)
    parser.add_argument("--near-r61", type=int, default=14)
    parser.add_argument("--near-gh60-hw", type=int, default=2)
    parser.add_argument("--emit-seed-batches", action="store_true")
    parser.add_argument("--global-seed", action="append", default=[])
    parser.add_argument("--batch-size", type=int, default=6)
    parser.add_argument("--nonce-start", type=int, default=831000)
    parser.add_argument("--run-tag", default="registry_plan")
    parser.add_argument("--out-dir", default="headline_hunt/bets/mitm_residue/results/runs")
    parser.add_argument("--walk-binary", default="/private/tmp/free_word_mitm_reducedn_seed")
    parser.add_argument("--walk-budget", type=int, default=5_000_000_000)
    parser.add_argument("--walk-seed-cap", type=int, default=16)
    parser.add_argument("--ball-binary", default="/private/tmp/free_word_mitm_reducedn_ball")
    parser.add_argument("--ball-radius", type=int, default=0)
    parser.add_argument("--ball-budget", type=int, default=500_000_000)
    parser.add_argument("--ball-seed-cap", type=int, default=48)
    args = parser.parse_args()

    entries = load_entries(Path(path) for path in args.summary_jsonl)
    if not entries:
        raise SystemExit("no registry entries found")

    by_n: dict[int, list[dict[str, object]]] = defaultdict(list)
    for entry in entries:
        by_n[int(entry["N"])].append(entry)

    print(f"registry_entries={len(entries)}")
    for n in sorted(by_n):
        rows = by_n[n]
        print(
            f"N={n} entries={len(rows)} tail_entries={sum(1 for e in rows if e['kind'] == 'tail')} "
            f"r61_entries={sum(1 for e in rows if e['kind'] == 'r61')}"
        )

    tail_entries = [entry for entry in entries if entry["kind"] == "tail"]
    r61_entries = [entry for entry in entries if entry["kind"] == "r61"]

    print_entries(
        "top_tail_registry",
        sorted(tail_entries, key=lambda e: (int(e["tail"]), int(e["r61"]), int(e["N"]))),
        args.top,
    )
    print_entries(
        "top_r61_registry",
        sorted(r61_entries, key=lambda e: (int(e["r61"]), int(e["tail"]), int(e["N"]))),
        args.top,
    )
    print_entries(
        "top_joint_registry",
        sorted(entries, key=lambda e: (int(e["tail"]) + int(e["r61"]), int(e["tail"]))),
        args.top,
    )

    exact_groups: dict[tuple[int, int], list[dict[str, object]]] = defaultdict(list)
    for entry in entries:
        exact_groups[(int(entry["N"]), int(entry["gh60"]))].append(entry)
    exact_pair_rows = []
    for (n, gh60), rows in exact_groups.items():
        tail_rows = [row for row in rows if row["kind"] == "tail"]
        r61_rows = [row for row in rows if row["kind"] == "r61"]
        if not tail_rows or not r61_rows:
            continue
        best_tail = min(tail_rows, key=lambda e: (int(e["tail"]), int(e["r61"])))
        best_r61 = min(r61_rows, key=lambda e: (int(e["r61"]), int(e["tail"])))
        exact_pair_rows.append((int(best_tail["tail"]) + int(best_r61["r61"]), n, gh60, len(rows), best_tail, best_r61))
    print_exact_pairs("exact_gh60_pairs", exact_pair_rows, args.top)
    for n in sorted(by_n):
        print_exact_pairs(
            f"exact_gh60_pairs_N{n}",
            [row for row in exact_pair_rows if row[1] == n],
            args.top,
        )

    tail_candidates = [entry for entry in tail_entries if int(entry["tail"]) <= args.near_tail]
    r61_candidates = [entry for entry in r61_entries if int(entry["r61"]) <= args.near_r61]
    near_pairs = []
    for a in tail_candidates:
        for b in r61_candidates:
            if int(a["N"]) != int(b["N"]):
                continue
            dist = gh60_hamming(int(a["gh60"]), int(b["gh60"]))
            if dist > args.near_gh60_hw:
                continue
            score = int(a["tail"]) + int(b["r61"]) + dist
            tie = int(a["r61"]) + int(b["tail"])
            near_pairs.append((score, tie, dist, a, b))
    print(f"\nnear_gh60_pairs_hw_le_{args.near_gh60_hw}: candidates={len(near_pairs)}")
    for score, _tie, dist, a, b in sorted(near_pairs, key=lambda row: (
        row[0],
        row[1],
        row[2],
        int(row[3]["N"]),
        int(row[3]["sample_start"]),
        int(row[4]["sample_start"]),
    ))[:args.top]:
        print(
            f"  score={score} gh60_hw_dist={dist}\n"
            f"    a: {fmt_entry(a)}\n"
            f"    b: {fmt_entry(b)}"
        )

    if args.emit_seed_batches:
        if args.batch_size <= 0:
            raise SystemExit("--batch-size must be positive")
        out_dir = Path(args.out_dir)
        for n in sorted(by_n):
            emit_seed_batches(
                entries=entries,
                n=n,
                global_seeds=args.global_seed,
                batch_size=args.batch_size,
                top=args.top,
                near_tail=args.near_tail,
                near_r61=args.near_r61,
                walk_binary=args.walk_binary,
                ball_binary=args.ball_binary,
                out_dir=out_dir,
                run_tag=args.run_tag,
                nonce_start=args.nonce_start,
                walk_budget=args.walk_budget,
                walk_seed_cap=args.walk_seed_cap,
                ball_radius=args.ball_radius,
                ball_budget=args.ball_budget,
                ball_seed_cap=args.ball_seed_cap,
            )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
