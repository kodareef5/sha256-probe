#!/usr/bin/env python3
"""
build_candidate_evidence_manifest.py - Cross-bet candidate evidence table.

This is the Phase 0 data bed for the math-principles plan after the
Yale/MacBook W57 and block2 bridge chains converged.  It intentionally keeps a
small, concrete scope: candidate registry metadata, F387 class labels,
preflight clause evidence, W57 polarity probes, block2 bridge witnesses, and
Yale bridge-cube context.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml


REPO = Path(__file__).resolve().parents[4]

DEFAULT_CANDIDATES = REPO / "headline_hunt/registry/candidates.yaml"
DEFAULT_PREFLIGHT_ROOT = (
    REPO / "headline_hunt/bets/programmatic_sat_propagator/results/preflight_2026-04-29"
)
DEFAULT_F340_W57 = (
    REPO / "headline_hunt/bets/cascade_aux_encoding/results/20260429_F340_W57_22_23_polarity_results.json"
)
DEFAULT_F380_BRIDGE_CUBES = (
    REPO / "headline_hunt/bets/math_principles/results/20260429_F380_bridge_cubes.json"
)
DEFAULT_F384_W57 = (
    REPO / "headline_hunt/bets/math_principles/results/20260429_F384_w57_core_pair_analysis.json"
)
DEFAULT_BLOCK2_BEAM = (
    REPO / "headline_hunt/bets/block2_wang/results/search_artifacts/20260430_F379_bridge_beam.json"
)
DEFAULT_BLOCK2_CERTPIN = (
    REPO / "headline_hunt/bets/block2_wang/results/20260430_F380_certpin_top11_bridge_witnesses.json"
)
DEFAULT_OUT_JSONL = (
    REPO / "headline_hunt/bets/math_principles/data/20260430_F396_candidate_evidence_manifest.jsonl"
)
DEFAULT_OUT_SUMMARY = (
    REPO / "headline_hunt/bets/math_principles/results/20260430_F396_candidate_evidence_manifest_summary.json"
)


CAND_RE = re.compile(
    r"(?:cand_)?(?:n32_)?(?:(?:bit(?P<bit>\d+))|(?P<msb>msb))_"
    r"m(?:0x)?(?P<m0>[0-9a-fA-F]+)(?:_(?:fill|f)(?:0x)?(?P<fill>[0-9a-fA-F]+))?"
)
CNF_RE = re.compile(
    r"(?:aux_(?:force|expose)_sr\d+_)?n32_"
    r"(?:(?:bit(?P<bit>\d+))|(?P<msb>msb))_"
    r"m(?:0x)?(?P<m0>[0-9a-fA-F]+)_(?:fill|f)(?:0x)?(?P<fill>[0-9a-fA-F]+)"
)


def rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO))
    except ValueError:
        return str(path)


def load_json(path: Path) -> dict[str, Any]:
    with path.open() as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def load_yaml(path: Path) -> Any:
    with path.open() as f:
        return yaml.safe_load(f)


def hex_norm(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, int):
        return f"{value:08x}"
    text = str(value).strip().lower()
    if text.startswith("0x"):
        text = text[2:]
    return text.zfill(8)


def popcount_hex(value: str | None) -> int | None:
    if value is None:
        return None
    return int(value, 16).bit_count()


def candidate_key(bit: int | str | None, m0: str | None, fill: str | None) -> str | None:
    if bit is None or m0 is None or fill is None:
        return None
    return f"bit{int(bit)}_m{hex_norm(m0)}_fill{hex_norm(fill)}"


def parse_candidate_text(text: str, aliases: dict[tuple[int, str], str]) -> str | None:
    for regex in (CNF_RE, CAND_RE):
        match = regex.search(text)
        if not match:
            continue
        bit = 31 if match.groupdict().get("msb") else int(match.group("bit"))
        m0 = hex_norm(match.group("m0"))
        fill = match.groupdict().get("fill")
        if fill is not None:
            return candidate_key(bit, m0, fill)
        return aliases.get((bit, m0))
    return None


def f387_class(m0: str | None, fill: str | None) -> dict[str, Any]:
    m0_i = int(m0, 16) if m0 is not None else 0
    fill_i = int(fill, 16) if fill is not None else 0
    fill_hw = fill_i.bit_count()
    path1 = bool((m0_i >> 31) & 1)
    path2 = bool(((fill_i >> 31) & 1) and fill_hw > 1)
    return {
        "m0_bit31": int(path1),
        "fill_bit31": int((fill_i >> 31) & 1),
        "fill_hw": fill_hw,
        "f387_class": "A" if path1 or path2 else "B",
        "f387_path1_m0_bit31": path1,
        "f387_path2_fill_bit31_hw_gt1": path2,
    }


def base_row(kind: str, source_id: str, artifact_path: Path | str, candidate: str | None) -> dict[str, Any]:
    return {
        "kind": kind,
        "source_id": source_id,
        "artifact_path": rel(artifact_path) if isinstance(artifact_path, Path) else artifact_path,
        "candidate": candidate,
    }


def build_registry_rows(path: Path) -> tuple[list[dict[str, Any]], dict[tuple[int, str], str]]:
    rows: list[dict[str, Any]] = []
    aliases: dict[tuple[int, str], str] = {}
    candidates = load_yaml(path) or []
    for item in candidates:
        kernel = item.get("kernel") or {}
        bit = kernel.get("bit")
        m0 = hex_norm(item.get("m0"))
        fill = hex_norm(item.get("fill"))
        key = candidate_key(bit, m0, fill)
        if key is None:
            continue
        aliases[(int(bit), m0)] = key
        metrics = item.get("metrics") or {}
        sr60 = ((item.get("statuses") or {}).get("sr60") or {})
        true_sr61 = ((item.get("statuses") or {}).get("true_sr61") or {})
        rows.append({
            **base_row("registry_candidate", item.get("id", "registry"), path, key),
            "candidate_id": item.get("id"),
            "kernel_bit": int(bit),
            "m0": f"0x{m0}",
            "fill": f"0x{fill}",
            "metrics": {
                "hw56": metrics.get("hw56"),
                "de58_size": metrics.get("de58_size"),
                "de58_hardlock_bits": metrics.get("de58_hardlock_bits"),
                "hard_bit_total_lb": metrics.get("hard_bit_total_lb"),
            },
            "sr60_status": sr60.get("status"),
            "true_sr61_status": true_sr61.get("status"),
            "evidence_level": item.get("evidence_level"),
            **f387_class(m0, fill),
        })
    return rows, aliases


def ingest_f340(path: Path, aliases: dict[tuple[int, str], str]) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = load_json(path)
    rows = []
    for item in data.get("cands", []):
        key = parse_candidate_text(
            f"{item.get('name', '')}_fill{item.get('fill', '')}",
            aliases,
        )
        rows.append({
            **base_row("cascade_w57_pair_probe", "F340", path, key),
            "name": item.get("name"),
            "m0": item.get("M0"),
            "fill": item.get("fill"),
            "fill_bit31": item.get("fill_bit31"),
            "round": 57,
            "bits": [22, 23],
            "unsat_polarity": item.get("unsat_polarity"),
            "results": item.get("results"),
        })
    return rows


def preflight_paths(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path for path in root.rglob("*.json")
        if path.name.endswith("_preflight.json") or path.name == "bit31_m17149975_full_scan.json"
    )


def ingest_preflight(root: Path, aliases: dict[tuple[int, str], str]) -> list[dict[str, Any]]:
    rows = []
    for path in preflight_paths(root):
        data = load_json(path)
        if "unit_clauses" not in data and "pair_clauses" not in data:
            continue
        key = parse_candidate_text(str(data.get("cnf", "")), aliases)
        if key is None:
            key = parse_candidate_text(path.name, aliases)
        units = data.get("unit_clauses") or []
        pairs = data.get("pair_clauses") or []
        rows.append({
            **base_row("preflight_clause_set", path.stem, path, key),
            "budget_seconds": data.get("budget_seconds"),
            "preflight_wall_seconds": data.get("preflight_wall_seconds"),
            "rounds_probed": data.get("rounds_probed"),
            "unit_count": len(units),
            "pair_count": len(pairs),
            "unit_forced": [
                {"round": row.get("round"), "bit": row.get("bit"), "forced": row.get("forced")}
                for row in units
            ],
            "pair_forbidden": [
                {
                    "round": row.get("round"),
                    "bits": row.get("bits"),
                    "forbidden_polarity": row.get("forbidden_polarity"),
                }
                for row in pairs
            ],
        })
    return rows


def ingest_block2_beam(path: Path, aliases: dict[tuple[int, str], str]) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = load_json(path)
    rows = []
    for name, item in (data.get("best_per_cand") or {}).items():
        key = parse_candidate_text(f"bit{item.get('kernel_bit')}_m{item.get('m0')}_fill{item.get('fill')}", aliases)
        best = item.get("best_record") or {}
        rows.append({
            **base_row("block2_bridge_beam_best", "F379", path, key),
            "name": name,
            "kernel_bit": item.get("kernel_bit"),
            "m0": item.get("m0"),
            "fill": item.get("fill"),
            "seed": item.get("seed"),
            "best_score": item.get("best_score"),
            "hw_total": best.get("hw_total"),
            "hw63": best.get("hw63"),
            "active_regs": best.get("active_regs"),
            "best_W": item.get("best_W"),
        })
    return rows


def ingest_block2_certpin(path: Path, aliases: dict[tuple[int, str], str]) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = load_json(path)
    rows = []
    for item in data.get("results", []):
        key = parse_candidate_text(item.get("cand", ""), aliases)
        solver_statuses = {
            name: solver.get("status")
            for name, solver in (item.get("solvers") or {}).items()
        }
        rows.append({
            **base_row("block2_certpin_witness", item.get("src", "F380"), path, key),
            "cand": item.get("cand"),
            "hw_total": item.get("hw_total"),
            "W": item.get("W"),
            "solver_statuses": solver_statuses,
        })
    return rows


def ingest_math_bridge_cubes(
    bridge_path: Path,
    f384_path: Path,
    aliases: dict[tuple[int, str], str],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    aux_candidate = None
    if bridge_path.exists():
        data = load_json(bridge_path)
        aux_candidate = parse_candidate_text(str(data.get("varmap", "")), aliases)
        for cube in data.get("cubes", []):
            cand = cube.get("candidate") or {}
            coordinate_bits = cube.get("coordinate_bits") or {}
            rows.append({
                **base_row("math_bridge_cube", cube.get("target", "F380"), bridge_path, aux_candidate),
                "target": cube.get("target"),
                "subset": cube.get("subset"),
                "source": cube.get("source"),
                "bit_count": cube.get("bit_count"),
                "assumption_count": (cube.get("literal_cube") or {}).get("assumption_count"),
                "strict_candidate": cand,
                "dW57_22_23": [
                    coordinate_bits.get("57", [None] * 24)[22] if "57" in coordinate_bits else None,
                    coordinate_bits.get("57", [None] * 24)[23] if "57" in coordinate_bits else None,
                ] if cube.get("subset") == "w57_w60" else None,
            })
    if f384_path.exists():
        data = load_json(f384_path)
        candidate = parse_candidate_text(str(data.get("varmap", "")), aliases) or aux_candidate
        rows.append({
            **base_row("math_w57_pair_core", "F384", f384_path, candidate),
            "round": data.get("round"),
            "bits": data.get("bits"),
            "literals": data.get("literals"),
            "verdict": data.get("verdict"),
            "decision": data.get("decision"),
            "polarity_tests": [
                {"values": row.get("values"), "status": row.get("status")}
                for row in data.get("polarity_tests", [])
            ],
            "target_values": data.get("target_values"),
        })
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        for row in rows:
            f.write(json.dumps(row, sort_keys=True))
            f.write("\n")


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_kind = Counter(row["kind"] for row in rows)
    by_candidate = defaultdict(Counter)
    for row in rows:
        if row.get("candidate"):
            by_candidate[row["candidate"]][row["kind"]] += 1
    registry = [row for row in rows if row["kind"] == "registry_candidate"]
    preflight = [row for row in rows if row["kind"] == "preflight_clause_set"]
    certpin = [row for row in rows if row["kind"] == "block2_certpin_witness"]
    beam = [row for row in rows if row["kind"] == "block2_bridge_beam_best"]
    f387_hist = Counter(row.get("f387_class") for row in registry)
    pair_hist = Counter(
        tuple(pair.get("forbidden_polarity") or [])
        for row in preflight
        for pair in row.get("pair_forbidden", [])
    )
    return {
        "report_id": "F396",
        "record_count": len(rows),
        "candidate_count": len(by_candidate),
        "by_kind": dict(sorted(by_kind.items())),
        "registry_candidate_count": len(registry),
        "f387_class_histogram": dict(sorted(f387_hist.items())),
        "preflight_clause_sets": len(preflight),
        "preflight_pair_forbidden_histogram": {
            ",".join(map(str, key)): count for key, count in sorted(pair_hist.items())
        },
        "block2_certpin_witnesses": len(certpin),
        "block2_certpin_status_histogram": dict(Counter(
            "/".join(sorted(set(row.get("solver_statuses", {}).values())))
            for row in certpin
        )),
        "block2_bridge_beam_best_hw_min": min(
            (row.get("hw_total") for row in beam if row.get("hw_total") is not None),
            default=None,
        ),
        "candidate_evidence_density_top10": [
            {"candidate": cand, "records": sum(counter.values()), "kinds": dict(sorted(counter.items()))}
            for cand, counter in sorted(
                by_candidate.items(),
                key=lambda item: (-sum(item[1].values()), item[0]),
            )[:10]
        ],
    }


def write_summary_json(path: Path, summary: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(summary, f, indent=2, sort_keys=True)
        f.write("\n")


def write_summary_md(path: Path, summary: dict[str, Any], manifest_path: Path) -> None:
    lines = [
        "---",
        "date: 2026-04-30",
        "bet: math_principles",
        "status: CANDIDATE_EVIDENCE_MANIFEST",
        "---",
        "",
        "# F396: candidate evidence manifest",
        "",
        "## Summary",
        "",
        f"Manifest: `{rel(manifest_path)}`.",
        f"Rows: {summary['record_count']}; candidates with evidence: {summary['candidate_count']}.",
        f"Registry candidates: {summary['registry_candidate_count']}.",
        f"F387 class histogram: `{summary['f387_class_histogram']}`.",
        f"Preflight clause sets: {summary['preflight_clause_sets']}.",
        f"Block2 cert-pin witnesses: {summary['block2_certpin_witnesses']}.",
        f"Best block2 bridge-beam HW in manifest: {summary['block2_bridge_beam_best_hw_min']}.",
        "",
        "## Rows By Kind",
        "",
        "| Kind | Rows |",
        "|---|---:|",
    ]
    for kind, count in summary["by_kind"].items():
        lines.append(f"| `{kind}` | {count} |")
    lines.extend([
        "",
        "## Candidate Evidence Density",
        "",
        "| Candidate | Rows | Kinds |",
        "|---|---:|---|",
    ])
    for row in summary["candidate_evidence_density_top10"]:
        lines.append(
            f"| `{row['candidate']}` | {row['records']} | "
            f"`{json.dumps(row['kinds'], sort_keys=True)}` |"
        )
    lines.extend([
        "",
        "## Immediate Use",
        "",
        "- Use this table as the join point for REM/tail, influence, preflight, and bridge-score follow-ups.",
        "- Keep cert-pin and aux-force evidence separated; cert-pin is UP-trivial while aux-force carries the CDCL learning signal.",
        "- Treat F343/F344 clause count as mostly exhausted per F395; the next useful operator axis is decision priority / VSIDS trajectory.",
        "",
    ])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    ap.add_argument("--preflight-root", type=Path, default=DEFAULT_PREFLIGHT_ROOT)
    ap.add_argument("--f340-w57", type=Path, default=DEFAULT_F340_W57)
    ap.add_argument("--f380-bridge-cubes", type=Path, default=DEFAULT_F380_BRIDGE_CUBES)
    ap.add_argument("--f384-w57", type=Path, default=DEFAULT_F384_W57)
    ap.add_argument("--block2-beam", type=Path, default=DEFAULT_BLOCK2_BEAM)
    ap.add_argument("--block2-certpin", type=Path, default=DEFAULT_BLOCK2_CERTPIN)
    ap.add_argument("--out-jsonl", type=Path, default=DEFAULT_OUT_JSONL)
    ap.add_argument("--summary-json", type=Path, default=DEFAULT_OUT_SUMMARY)
    ap.add_argument("--summary-md", type=Path, default=None)
    args = ap.parse_args()

    registry_rows, aliases = build_registry_rows(args.candidates)
    rows = [
        *registry_rows,
        *ingest_f340(args.f340_w57, aliases),
        *ingest_preflight(args.preflight_root, aliases),
        *ingest_block2_beam(args.block2_beam, aliases),
        *ingest_block2_certpin(args.block2_certpin, aliases),
        *ingest_math_bridge_cubes(args.f380_bridge_cubes, args.f384_w57, aliases),
    ]
    rows = sorted(rows, key=lambda row: (row.get("candidate") or "", row["kind"], row["source_id"]))
    write_jsonl(args.out_jsonl, rows)
    summary = summarize(rows)
    write_summary_json(args.summary_json, summary)
    write_summary_md(args.summary_md or args.summary_json.with_suffix(".md"), summary, args.out_jsonl)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
