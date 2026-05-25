#!/usr/bin/env python3
"""Plan shape-reserve triage runs from combo-search artifacts.

The shape-reserve beam is now useful as a calibrated repair-coverability
diagnostic. This helper turns existing combo records into restartable triage
candidates, deduplicates by M2, and marks candidates whose exact M2 was already
used as a beam init.
"""

import argparse
import glob
import json
from pathlib import Path


DEFAULT_GROUPS = ("top_by_hw", "top_by_target_l1", "top_by_cg", "top_records_hw_le_init")


def expand_paths(items):
    paths = []
    for item in items:
        expanded = sorted(glob.glob(item))
        paths.extend(expanded or [item])
    return [Path(path) for path in paths]


def m2_key(words):
    return tuple(f"0x{int(str(word), 16) & 0xFFFFFFFF:08x}" for word in words or [])


def m2_arg(words):
    return ",".join(m2_key(words))


def load_tried(paths):
    tried = {}
    for path in expand_paths(paths):
        data = json.loads(path.read_text())
        init = data.get("init_M2")
        if init:
            tried.setdefault(m2_key(init), []).append({
                "artifact": str(path),
                "label": data.get("label") or path.stem,
                "role": "init_M2",
                "init_hw": data.get("init_hw"),
                "best_seen_hw": data.get("best_seen_hw"),
            })
        best = data.get("best_seen_M2")
        if best:
            tried.setdefault(m2_key(best), []).append({
                "artifact": str(path),
                "label": data.get("label") or path.stem,
                "role": "best_seen_M2",
                "init_hw": data.get("init_hw"),
                "best_seen_hw": data.get("best_seen_hw"),
            })
    return tried


def shape_counts(init_words, words):
    init = [int(str(word), 16) & 0xFFFFFFFF for word in init_words]
    cur = [int(str(word), 16) & 0xFFFFFFFF for word in words]
    added = 0
    removed = 0
    for left, right in zip(init, cur):
        added += ((~left) & right & 0xFFFFFFFF).bit_count()
        removed += (left & (~right) & 0xFFFFFFFF).bit_count()
    return added, removed, added - removed


def record_key(candidate):
    return (
        candidate.get("hw_total", 10**9),
        candidate.get("target_l1", 10**9),
        candidate.get("cg_objective", 10**9),
        candidate.get("radius", 10**9),
        candidate["m2_arg"],
    )


def collect_candidates(combo_paths, groups, per_group, tried):
    by_m2 = {}
    for path in expand_paths(combo_paths):
        data = json.loads(path.read_text())
        init_m2 = data.get("init_M2") or []
        for group in groups:
            records = data.get(group) or []
            for index, record in enumerate(records[:per_group]):
                words = record.get("M2")
                if not words:
                    continue
                key = m2_key(words)
                added, removed, net = shape_counts(init_m2, words)
                candidate = {
                    "source_artifact": str(path),
                    "source_label": data.get("label") or path.stem,
                    "source_group": group,
                    "source_index": index,
                    "seed_jsonl": data.get("seed_jsonl"),
                    "seed_rank": data.get("seed_rank"),
                    "rounds": data.get("rounds"),
                    "parent_hw": data.get("init_hw"),
                    "parent_lane_hw": data.get("init_lane_hw"),
                    "hw_total": record.get("hw_total"),
                    "lane_hw": record.get("lane_hw"),
                    "target_l1": record.get("target_l1"),
                    "cg_objective": record.get("cg_objective"),
                    "radius": record.get("radius"),
                    "bits": record.get("bits"),
                    "pair_ids": record.get("pair_ids"),
                    "m2_added_bits": added,
                    "m2_removed_bits": removed,
                    "m2_net_added_bits": net,
                    "M2": list(key),
                    "m2_arg": ",".join(key),
                    "already_tried": key in tried,
                    "tried_artifacts": tried.get(key, []),
                }
                previous = by_m2.get(key)
                if previous is None or record_key(candidate) < record_key(previous):
                    by_m2[key] = candidate
    return sorted(by_m2.values(), key=record_key)


def beam_command(candidate, args):
    return (
        "python3 headline_hunt/bets/block2_wang/encoders/block2_m2_pair_beam.py "
        f"--seed-jsonl {candidate['seed_jsonl']} "
        f"--rank {candidate['seed_rank']} "
        f"--rounds {candidate['rounds']} "
        f"--init-M2 {candidate['m2_arg']} "
        f"--init-hw {candidate['hw_total']} "
        f"--pair-pool {args.pair_pool} "
        f"--beam-width {args.beam_width} "
        f"--reserve-low-net-width {args.reserve_low_net_width} "
        f"--reserve-low-net-max {args.reserve_low_net_max} "
        f"--reserve-low-net-min-removed {args.reserve_low_net_min_removed} "
        f"--reserve-removed-width {args.reserve_removed_width} "
        f"--reserve-removed-min {args.reserve_removed_min} "
        f"--max-pairs {args.max_pairs} "
        f"--max-radius {args.max_radius} "
        "--top-records 30 "
        "--out OUT.json --label LABEL"
    )


def markdown(candidates, args):
    lines = [
        "# M2 Reserve Triage Plan",
        "",
        "| rank | tried | source | group | idx | parent | HW | target L1 | cg | raw shape | lane |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | ---: | --- | --- |",
    ]
    for rank, candidate in enumerate(candidates[:args.limit], 1):
        lane = ",".join(str(value) for value in candidate.get("lane_hw") or [])
        shape = (
            f"add{candidate['m2_added_bits']}/remove{candidate['m2_removed_bits']}/"
            f"net{candidate['m2_net_added_bits']:+d}"
        )
        lines.append(
            f"| {rank} | {'yes' if candidate['already_tried'] else 'no'} | "
            f"`{Path(candidate['source_artifact']).name}` | {candidate['source_group']} | "
            f"{candidate['source_index']} | {candidate['parent_hw']} | {candidate['hw_total']} | "
            f"{candidate.get('target_l1')} | {candidate.get('cg_objective')} | {shape} | `{lane}` |"
        )
    lines.extend(["", "## First Fresh Commands", ""])
    emitted = 0
    for candidate in candidates:
        if candidate["already_tried"]:
            continue
        lines.extend([
            f"### {candidate['source_label']} {candidate['source_group']}[{candidate['source_index']}]",
            "",
            "```bash",
            beam_command(candidate, args),
            "```",
            "",
        ])
        emitted += 1
        if emitted >= args.command_limit:
            break
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--combo", action="append", required=True, help="Combo artifact path/glob.")
    ap.add_argument("--tried", action="append", default=[], help="Beam artifact path/glob to mark tried M2s.")
    ap.add_argument("--group", action="append", default=[], help="Record group to scan; default scans common groups.")
    ap.add_argument("--per-group", type=int, default=20)
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--command-limit", type=int, default=5)
    ap.add_argument("--pair-pool", type=int, default=1024)
    ap.add_argument("--beam-width", type=int, default=1024)
    ap.add_argument("--reserve-low-net-width", type=int, default=384)
    ap.add_argument("--reserve-low-net-max", type=int, default=4)
    ap.add_argument("--reserve-low-net-min-removed", type=int, default=1)
    ap.add_argument("--reserve-removed-width", type=int, default=128)
    ap.add_argument("--reserve-removed-min", type=int, default=2)
    ap.add_argument("--max-pairs", type=int, default=6)
    ap.add_argument("--max-radius", type=int, default=12)
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown-out")
    args = ap.parse_args()

    groups = tuple(args.group) if args.group else DEFAULT_GROUPS
    tried = load_tried(args.tried)
    candidates = collect_candidates(args.combo, groups, args.per_group, tried)
    for candidate in candidates:
        candidate["command_template"] = beam_command(candidate, args)

    payload = {
        "description": "M2 shape-reserve triage plan from combo records",
        "groups": groups,
        "per_group": args.per_group,
        "candidate_count": len(candidates),
        "tried_count": sum(1 for candidate in candidates if candidate["already_tried"]),
        "candidates": candidates,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    if args.markdown_out:
        md_out = Path(args.markdown_out)
        md_out.parent.mkdir(parents=True, exist_ok=True)
        md_out.write_text(markdown(candidates, args))
        print(f"wrote {out} and {md_out}")
    else:
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
