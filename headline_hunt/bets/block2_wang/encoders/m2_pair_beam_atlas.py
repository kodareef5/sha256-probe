#!/usr/bin/env python3
"""
m2_pair_beam_atlas.py - summarize block2_m2_pair_beam JSON artifacts.

The first F535 artifacts can have a stale best_seen_hw field because an
earlier-depth record may fall out of the final beam. This tool recomputes the
true artifact best from top_records plus best_seen_* fields and reports the
disagreement explicitly.
"""

import argparse
import glob
import json
from pathlib import Path


def parse_m2(words):
    out = []
    for word in words or []:
        out.append(int(str(word), 16) & 0xFFFFFFFF)
    return out


def m2_distance(a, b):
    if len(a) != len(b):
        return None
    return sum((x ^ y).bit_count() for x, y in zip(a, b))


def best_record(data):
    best_hw = data.get("best_seen_hw")
    best_m2 = parse_m2(data.get("best_seen_M2"))
    best_lane = data.get("best_seen_lane_hw")
    best_depth = data.get("best_seen_depth")
    best_source = data.get("best_seen_source", "best_seen")

    for rec in data.get("top_records", []):
        hw = rec.get("hw")
        if hw is None:
            continue
        if best_hw is None or hw < best_hw:
            best_hw = hw
            best_m2 = parse_m2(rec.get("M2"))
            best_lane = rec.get("lane_hw")
            best_depth = rec.get("depth")
            best_source = "top_records"

    return {
        "hw": best_hw,
        "m2": best_m2,
        "lane_hw": best_lane,
        "depth": best_depth,
        "source": best_source,
    }


def artifact_rows(paths):
    rows = []
    for raw_path in paths:
        path = Path(raw_path)
        with path.open() as f:
            data = json.load(f)
        best = best_record(data)
        top_best = None
        if data.get("top_records"):
            top_best = min(rec.get("hw") for rec in data["top_records"] if rec.get("hw") is not None)
        reported = data.get("best_seen_hw")
        warn = ""
        if top_best is not None and reported is not None and top_best < reported:
            warn = f"reported_best_stale:{reported}->top:{top_best}"
        init_hw = data.get("init_hw")
        delta = None if init_hw is None or best["hw"] is None else best["hw"] - init_hw
        rows.append({
            "path": path,
            "label": data.get("label") or path.stem,
            "seed_rank": data.get("seed_rank"),
            "init_hw": init_hw,
            "best_hw": best["hw"],
            "delta": delta,
            "depth": best["depth"],
            "source": best["source"],
            "lane_hw": best["lane_hw"],
            "m2": best["m2"],
            "warn": warn,
            "records": data.get("n_new_records"),
            "wall": data.get("wall_seconds"),
        })
    return rows


def fmt_lane(lane):
    if not lane:
        return ""
    return ",".join(str(x) for x in lane)


def emit_markdown(rows, pairwise):
    print("| Artifact | Rank | Init | Best | Delta | Depth | Records | Wall(s) | Lane HW | Source | Warning |")
    print("|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|")
    for row in sorted(rows, key=lambda r: (r["seed_rank"] is None, r["seed_rank"], str(r["path"]))):
        wall = "" if row["wall"] is None else f"{row['wall']:.1f}"
        print(
            f"| `{row['path'].name}` | {row['seed_rank']} | {row['init_hw']} | "
            f"{row['best_hw']} | {row['delta']} | {row['depth']} | {row['records']} | "
            f"{wall} | `{fmt_lane(row['lane_hw'])}` | {row['source']} | {row['warn']} |"
        )

    if pairwise:
        print()
        print("| Pair | M2 bit distance |")
        print("|---|---:|")
        for i, left in enumerate(rows):
            for right in rows[i + 1:]:
                dist = m2_distance(left["m2"], right["m2"])
                print(f"| `{left['label']}` vs `{right['label']}` | {dist} |")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("artifacts", nargs="+", help="JSON artifact path(s), with shell globs allowed.")
    ap.add_argument("--pairwise", action="store_true", help="Also emit pairwise M2 bit distances.")
    args = ap.parse_args()

    paths = []
    for item in args.artifacts:
        expanded = sorted(glob.glob(item))
        paths.extend(expanded or [item])
    rows = artifact_rows(paths)
    emit_markdown(rows, args.pairwise)


if __name__ == "__main__":
    main()
