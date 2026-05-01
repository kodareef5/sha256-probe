#!/usr/bin/env python3
"""Extract reusable basin seeds from pair-beam artifacts.

Pair-beam runs often contain useful non-record states in top_records. This
utility deduplicates those states across artifacts and emits a compact seed
manifest that can drive follow-up runs.
"""

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def seed_from_entry(payload: dict, path: Path, entry: dict, source_section: str) -> dict | None:
    record = entry.get("record") or {}
    hw_total = entry.get("hw_total", record.get("hw_total"))
    score = entry.get("score")
    w = entry.get("W")
    if hw_total is None or score is None or not w:
        return None
    return {
        "candidate": payload.get("candidate"),
        "source_artifact": str(path),
        "source_section": source_section,
        "source_description": payload.get("description"),
        "init_W": payload.get("init_W"),
        "init_hw": payload.get("init_hw"),
        "hw_total": hw_total,
        "score": score,
        "W": w,
        "hw63": record.get("hw63"),
        "diff63": record.get("diff63"),
        "bits": entry.get("bits", []),
        "pair_beam_init_W_arg": ",".join(w),
        "pair_beam_init_hw_arg": hw_total,
    }


def collect_seeds(path: Path, max_per_artifact: int, include_best_seen: bool) -> list[dict]:
    payload = load_json(path)
    seeds = []
    if include_best_seen:
        best = seed_from_entry(payload, path, payload.get("best_seen", {}), "best_seen")
        if best is not None:
            seeds.append(best)
    for section in ("new_records", "top_records"):
        entries = payload.get(section, [])
        for entry in entries[:max_per_artifact]:
            seed = seed_from_entry(payload, path, entry, section)
            if seed is not None:
                seeds.append(seed)
    return seeds


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--artifacts", nargs="+", required=True, help="pair-beam JSON artifacts")
    ap.add_argument("--max-per-artifact", type=int, default=40)
    ap.add_argument("--include-best-seen", action="store_true")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    deduped = {}
    for raw in args.artifacts:
        path = Path(raw)
        for seed in collect_seeds(path, args.max_per_artifact, args.include_best_seen):
            key = (seed["candidate"], tuple(seed["W"]))
            old = deduped.get(key)
            if old is None or (seed["hw_total"], -seed["score"]) < (old["hw_total"], -old["score"]):
                deduped[key] = seed

    seeds = sorted(
        deduped.values(),
        key=lambda s: (s["candidate"] or "", s["hw_total"], -s["score"], s["W"]),
    )
    for idx, seed in enumerate(seeds, start=1):
        seed["rank"] = idx

    payload = {
        "description": "deduplicated pair-beam basin seed manifest",
        "source_artifacts": args.artifacts,
        "max_per_artifact": args.max_per_artifact,
        "include_best_seen": args.include_best_seen,
        "seed_count": len(seeds),
        "seeds": seeds,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}: {len(seeds)} seeds")


if __name__ == "__main__":
    main()
