#!/usr/bin/env python3
"""Summarize block2_m2_pair_beam frontier diagnostics.

The frontier summaries added to block2_m2_pair_beam.py keep compact
per-depth shape buckets for the retained beam. This report is meant to compare
successful and failed repair branches without opening large JSON artifacts by
hand.
"""

import argparse
import glob
import json
from pathlib import Path


def expand_paths(items):
    paths = []
    for item in items:
        expanded = sorted(glob.glob(item))
        paths.extend(expanded or [item])
    return [Path(path) for path in paths]


def fmt_lane(lane):
    if not lane:
        return ""
    return ",".join(str(value) for value in lane)


def fmt_hist(items, limit=4):
    if not items:
        return ""
    return ", ".join(
        f"{item['bucket']}x{item['count']}"
        for item in items[:limit]
    )


def fmt_selection(passes):
    if not passes:
        return ""
    return ", ".join(
        f"{item['pass']}:{item.get('added', 0)}/{item.get('limit', 0)}"
        for item in passes
    )


def state_cell(state):
    if not state:
        return ""
    return (
        f"HW{state['hw']} {state['m2_shape']} "
        f"wt{state['m2_weight']} lane[{fmt_lane(state['lane_hw'])}]"
    )


def best_bucket_cell(items, predicate):
    for item in items or []:
        bucket = item.get("bucket")
        try:
            bucket_value = int(bucket)
        except (TypeError, ValueError):
            continue
        if predicate(bucket_value):
            return f"{bucket}: {state_cell(item.get('best'))}"
    return ""


def load_artifact(path):
    data = json.loads(path.read_text())
    label = data.get("label") or path.stem
    frontiers = data.get("frontier_summaries") or []
    selection_by_depth = {
        item.get("depth"): item.get("passes") or []
        for item in data.get("beam_selection_summaries") or []
    }
    summary = {
        "path": str(path),
        "artifact": path.name,
        "label": label,
        "init_hw": data.get("init_hw"),
        "init_lane_hw": data.get("init_lane_hw"),
        "init_m2_weight": data.get("init_m2_weight"),
        "best_seen_hw": data.get("best_seen_hw"),
        "best_seen_depth": data.get("best_seen_depth"),
        "best_seen_source": data.get("best_seen_source"),
        "best_seen_lane_hw": data.get("best_seen_lane_hw"),
        "best_seen_m2_weight": data.get("best_seen_m2_weight"),
        "best_seen_m2_added_bits": data.get("best_seen_m2_added_bits"),
        "best_seen_m2_removed_bits": data.get("best_seen_m2_removed_bits"),
        "best_seen_m2_net_added_bits": data.get("best_seen_m2_net_added_bits"),
        "n_new_records": data.get("n_new_records"),
        "wall_seconds": data.get("wall_seconds"),
        "frontier_count": len(frontiers),
        "reserve_low_net_width": data.get("reserve_low_net_width", 0),
        "reserve_low_net_max": data.get("reserve_low_net_max"),
        "reserve_low_net_min_removed": data.get("reserve_low_net_min_removed"),
        "reserve_removed_width": data.get("reserve_removed_width", 0),
        "reserve_removed_min": data.get("reserve_removed_min"),
    }
    rows = []
    for frontier in frontiers:
        top_state = (frontier.get("top_by_hw") or [{}])[0]
        best_objective_state = (frontier.get("top_by_objective") or [{}])[0]
        rows.append({
            "label": label,
            "artifact": path.name,
            "depth": frontier.get("depth"),
            "candidate_count": frontier.get("candidate_count"),
            "kept_count": frontier.get("kept_count"),
            "selection_passes": selection_by_depth.get(frontier.get("depth"), []),
            "best_hw": frontier.get("best_hw"),
            "best_objective": frontier.get("best_objective"),
            "best_state": top_state,
            "best_objective_state": best_objective_state,
            "shape_hist_top": frontier.get("shape_hist_top") or [],
            "net_added_hist_top": frontier.get("net_added_hist_top") or [],
            "removed_bits_hist_top": frontier.get("removed_bits_hist_top") or [],
            "best_positive_removed": best_bucket_cell(
                frontier.get("best_by_removed_bits"),
                lambda value: value > 0,
            ),
            "best_low_net": best_bucket_cell(
                frontier.get("best_by_net_added"),
                lambda value: value <= 4,
            ),
        })
    return summary, rows


def markdown(summaries, rows):
    lines = [
        "# M2 Beam Frontier Comparison",
        "",
        "| artifact | init | best | depth | records | best shape | reserves | wall(s) |",
        "| --- | ---: | ---: | ---: | ---: | --- | --- | ---: |",
    ]
    for summary in summaries:
        shape = (
            f"add{summary['best_seen_m2_added_bits']}_"
            f"remove{summary['best_seen_m2_removed_bits']}_"
            f"net{summary['best_seen_m2_net_added_bits']:+d}"
            if summary["best_seen_m2_added_bits"] is not None
            else ""
        )
        wall = summary["wall_seconds"]
        wall_cell = "" if wall is None else f"{wall:.1f}"
        reserves = ""
        if summary["reserve_low_net_width"] or summary["reserve_removed_width"]:
            reserves = (
                f"low-net {summary['reserve_low_net_width']} "
                f"(net<={summary['reserve_low_net_max']}, rem>={summary['reserve_low_net_min_removed']}), "
                f"removed {summary['reserve_removed_width']} "
                f"(rem>={summary['reserve_removed_min']})"
            )
        lines.append(
            f"| `{summary['artifact']}` | {summary['init_hw']} | "
            f"{summary['best_seen_hw']} | {summary['best_seen_depth']} | "
            f"{summary['n_new_records']} | {shape} | {reserves} | {wall_cell} |"
        )

    lines.extend([
        "",
        "| artifact | d | candidates | kept | selection | best | shape hist | removed hist | net hist | best removed | best low-net |",
        "| --- | ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |",
    ])
    for row in rows:
        lines.append(
            f"| `{row['artifact']}` | {row['depth']} | {row['candidate_count']} | "
            f"{row['kept_count']} | {fmt_selection(row['selection_passes'])} | "
            f"{state_cell(row['best_state'])} | "
            f"{fmt_hist(row['shape_hist_top'])} | {fmt_hist(row['removed_bits_hist_top'])} | "
            f"{fmt_hist(row['net_added_hist_top'])} | {row['best_positive_removed']} | "
            f"{row['best_low_net']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("artifacts", nargs="+", help="JSON artifacts, with shell globs allowed.")
    ap.add_argument("--out", required=True)
    ap.add_argument("--markdown-out")
    args = ap.parse_args()

    summaries = []
    rows = []
    for path in expand_paths(args.artifacts):
        summary, artifact_rows = load_artifact(path)
        summaries.append(summary)
        rows.extend(artifact_rows)

    payload = {
        "description": "M2 pair-beam frontier comparison",
        "summaries": summaries,
        "rows": rows,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n")
    if args.markdown_out:
        md_out = Path(args.markdown_out)
        md_out.parent.mkdir(parents=True, exist_ok=True)
        md_out.write_text(markdown(summaries, rows))
        print(f"wrote {out} and {md_out}")
    else:
        print(f"wrote {out}")


if __name__ == "__main__":
    main()
