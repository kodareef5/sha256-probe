#!/usr/bin/env python3
"""
audit_carry_invariants.py - Cross-mode hard-core/carry invariant audit.

This first audit uses the sr60/sr61 hard-core stability artifacts as the
machine-readable proxy for carry-growth structure. It checks the concrete rule
that survived F332/F336: the last two free schedule rounds are universal core.
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


REPO = Path(__file__).resolve().parents[4]
DEFAULT_MANIFEST = REPO / "headline_hunt/bets/math_principles/data/20260429_principles_manifest.jsonl"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    with path.open() as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def round_num(word_round: str) -> int | None:
    if "[" not in word_round or "]" not in word_round:
        return None
    return int(word_round.split("[", 1)[1].split("]", 1)[0])


def audit_mode(rows: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    mode_rows = [row for row in rows if row.get("kind") == "hard_core_stability_bit" and row.get("mode") == mode]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in mode_rows:
        grouped[row["word_round"]].append(row)
    word_rounds = sorted(grouped, key=lambda item: (item[:2], round_num(item) or -1))
    rounds = sorted({round_num(wr) for wr in word_rounds if round_num(wr) is not None})
    last_two = set(rounds[-2:]) if len(rounds) >= 2 else set(rounds)
    first = rounds[0] if rounds else None

    by_word_round = {}
    for wr in word_rounds:
        rows_ = grouped[wr]
        by_word_round[wr] = {
            "stable_core": sum(1 for row in rows_ if row.get("hard_core_class") == "stable_core"),
            "stable_shell": sum(1 for row in rows_ if row.get("hard_core_class") == "stable_shell"),
            "variable": sum(1 for row in rows_ if row.get("hard_core_class") == "variable"),
            "mean_core_fraction": round(sum(float(row.get("core_fraction") or 0.0) for row in rows_) / len(rows_), 6),
        }

    last_two_rows = [
        row for row in mode_rows
        if round_num(row.get("word_round", "")) in last_two
    ]
    first_rows = [
        row for row in mode_rows
        if round_num(row.get("word_round", "")) == first
    ]
    return {
        "mode": mode,
        "word_rounds": by_word_round,
        "free_rounds": rounds,
        "last_two_rounds": sorted(last_two),
        "last_two_bits": len(last_two_rows),
        "last_two_stable_core": sum(1 for row in last_two_rows if row.get("hard_core_class") == "stable_core"),
        "first_round_bits": len(first_rows),
        "first_round_variable": sum(1 for row in first_rows if row.get("hard_core_class") == "variable"),
        "first_round_stable_shell": sum(1 for row in first_rows if row.get("hard_core_class") == "stable_shell"),
    }


def invariant_verdict(mode_summary: dict[str, Any]) -> dict[str, Any]:
    last_bits = mode_summary["last_two_bits"]
    stable = mode_summary["last_two_stable_core"]
    if last_bits == 0:
        status = "missing"
    elif stable == last_bits:
        status = "holds_exact"
    elif stable >= last_bits - 1:
        status = "holds_with_single_exception"
    else:
        status = "fails"
    return {
        "mode": mode_summary["mode"],
        "invariant": "last_two_free_rounds_are_stable_core",
        "status": status,
        "stable_core": stable,
        "bits": last_bits,
    }


def write_md(path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "---",
        "date: 2026-04-29",
        "bet: math_principles",
        "status: CARRY_INVARIANT_AUDIT",
        "---",
        "",
        "# F342: carry / hard-core invariant audit",
        "",
        "## Summary",
        "",
    ]
    for verdict in payload["verdicts"]:
        lines.append(
            f"- {verdict['mode']}: `{verdict['status']}` "
            f"({verdict['stable_core']}/{verdict['bits']} last-two bits stable core)"
        )
    lines.extend([
        "",
        "## Mode summaries",
        "",
    ])
    for mode in payload["modes"]:
        lines.append(f"### {mode['mode']}")
        lines.append("")
        lines.append("| Word round | Stable core | Stable shell | Variable | Mean core fraction |")
        lines.append("|---|---:|---:|---:|---:|")
        for wr, row in mode["word_rounds"].items():
            lines.append(
                f"| {wr} | {row['stable_core']} | {row['stable_shell']} | "
                f"{row['variable']} | {row['mean_core_fraction']} |"
            )
        lines.append("")
    lines.extend([
        "## Decision",
        "",
        "Promote the last-two-free-round rule as a structural coordinate for selector/BP work. Keep first-free-round behavior candidate-specific.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("manifest", type=Path, nargs="?", default=DEFAULT_MANIFEST)
    ap.add_argument("--out-json", type=Path, default=REPO / "headline_hunt/bets/math_principles/results/20260429_F342_carry_invariant_audit.json")
    ap.add_argument("--out-md", type=Path, default=REPO / "headline_hunt/bets/math_principles/results/20260429_F342_carry_invariant_audit.md")
    args = ap.parse_args()

    rows = read_jsonl(args.manifest)
    modes = [audit_mode(rows, mode) for mode in ("sr60", "sr61")]
    payload = {
        "manifest": repo_path(args.manifest),
        "modes": modes,
        "verdicts": [invariant_verdict(mode) for mode in modes],
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    with args.out_json.open("w") as f:
        json.dump(payload, f, indent=2, sort_keys=True)
        f.write("\n")
    write_md(args.out_md, payload)
    print(json.dumps({"verdicts": payload["verdicts"]}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
