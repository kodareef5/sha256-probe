#!/usr/bin/env python3
"""Materialize concrete commands from an M2 reserve triage plan.

The planner intentionally emits reusable command templates with OUT.json and
LABEL placeholders. This helper turns the next fresh rows into named artifacts
so a long reserve-triage queue can be launched without manual label edits.
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path


def m2_key(words):
    return tuple(str(word).lower() for word in words or [])


def parse_m2_arg(value):
    return tuple(part.strip().lower() for part in value.split(",") if part.strip())


def source_token(label):
    match = re.match(r"F(?P<num>\d+)_", label or "")
    if match:
        return f"f{match.group('num')}"
    return re.sub(r"[^a-zA-Z0-9]+", "_", label or "source").strip("_").lower()[:24]


def group_token(group, index):
    return re.sub(r"[^a-zA-Z0-9]+", "_", f"{group}{index}").strip("_").lower()


def command_label(run_id, candidate):
    src = source_token(candidate.get("source_label"))
    group = group_token(candidate.get("source_group"), candidate.get("source_index"))
    hw = candidate.get("hw_total")
    return f"F{run_id}_{src}_{group}_hw{hw}_shape_reserve_beam"


def materialize(candidate, run_id, date, out_dir):
    label = command_label(run_id, candidate)
    out_path = Path(out_dir) / f"{date}_{label}.json"
    command = candidate["command_template"].replace("OUT.json", str(out_path))
    command = command.replace("LABEL", label)
    return {
        "run_id": run_id,
        "date": date,
        "label": label,
        "out": str(out_path),
        "source_artifact": candidate.get("source_artifact"),
        "source_label": candidate.get("source_label"),
        "source_group": candidate.get("source_group"),
        "source_index": candidate.get("source_index"),
        "hw_total": candidate.get("hw_total"),
        "target_l1": candidate.get("target_l1"),
        "cg_objective": candidate.get("cg_objective"),
        "m2_added_bits": candidate.get("m2_added_bits"),
        "m2_removed_bits": candidate.get("m2_removed_bits"),
        "m2_net_added_bits": candidate.get("m2_net_added_bits"),
        "M2": candidate.get("M2"),
        "command": command,
    }


def load_skip_keys(paths, m2_args):
    keys = set()
    for value in m2_args:
        keys.add(parse_m2_arg(value))
    for raw_path in paths:
        data = json.loads(Path(raw_path).read_text())
        for key in ("init_M2", "best_seen_M2"):
            words = data.get(key)
            if words:
                keys.add(m2_key(words))
    return keys


def collect(plan, skip_keys, limit):
    rows = []
    for candidate in plan.get("candidates") or []:
        if candidate.get("already_tried"):
            continue
        if m2_key(candidate.get("M2")) in skip_keys:
            continue
        rows.append(candidate)
        if len(rows) >= limit:
            break
    return rows


def markdown(commands):
    lines = [
        "# Materialized M2 Reserve Commands",
        "",
        "| run | source | group | HW | target L1 | cg | shape | out |",
        "| ---: | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for item in commands:
        shape = (
            f"add{item['m2_added_bits']}/remove{item['m2_removed_bits']}/"
            f"net{item['m2_net_added_bits']:+d}"
        )
        lines.append(
            f"| F{item['run_id']} | `{Path(item['source_artifact']).name}` | "
            f"{item['source_group']}[{item['source_index']}] | {item['hw_total']} | "
            f"{item['target_l1']} | {item['cg_objective']} | {shape} | `{Path(item['out']).name}` |"
        )
    lines.extend(["", "## Commands", ""])
    for item in commands:
        lines.extend([f"### {item['label']}", "", "```bash", item["command"], "```", ""])
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("plan", help="M2 reserve triage plan JSON.")
    ap.add_argument("--skip-artifact", action="append", default=[], help="Artifact whose init/best M2 should be skipped.")
    ap.add_argument("--skip-m2", action="append", default=[], help="Comma-separated M2 words to skip.")
    ap.add_argument("--date", default=datetime.now().strftime("%Y%m%d"))
    ap.add_argument("--start-id", type=int, required=True)
    ap.add_argument("--id-step", type=int, default=1, help="Increment between materialized run IDs.")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--out-dir", default="headline_hunt/bets/block2_wang/results/search_artifacts")
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown-out")
    args = ap.parse_args()

    plan = json.loads(Path(args.plan).read_text())
    skip_keys = load_skip_keys(args.skip_artifact, args.skip_m2)
    rows = collect(plan, skip_keys, args.limit)
    commands = [
        materialize(candidate, args.start_id + index * args.id_step, args.date, args.out_dir)
        for index, candidate in enumerate(rows)
    ]

    payload = {
        "description": "Concrete M2 reserve triage commands",
        "plan": args.plan,
        "date": args.date,
        "start_id": args.start_id,
        "id_step": args.id_step,
        "limit": args.limit,
        "skip_artifacts": args.skip_artifact,
        "skip_m2": args.skip_m2,
        "commands": commands,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    if args.markdown_out:
        md_out = Path(args.markdown_out)
        md_out.parent.mkdir(parents=True, exist_ok=True)
        md_out.write_text(markdown(commands))
        print(f"wrote {out} and {md_out} ({len(commands)} commands)")
    else:
        print(f"wrote {out} ({len(commands)} commands)")


if __name__ == "__main__":
    main()
