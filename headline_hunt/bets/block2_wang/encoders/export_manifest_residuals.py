#!/usr/bin/env python3
"""Export pair-beam seed manifests as residual JSONL.

The C absorber prototype consumes residual-corpus rows with candidate_id,
hw_total, W57..W60, and diff63. Pair-beam seed manifests already contain
that information, but in a nested JSON shape. This utility makes the near
residuals from the current Path C basin directly usable by the second-block
absorber probe.
"""

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def word_key(slot: int) -> str:
    return f"w_{slot}"


def seed_to_row(seed: dict[str, Any], source_manifest: Path) -> dict[str, Any] | None:
    diff63 = seed.get("diff63")
    words = seed.get("W")
    hw_total = seed.get("hw_total")
    if not diff63 or not words or hw_total is None:
        return None
    if len(diff63) != 8 or len(words) != 4:
        return None

    row = {
        "candidate_id": seed.get("candidate") or "unknown",
        "source_manifest": str(source_manifest),
        "source_rank": seed.get("rank"),
        "source_artifact": seed.get("source_artifact"),
        "source_section": seed.get("source_section"),
        "hw_total": hw_total,
        "score": seed.get("score"),
        "diff63": diff63,
    }
    for offset, value in enumerate(words):
        row[word_key(57 + offset)] = value
    for idx, reg in enumerate(("a", "b", "c", "d", "e", "f", "g", "h")):
        row[f"{reg}63"] = diff63[idx]
    return row


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True, help="seed manifest JSON")
    ap.add_argument("--out", required=True, help="output residual JSONL")
    ap.add_argument("--max-hw", type=int, default=None)
    ap.add_argument("--top", type=int, default=None)
    ap.add_argument(
        "--ranks",
        default="",
        help="optional comma-separated source ranks to export, e.g. 1,2,18,19",
    )
    args = ap.parse_args()

    manifest_path = Path(args.manifest)
    payload = load_json(manifest_path)
    seeds = payload.get("seeds", [])
    if args.top is not None:
        seeds = seeds[: args.top]
    rank_filter = None
    if args.ranks:
        rank_filter = {int(part) for part in args.ranks.split(",") if part.strip()}

    rows = []
    for seed in seeds:
        if rank_filter is not None and seed.get("rank") not in rank_filter:
            continue
        if args.max_hw is not None and seed.get("hw_total", 10**9) > args.max_hw:
            continue
        row = seed_to_row(seed, manifest_path)
        if row is not None:
            rows.append(row)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    print(f"wrote {out}: {len(rows)} residual rows")


if __name__ == "__main__":
    main()
