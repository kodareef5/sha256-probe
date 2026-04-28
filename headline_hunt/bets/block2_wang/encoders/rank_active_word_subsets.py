#!/usr/bin/env python3
"""
rank_active_word_subsets.py - rank message-word masks by expansion geometry.

This is a structural prefilter for active_subset_scan.py. It does not run the
absorber search. Instead, it asks which W[0..15] active-word subsets create
concentrated one-hop overlap in the SHA-256 message expansion:

    W[i] = sigma1(W[i-2]) + W[i-7] + sigma0(W[i-15]) + W[i-16]

F150 used total overlap density. F128 showed that total density alone was a
weak predictor, so this tool exposes concentration and feed-channel features.
"""
import argparse
import itertools
import json
import os
import sys


REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
sys.path.insert(0, REPO)

from headline_hunt.bets.block2_wang.encoders.search_block2_absorption import (
    parse_active_words,
)


FEEDS = (
    ("sigma1", 2),
    ("minus7", 7),
    ("sigma0", 15),
    ("minus16", 16),
)


def parse_sizes(spec):
    sizes = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = [int(x) for x in part.split("-", 1)]
            sizes.extend(range(lo, hi + 1))
        else:
            sizes.append(int(part))
    sizes = sorted(set(sizes))
    if not sizes or any(n < 1 or n > 16 for n in sizes):
        raise ValueError("--sizes must name subset sizes in [1,16]")
    return sizes


def iter_subsets(pool, sizes, include):
    pool = sorted(set(pool))
    include = sorted(set(include))
    missing = [w for w in include if w not in pool]
    if missing:
        raise ValueError(f"--include words are absent from --pool: {missing}")

    rest = [w for w in pool if w not in include]
    for size in sizes:
        if size < len(include) or size > len(pool):
            continue
        for extra in itertools.combinations(rest, size - len(include)):
            yield tuple(sorted(include + list(extra)))


def profile_subset(subset, early_limit):
    active = set(subset)
    targets = []
    channel_counts = {name: 0 for name, _ in FEEDS}
    mixed_channel_targets = 0
    identity_mixed_targets = 0

    for target in range(16, 64):
        feeds = []
        for channel, offset in FEEDS:
            source = target - offset
            if source in active:
                feeds.append({"source": source, "channel": channel})
                channel_counts[channel] += 1
        if feeds:
            channels = {feed["channel"] for feed in feeds}
            identities = {"minus7", "minus16"}
            nonlinear = {"sigma0", "sigma1"}
            mixed = len(channels) > 1
            identity_mixed = bool(channels & identities) and bool(channels & nonlinear)
            if mixed and len(feeds) >= 2:
                mixed_channel_targets += 1
            if identity_mixed and len(feeds) >= 2:
                identity_mixed_targets += 1
            targets.append({
                "target": target,
                "feeds": feeds,
                "fan_in": len(feeds),
                "overlap": len(feeds) >= 2,
                "early": target <= early_limit,
                "mixed_channels": mixed,
                "identity_mixed": identity_mixed,
            })

    overlap_targets = [t for t in targets if t["overlap"]]
    early_overlap_targets = [t for t in overlap_targets if t["early"]]
    triple_targets = [t for t in overlap_targets if t["fan_in"] >= 3]
    early_triple_targets = [t for t in early_overlap_targets if t["fan_in"] >= 3]
    extra_feeds = sum(t["fan_in"] - 1 for t in overlap_targets)
    early_extra_feeds = sum(t["fan_in"] - 1 for t in early_overlap_targets)
    max_fan_in = max((t["fan_in"] for t in targets), default=0)
    early_max_fan_in = max((t["fan_in"] for t in targets if t["early"]), default=0)

    concentration_score = (
        early_extra_feeds * 8
        + len(early_triple_targets) * 14
        + extra_feeds * 4
        + early_max_fan_in * 3
        + identity_mixed_targets * 2
        - len(overlap_targets) * 2
    )

    return {
        "active_words": list(subset),
        "rank_score": concentration_score,
        "extra_feeds": extra_feeds,
        "overlap_targets": len(overlap_targets),
        "early_extra_feeds": early_extra_feeds,
        "early_overlap_targets": len(early_overlap_targets),
        "max_fan_in": max_fan_in,
        "early_max_fan_in": early_max_fan_in,
        "triple_targets": len(triple_targets),
        "early_triple_targets": len(early_triple_targets),
        "mixed_channel_targets": mixed_channel_targets,
        "identity_mixed_targets": identity_mixed_targets,
        "channel_counts": channel_counts,
        "targets": targets,
    }


def active_words_from_run(run):
    m1 = run.get("M1")
    m2 = run.get("M2")
    if not m1 or not m2:
        return None
    words = []
    for idx, (a, b) in enumerate(zip(m1, m2)):
        if int(a, 16) ^ int(b, 16):
            words.append(idx)
    return tuple(words)


def add_observed(observed, key, run, source):
    if not key:
        return
    current = observed.get(key)
    score = run.get("score")
    msg_hw = run.get("message_diff_hw")
    if score is None:
        return
    candidate = {
        "score": score,
        "message_diff_hw": msg_hw,
        "source": source,
    }
    if current is None or (score, msg_hw or 9999) < (
        current["score"],
        current.get("message_diff_hw") or 9999,
    ):
        observed[key] = candidate


def load_observed(paths):
    observed = {}
    for path in paths:
        with open(path) as f:
            data = json.load(f)
        for run in data.get("results", []):
            add_observed(observed, active_words_from_run(run), run, path)
        if data.get("best"):
            add_observed(observed, active_words_from_run(data["best"]), data["best"], path)
        for subset in data.get("subsets", []):
            best = subset.get("best")
            if not best:
                continue
            add_observed(observed, tuple(subset["active_words"]), best, path)
            add_observed(observed, active_words_from_run(best), best, path)
    return observed


def target_signature(entry, limit):
    parts = []
    overlap_targets = [t for t in entry["targets"] if t["overlap"]]
    overlap_targets.sort(key=lambda t: (-t["fan_in"], t["target"]))
    for target in overlap_targets[:limit]:
        feeds = ",".join(f"{feed['source']}:{feed['channel']}" for feed in target["feeds"])
        parts.append(f"W{target['target']}[{feeds}]")
    return "; ".join(parts)


def sort_key(entry):
    return (
        -entry["rank_score"],
        -entry["early_extra_feeds"],
        -entry["early_triple_targets"],
        -entry["extra_feeds"],
        entry["overlap_targets"],
        entry["active_words"],
    )


def print_table(entries, top_n, signature_limit):
    print("rank  hscore  extra early  fan triple  mixed  observed  active  overlaps")
    for rank, entry in enumerate(entries[:top_n], 1):
        active = ",".join(str(w) for w in entry["active_words"])
        observed = entry.get("observed")
        if observed:
            obs = f"{observed['score']}/{observed.get('message_diff_hw', '-')}"
        else:
            obs = "-"
        print(
            f"{rank:>4}  {entry['rank_score']:>6}  "
            f"{entry['extra_feeds']:>5} {entry['early_extra_feeds']:>5}  "
            f"{entry['max_fan_in']:>3}/{entry['early_max_fan_in']:<3} "
            f"{entry['triple_targets']:>3}/{entry['early_triple_targets']:<3}  "
            f"{entry['identity_mixed_targets']:>5}  {obs:>8}  "
            f"{active:>16}  {target_signature(entry, signature_limit)}"
        )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pool", default="0-15",
                    help="Comma/range list of candidate message words")
    ap.add_argument("--sizes", default="5",
                    help="Comma/range list of subset sizes")
    ap.add_argument("--include", default="",
                    help="Comma/range list of message words forced into every subset")
    ap.add_argument("--early-limit", type=int, default=24,
                    help="Last schedule word counted as early")
    ap.add_argument("--top", type=int, default=25)
    ap.add_argument("--signature-targets", type=int, default=3)
    ap.add_argument("--observed-json", nargs="*", default=[],
                    help="Search/subset-scan JSONs used to annotate known outcomes")
    ap.add_argument("--out-json", default=None)
    ap.add_argument("--json-limit", type=int, default=0,
                    help="Store only this many ranked entries; 0 stores all")
    args = ap.parse_args()

    pool = parse_active_words(args.pool)
    sizes = parse_sizes(args.sizes)
    include = parse_active_words(args.include) if args.include else []
    observed = load_observed(args.observed_json)

    entries = []
    for subset in iter_subsets(pool, sizes, include):
        entry = profile_subset(subset, args.early_limit)
        key = tuple(entry["active_words"])
        if key in observed:
            entry["observed"] = observed[key]
        entries.append(entry)

    entries.sort(key=sort_key)

    print("=== active word structural rank ===")
    print(f"Pool:          {','.join(str(w) for w in pool)}")
    print(f"Sizes:         {','.join(str(s) for s in sizes)}")
    print(f"Include:       {','.join(str(w) for w in include) if include else '(none)'}")
    print(f"Early limit:   W{args.early_limit}")
    print(f"Subsets:       {len(entries)}")
    print()
    print_table(entries, min(args.top, len(entries)), args.signature_targets)

    if args.out_json:
        saved_entries = entries[:args.json_limit] if args.json_limit else entries
        with open(args.out_json, "w") as f:
            json.dump({
                "args": vars(args),
                "entries": saved_entries,
            }, f, indent=2)
        print(f"\nFull JSON: {args.out_json}", file=sys.stderr)


if __name__ == "__main__":
    main()
