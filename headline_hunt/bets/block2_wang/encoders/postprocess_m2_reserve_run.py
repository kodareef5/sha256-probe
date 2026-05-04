#!/usr/bin/env python3
"""Postprocess a shape-reserve M2 beam run.

This wraps the reserve-triage follow-up loop:

* extract mixed restart candidates from frontier summaries;
* compare the run against calibration/control artifacts;
* write a small verdict note with a consistent pass/weak/closed label.
"""

import argparse
import json
import re
from pathlib import Path

import extract_m2_frontier_candidates as extractor
import summarize_m2_beam_frontiers as summarizer


def artifact_prefix(path):
    match = re.match(r"(?P<date>\d{8})_F(?P<num>\d+)_(?P<tag>.+)$", path.stem)
    if not match:
        raise ValueError(f"artifact name does not start with YYYYMMDD_FNNN_: {path.name}")
    return match.group("date"), int(match.group("num")), match.group("tag")


def default_outputs(path, args):
    date, run_num, tag = artifact_prefix(path)
    run_token = f"f{run_num}"
    out_dir = Path(args.out_dir) if args.out_dir else path.parent
    if args.tag:
        run_token = args.tag

    return {
        "extract_jsonl": out_dir / f"{date}_F{run_num + 1}_{run_token}_mixed_candidates.jsonl",
        "extract_md": out_dir / f"{date}_F{run_num + 1}_{run_token}_mixed_candidates.md",
        "summary_json": out_dir / f"{date}_F{run_num + 2}_{run_token}_reserve_comparison.json",
        "summary_md": out_dir / f"{date}_F{run_num + 2}_{run_token}_reserve_comparison.md",
        "verdict_md": out_dir / f"{date}_F{run_num + 3}_{run_token}_reserve_verdict.md",
        "source_tag": tag,
    }


def ensure_outputs_available(outputs, force):
    paths = [
        outputs["extract_jsonl"],
        outputs["extract_md"],
        outputs["summary_json"],
        outputs["summary_md"],
        outputs["verdict_md"],
    ]
    existing = [path for path in paths if path.exists()]
    if existing and not force:
        names = ", ".join(str(path) for path in existing)
        raise FileExistsError(f"output already exists; use --force to overwrite: {names}")


def format_shape(state_or_summary):
    if not state_or_summary:
        return ""
    added = state_or_summary.get("m2_added_bits")
    removed = state_or_summary.get("m2_removed_bits")
    net = state_or_summary.get("m2_net_added_bits")
    if added is None:
        added = state_or_summary.get("best_seen_m2_added_bits")
        removed = state_or_summary.get("best_seen_m2_removed_bits")
        net = state_or_summary.get("best_seen_m2_net_added_bits")
    if added is None:
        return ""
    return f"add{added}/remove{removed}/net{net:+d}"


def state_cell(state):
    if not state:
        return ""
    lane = ",".join(str(value) for value in state.get("lane_hw") or [])
    return f"HW{state.get('hw')} {format_shape(state)} lane[{lane}]"


def unique_states(data):
    seen = set()
    states = []
    for frontier in data.get("frontier_summaries") or []:
        for state in extractor.collect_states(frontier):
            bits = tuple(sorted(state.get("bits") or []))
            if not bits or bits in seen:
                continue
            seen.add(bits)
            states.append(state)
    return states


def mixed_state_sort_key(state):
    return (
        state.get("hw", 10**9),
        state.get("m2_net_added_bits", 10**9),
        -state.get("m2_removed_bits", 0),
        state.get("depth", 10**9),
        state.get("bits", []),
    )


def best_mixed(states, max_net_added, min_removed):
    mixed = [
        state for state in states
        if state.get("m2_removed_bits", 0) >= min_removed
        and state.get("m2_net_added_bits", 10**9) <= max_net_added
    ]
    if not mixed:
        return None
    return sorted(mixed, key=mixed_state_sort_key)[0]


def final_frontier(data):
    frontiers = data.get("frontier_summaries") or []
    if not frontiers:
        return None
    return max(frontiers, key=lambda item: item.get("depth", -1))


def classify(data, max_net_added, min_removed):
    init_hw = data.get("init_hw")
    best_hw = data.get("best_seen_hw")
    best_summary = {
        "hw": best_hw,
        "m2_added_bits": data.get("best_seen_m2_added_bits"),
        "m2_removed_bits": data.get("best_seen_m2_removed_bits"),
        "m2_net_added_bits": data.get("best_seen_m2_net_added_bits"),
        "lane_hw": data.get("best_seen_lane_hw"),
    }
    states = unique_states(data)
    any_mixed = best_mixed(states, max_net_added, min_removed)
    frontier = final_frontier(data)
    final_mixed = best_mixed(
        extractor.collect_states(frontier) if frontier else [],
        max_net_added,
        min_removed,
    )

    best_is_mixed = (
        data.get("best_seen_m2_removed_bits", 0) >= min_removed
        and data.get("best_seen_m2_net_added_bits", 10**9) <= max_net_added
    )
    global_mixed_improves = (
        init_hw is not None
        and best_hw is not None
        and best_hw < init_hw
        and best_is_mixed
    )
    final_mixed_improves = (
        init_hw is not None
        and final_mixed is not None
        and final_mixed.get("hw", 10**9) < init_hw
    )
    any_mixed_improves = (
        init_hw is not None
        and any_mixed is not None
        and any_mixed.get("hw", 10**9) < init_hw
    )
    global_improves = init_hw is not None and best_hw is not None and best_hw < init_hw

    if global_mixed_improves or final_mixed_improves:
        verdict = "pass"
        reason = "mixed low-net reserve reached a better-than-init HW"
    elif global_improves or any_mixed_improves:
        verdict = "weak"
        reason = "run improved, but not through the calibrated final mixed-low-net channel"
    else:
        verdict = "closed"
        reason = "no better-than-init mixed low-net repair appeared"

    return {
        "artifact": data.get("_artifact"),
        "label": data.get("label"),
        "init_hw": init_hw,
        "best_hw": best_hw,
        "best_depth": data.get("best_seen_depth"),
        "best_shape": format_shape(best_summary),
        "best_state": best_summary,
        "best_mixed": any_mixed,
        "final_mixed": final_mixed,
        "verdict": verdict,
        "reason": reason,
    }


def read_artifact(path):
    data = json.loads(path.read_text())
    data["_artifact"] = path.name
    return data


def write_extract(artifact_path, outputs, args):
    ns = argparse.Namespace(
        max_hw=args.max_hw,
        min_removed=args.min_removed,
        max_net_added=args.max_net_added,
        min_depth=args.min_depth,
        max_depth=args.max_depth,
        per_depth=args.per_depth,
    )
    candidates = extractor.extract_from_artifact(artifact_path, ns)
    candidates.sort(key=extractor.state_sort_key)
    outputs["extract_jsonl"].parent.mkdir(parents=True, exist_ok=True)
    outputs["extract_jsonl"].write_text(
        "".join(json.dumps(candidate) + "\n" for candidate in candidates)
    )
    outputs["extract_md"].write_text(extractor.markdown(candidates))
    return candidates


def write_summary(paths, outputs):
    summaries = []
    rows = []
    for path in paths:
        summary, artifact_rows = summarizer.load_artifact(path)
        summaries.append(summary)
        rows.extend(artifact_rows)
    payload = {
        "description": "M2 reserve postprocess comparison",
        "summaries": summaries,
        "rows": rows,
    }
    outputs["summary_json"].write_text(json.dumps(payload, indent=2) + "\n")
    outputs["summary_md"].write_text(summarizer.markdown(summaries, rows))
    return summaries


def next_plan_candidate(plan_path, current_data):
    if not plan_path:
        return None
    plan = json.loads(Path(plan_path).read_text())
    current_key = tuple(str(word).lower() for word in current_data.get("init_M2") or [])
    for candidate in plan.get("candidates") or []:
        candidate_key = tuple(str(word).lower() for word in candidate.get("M2") or [])
        if candidate.get("already_tried"):
            continue
        if candidate_key == current_key:
            continue
        return candidate
    return None


def write_verdict(run_result, control_results, candidates, next_candidate, outputs, args):
    lines = [
        f"# {run_result['label'] or outputs['source_tag']} Reserve Verdict",
        "",
        f"Verdict: **{run_result['verdict']}** - {run_result['reason']}.",
        "",
        "| artifact | verdict | init | best | best shape | best mixed | final mixed |",
        "| --- | --- | ---: | ---: | --- | --- | --- |",
    ]
    for result in [run_result] + control_results:
        lines.append(
            f"| `{result['artifact']}` | {result['verdict']} | {result['init_hw']} | "
            f"{result['best_hw']} d{result['best_depth']} | {result['best_shape']} | "
            f"{state_cell(result['best_mixed'])} | {state_cell(result['final_mixed'])} |"
        )

    lines.extend([
        "",
        "## Extracted Mixed Candidates",
        "",
        f"- Count: {len(candidates)}",
        f"- Filter: HW <= {args.max_hw}, removed >= {args.min_removed}, net added <= {args.max_net_added}",
    ])
    if candidates:
        top = candidates[0]
        lane = ",".join(str(value) for value in top.get("lane_hw") or [])
        lines.append(
            f"- Best extracted: HW{top.get('hw')} {top.get('m2_shape')} "
            f"depth {top.get('source_depth')} lane[{lane}]"
        )

    lines.extend(["", "## Next Action", ""])
    if run_result["verdict"] == "pass":
        lines.append(
            "Deepen from the best extracted mixed candidate before moving to the next fresh triage target."
        )
    elif run_result["verdict"] == "weak":
        lines.append(
            "Treat as a weak false-positive unless a short deepen from the best mixed candidate improves."
        )
    else:
        lines.append("Move to the next fresh reserve-triage target.")

    if next_candidate:
        source = Path(next_candidate["source_artifact"]).name
        lines.extend([
            "",
            f"Suggested next fresh plan row: `{source}` "
            f"{next_candidate['source_group']}[{next_candidate['source_index']}] "
            f"HW{next_candidate['hw_total']} target_l1 {next_candidate.get('target_l1')} "
            f"cg {next_candidate.get('cg_objective')}.",
            "",
            "```bash",
            next_candidate["command_template"],
            "```",
        ])

    outputs["verdict_md"].write_text("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("artifact", help="Primary shape-reserve beam JSON artifact.")
    ap.add_argument("--compare", action="append", default=[], help="Control/comparison artifact.")
    ap.add_argument("--plan", help="Reserve triage plan JSON for next-candidate suggestion.")
    ap.add_argument("--out-dir", help="Output directory; default uses artifact directory.")
    ap.add_argument("--tag", help="Short output tag; default uses fNNN from artifact name.")
    ap.add_argument("--max-hw", type=int, default=91)
    ap.add_argument("--min-removed", type=int, default=1)
    ap.add_argument("--max-net-added", type=int, default=4)
    ap.add_argument("--min-depth", type=int)
    ap.add_argument("--max-depth", type=int)
    ap.add_argument("--per-depth", type=int, default=8)
    ap.add_argument("--force", action="store_true", help="Overwrite existing output files.")
    args = ap.parse_args()

    artifact_path = Path(args.artifact)
    outputs = default_outputs(artifact_path, args)
    ensure_outputs_available(outputs, args.force)
    run_data = read_artifact(artifact_path)
    control_data = [read_artifact(Path(path)) for path in args.compare]

    candidates = write_extract(artifact_path, outputs, args)
    write_summary([Path(path) for path in args.compare] + [artifact_path], outputs)

    run_result = classify(run_data, args.max_net_added, args.min_removed)
    control_results = [
        classify(data, args.max_net_added, args.min_removed)
        for data in control_data
    ]
    next_candidate = next_plan_candidate(args.plan, run_data)
    write_verdict(run_result, control_results, candidates, next_candidate, outputs, args)

    print(f"wrote {outputs['extract_jsonl']} and {outputs['extract_md']}")
    print(f"wrote {outputs['summary_json']} and {outputs['summary_md']}")
    print(f"wrote {outputs['verdict_md']}")
    print(f"verdict {run_result['verdict']}: {run_result['reason']}")


if __name__ == "__main__":
    main()
