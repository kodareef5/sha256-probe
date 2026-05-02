#!/usr/bin/env python3
"""Select absorber-profile follow-up seeds while avoiding known pair-beam reruns."""

import argparse
import glob
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def pair_beam_tested_ranks(manifest: dict[str, Any], artifact_glob: str) -> dict[int, list[str]]:
    rank_by_w = {tuple(seed["W"]): int(seed["rank"]) for seed in manifest.get("seeds", [])}
    tested: dict[int, list[str]] = {}
    for raw_path in glob.glob(artifact_glob):
        path = Path(raw_path)
        try:
            payload = load_json(path)
        except Exception:
            continue
        description = payload.get("description", "")
        if "pair beam search" not in description:
            continue
        w = tuple(payload.get("init_W") or [])
        rank = rank_by_w.get(w)
        if rank is not None:
            tested.setdefault(rank, []).append(str(path))
    return tested


def top_unique(rows: list[dict[str, Any]], key, limit: int, tested: dict[int, list[str]] | None = None) -> list[dict[str, Any]]:
    out = []
    seen = set()
    for row in sorted(rows, key=key):
        rank = int(row["rank"])
        if rank in seen:
            continue
        if tested is not None and rank in tested:
            continue
        seen.add(rank)
        out.append(row)
        if len(out) >= limit:
            break
    return out


def attach_status(rows: list[dict[str, Any]], tested: dict[int, list[str]]) -> list[dict[str, Any]]:
    out = []
    for row in rows:
        rank = int(row["rank"])
        item = dict(row)
        item["pair_beam_tested"] = rank in tested
        item["pair_beam_artifacts"] = tested.get(rank, [])
        out.append(item)
    return out


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = ["# Absorber Follow-Up Selector", ""]
    for section in ("untested_late_round", "untested_cg_profile", "controls"):
        lines += [
            f"## {section.replace('_', ' ').title()}",
            "",
            "| Rank | Block-1 HW | Best HW | Late Best | c/g Min | Cleared Max | Tested | W57..W60 |",
            "|---:|---:|---:|---:|---:|---:|---|---|",
        ]
        for row in payload[section]:
            words = ",".join(str(w) for w in row["best_W"])
            tested = "yes" if row.get("pair_beam_tested") else "no"
            lines.append(
                f"| {row['rank']} | {row['block1_hw']} | {row['best_hw_min']} | "
                f"{row['late_best_hw']} | {row['cg_best_min']} | {row['cleared_max']} | "
                f"{tested} | `{words}` |"
            )
        lines.append("")

    lines += [
        "## Suggested Order",
        "",
    ]
    for idx, row in enumerate(payload["suggested_order"], start=1):
        words = ",".join(str(w) for w in row["best_W"])
        lines.append(
            f"{idx}. rank {row['rank']} block1_hw={row['block1_hw']} "
            f"late_best={row['late_best_hw']} cg_min={row['cg_best_min']} W=`{words}`"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--profile", required=True)
    ap.add_argument("--artifact-glob", default="headline_hunt/bets/block2_wang/results/search_artifacts/*.json")
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    args = ap.parse_args()

    manifest = load_json(Path(args.manifest))
    profile = load_json(Path(args.profile))
    rows = profile["ranking"]
    tested = pair_beam_tested_ranks(manifest, args.artifact_glob)

    untested_late = top_unique(
        rows,
        key=lambda r: (r["late_best_hw"] if r["late_best_hw"] is not None else 999, r["best_hw_min"], -r["cleared_max"], r["rank"]),
        limit=args.limit,
        tested=tested,
    )
    untested_cg = top_unique(
        rows,
        key=lambda r: (r["cg_best_min"], r["late_best_hw"] if r["late_best_hw"] is not None else 999, r["best_hw_mean"], r["rank"]),
        limit=args.limit,
        tested=tested,
    )

    control_ranks = {1, 4, 11, 15, 20, 21, 34, 36}
    controls = [row for row in rows if int(row["rank"]) in control_ranks]
    controls.sort(key=lambda r: (r["rank"]))

    suggested = []
    seen = set()
    for source in (untested_late, untested_cg):
        for row in source:
            rank = int(row["rank"])
            if rank not in seen:
                suggested.append(row)
                seen.add(rank)
    suggested = suggested[: args.limit]

    payload = {
        "description": "absorber profile follow-up selector",
        "tested_rank_count": len(tested),
        "tested_ranks": {str(k): v for k, v in sorted(tested.items())},
        "untested_late_round": attach_status(untested_late, tested),
        "untested_cg_profile": attach_status(untested_cg, tested),
        "controls": attach_status(controls, tested),
        "suggested_order": attach_status(suggested, tested),
    }

    Path(args.out_json).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    write_md(Path(args.out_md), payload)
    print(f"wrote {args.out_md}")


if __name__ == "__main__":
    main()
