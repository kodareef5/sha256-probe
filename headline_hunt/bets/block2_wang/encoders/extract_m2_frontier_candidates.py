#!/usr/bin/env python3
"""Extract restartable M2 candidates from pair-beam frontier summaries.

Frontier summaries store compact states as bit flips relative to the artifact
init_M2. This tool reconstructs those M2 words and filters candidates by
repair shape so follow-up beams can restart from non-record frontier states.
"""

import argparse
import glob
import json
from pathlib import Path

MASK = 0xFFFFFFFF


def expand_paths(items):
    paths = []
    for item in items:
        expanded = sorted(glob.glob(item))
        paths.extend(expanded or [item])
    return [Path(path) for path in paths]


def parse_words(words):
    return [int(str(word), 16) & MASK for word in words]


def format_words(words):
    return [f"0x{word:08x}" for word in words]


def m2_arg(words):
    return ",".join(format_words(words))


def apply_bits(base_words, bits):
    words = list(base_words)
    for bit_idx in bits:
        word_idx = bit_idx // 32
        bit = bit_idx % 32
        words[word_idx] ^= 1 << bit
    return words


def state_sort_key(state):
    return (
        state.get("hw", 10**9),
        state.get("objective", state.get("hw", 10**9)),
        state.get("depth", 0),
        state.get("bits", []),
    )


def collect_states(frontier):
    states = []
    states.extend(frontier.get("top_by_hw") or [])
    states.extend(frontier.get("top_by_objective") or [])
    for key in (
        "best_by_shape",
        "best_by_net_added",
        "best_by_removed_bits",
        "best_by_added_bits",
    ):
        for item in frontier.get(key) or []:
            best = item.get("best")
            if best:
                states.append(best)
    return states


def passes_filters(state, args):
    if args.max_hw is not None and state.get("hw", 10**9) > args.max_hw:
        return False
    if args.min_removed is not None and state.get("m2_removed_bits", 0) < args.min_removed:
        return False
    if args.max_net_added is not None and state.get("m2_net_added_bits", 10**9) > args.max_net_added:
        return False
    if args.min_depth is not None and state.get("depth", 0) < args.min_depth:
        return False
    if args.max_depth is not None and state.get("depth", 0) > args.max_depth:
        return False
    return True


def extract_from_artifact(path, args):
    data = json.loads(path.read_text())
    base_m2 = parse_words(data["init_M2"])
    label = data.get("label") or path.stem
    seen = set()
    candidates = []
    for frontier in data.get("frontier_summaries") or []:
        depth_states = []
        for state in collect_states(frontier):
            bits = tuple(sorted(state.get("bits") or []))
            if not bits or bits in seen:
                continue
            if not passes_filters(state, args):
                continue
            seen.add(bits)
            words = apply_bits(base_m2, bits)
            depth_states.append({
                "source_artifact": str(path),
                "source_label": label,
                "seed_jsonl": data.get("seed_jsonl"),
                "seed_rank": data.get("seed_rank"),
                "rounds": data.get("rounds"),
                "source_depth": state.get("depth"),
                "hw": state.get("hw"),
                "objective": state.get("objective"),
                "lane_hw": state.get("lane_hw"),
                "m2_weight": state.get("m2_weight"),
                "m2_added_bits": state.get("m2_added_bits"),
                "m2_removed_bits": state.get("m2_removed_bits"),
                "m2_net_added_bits": state.get("m2_net_added_bits"),
                "m2_shape": state.get("m2_shape"),
                "bits": list(bits),
                "M2": format_words(words),
                "init_M2_arg": m2_arg(words),
            })
        depth_states.sort(key=state_sort_key)
        candidates.extend(depth_states[:args.per_depth])
    candidates.sort(key=state_sort_key)
    return candidates


def markdown(candidates):
    lines = [
        "# M2 Frontier Candidates",
        "",
        "| source | depth | HW | shape | M2 wt | lane | bits |",
        "| --- | ---: | ---: | --- | ---: | --- | --- |",
    ]
    for candidate in candidates:
        lane = ",".join(str(value) for value in candidate.get("lane_hw") or [])
        lines.append(
            f"| `{Path(candidate['source_artifact']).name}` | {candidate['source_depth']} | "
            f"{candidate['hw']} | {candidate['m2_shape']} | {candidate['m2_weight']} | "
            f"`{lane}` | {candidate['bits']} |"
        )
    lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("artifacts", nargs="+", help="JSON artifacts, with shell globs allowed.")
    ap.add_argument("--max-hw", type=int)
    ap.add_argument("--min-removed", type=int)
    ap.add_argument("--max-net-added", type=int)
    ap.add_argument("--min-depth", type=int)
    ap.add_argument("--max-depth", type=int)
    ap.add_argument("--per-depth", type=int, default=8)
    ap.add_argument("--out", required=True, help="JSONL output path.")
    ap.add_argument("--markdown-out")
    args = ap.parse_args()

    candidates = []
    for path in expand_paths(args.artifacts):
        candidates.extend(extract_from_artifact(path, args))
    candidates.sort(key=state_sort_key)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("".join(json.dumps(candidate) + "\n" for candidate in candidates))
    if args.markdown_out:
        md_out = Path(args.markdown_out)
        md_out.parent.mkdir(parents=True, exist_ok=True)
        md_out.write_text(markdown(candidates))
        print(f"wrote {out} and {md_out} ({len(candidates)} candidates)")
    else:
        print(f"wrote {out} ({len(candidates)} candidates)")


if __name__ == "__main__":
    main()
