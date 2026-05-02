#!/usr/bin/env python3
"""Select untested manifest seeds for pair-beam follow-up.

The basin manifests already carry rank, W, HW, score, and pair-beam-ready
arguments. This helper cross-references a manifest against existing
pair_beam_search artifacts by their init_W and reports the next untested
seeds. It is intentionally generic; it does not assume absorber-profile fields.
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def norm_w(words: Any) -> tuple[str, ...]:
    if not words:
        return ()
    return tuple(str(w).lower() for w in words)


def artifact_init_w(path: Path) -> tuple[str, ...]:
    try:
        payload = load_json(path)
    except Exception:
        return ()
    if "pair beam search" not in str(payload.get("description", "")):
        return ()
    return norm_w(payload.get("init_W"))


def tested_by_w(artifact_glob: str) -> dict[tuple[str, ...], list[str]]:
    out: dict[tuple[str, ...], list[str]] = {}
    for raw in glob.glob(artifact_glob):
        path = Path(raw)
        w = artifact_init_w(path)
        if w:
            out.setdefault(w, []).append(str(path))
    return out


def seed_sort_key(seed: dict[str, Any], mode: str) -> tuple[Any, ...]:
    hw = seed.get("hw_total", seed.get("pair_beam_init_hw_arg", 999))
    score = seed.get("score")
    score_key = -float(score) if score is not None else 0.0
    rank = int(seed.get("rank", 999999))
    if mode == "rank":
        return (rank,)
    if mode == "score":
        return (hw, score_key, rank)
    return (hw, rank)


def render_words(seed: dict[str, Any]) -> str:
    words = seed.get("W") or []
    return " ".join(str(w) for w in words)


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Manifest Follow-Up Selector",
        "",
        f"- manifest: `{payload['manifest']}`",
        f"- artifact glob: `{payload['artifact_glob']}`",
        f"- tested ranks: {payload['tested_rank_count']}",
        "",
        "## Suggested Untested Seeds",
        "",
        "| Rank | HW | Score | W57..W60 | pair_beam init |",
        "|---:|---:|---:|---|---|",
    ]
    for row in payload["suggested"]:
        score = row.get("score")
        score_text = "" if score is None else f"{float(score):.3f}"
        lines.append(
            f"| {row.get('rank')} | {row.get('hw_total')} | {score_text} | "
            f"`{render_words(row)}` | "
            f"`--init-W {row.get('pair_beam_init_W_arg')} --init-hw {row.get('pair_beam_init_hw_arg')}` |"
        )
    lines += [
        "",
        "## Tested Seeds",
        "",
        "| Rank | HW | Score | Artifacts |",
        "|---:|---:|---:|---|",
    ]
    for row in payload["tested"]:
        score = row.get("score")
        score_text = "" if score is None else f"{float(score):.3f}"
        arts = "<br>".join(f"`{Path(p).name}`" for p in row["pair_beam_artifacts"])
        lines.append(f"| {row.get('rank')} | {row.get('hw_total')} | {score_text} | {arts} |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--manifest", required=True)
    ap.add_argument(
        "--artifact-glob",
        default="headline_hunt/bets/block2_wang/results/search_artifacts/*.json",
    )
    ap.add_argument("--limit", type=int, default=12)
    ap.add_argument("--mode", choices=["hw", "rank", "score"], default="hw")
    ap.add_argument("--out-json")
    ap.add_argument("--out-md")
    args = ap.parse_args()

    manifest_path = Path(args.manifest)
    manifest = load_json(manifest_path)
    tested = tested_by_w(args.artifact_glob)

    tested_rows = []
    untested_rows = []
    for seed in manifest.get("seeds", []):
        row = dict(seed)
        w = norm_w(seed.get("W"))
        artifacts = tested.get(w, [])
        if artifacts:
            row["pair_beam_tested"] = True
            row["pair_beam_artifacts"] = artifacts
            tested_rows.append(row)
        else:
            row["pair_beam_tested"] = False
            row["pair_beam_artifacts"] = []
            untested_rows.append(row)

    suggested = sorted(untested_rows, key=lambda r: seed_sort_key(r, args.mode))[: args.limit]
    tested_rows.sort(key=lambda r: int(r.get("rank", 999999)))

    payload = {
        "description": "manifest follow-up selector",
        "manifest": str(manifest_path),
        "artifact_glob": args.artifact_glob,
        "mode": args.mode,
        "tested_rank_count": len(tested_rows),
        "suggested": suggested,
        "tested": tested_rows,
    }

    if args.out_json:
        Path(args.out_json).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.out_md:
        write_md(Path(args.out_md), payload)

    print(f"tested ranks: {len(tested_rows)}")
    for row in suggested:
        print(
            f"rank {row.get('rank'):>3} hw={row.get('hw_total'):>2} "
            f"score={row.get('score')} W={render_words(row)}"
        )


if __name__ == "__main__":
    main()
