#!/usr/bin/env python3
"""
m2_cross_round_pipe.py - staged M2 pair-beam continuation across rounds.

This automates the F519/F535 suggestion:
  polish at an easier round count, then lift the best M2 to later rounds.

Example:
  python3 headline_hunt/bets/block2_wang/encoders/m2_cross_round_pipe.py \
    --seed-jsonl headline_hunt/bets/block2_wang/results/search_artifacts/20260502_absorber_matrix_overnight/F518_absorber_m2_late_round_seeds.jsonl \
    --rank 0 --rounds 16,20,24 \
    --out-dir headline_hunt/bets/block2_wang/results/search_artifacts \
    --label F537_rank0_pipe
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def true_best(data):
    best_hw = data.get("best_seen_hw")
    best_m2 = data.get("best_seen_M2")
    best_source = data.get("best_seen_source", "best_seen")
    for rec in data.get("top_records", []):
        hw = rec.get("hw")
        if hw is not None and (best_hw is None or hw < best_hw):
            best_hw = hw
            best_m2 = rec.get("M2")
            best_source = "top_records"
    if best_m2 is None:
        raise SystemExit("artifact has no usable best M2")
    return best_hw, best_m2, best_source


def run_stage(script, args, round_count, stage_idx, init_m2):
    out = args.out_dir / f"{args.label}_stage{stage_idx}_r{round_count}.json"
    cmd = [
        sys.executable,
        str(script),
        "--seed-jsonl",
        str(args.seed_jsonl),
        "--rank",
        str(args.rank),
        "--rounds",
        str(round_count),
        "--pair-pool",
        str(args.pair_pool),
        "--beam-width",
        str(args.beam_width),
        "--max-pairs",
        str(args.max_pairs),
        "--max-radius",
        str(args.max_radius),
        "--top-records",
        str(args.top_records),
        "--objective",
        args.objective,
        "--pair-rank",
        args.pair_rank,
        "--cg-weight",
        str(args.cg_weight),
        "--out",
        str(out),
        "--label",
        f"{args.label}_stage{stage_idx}_r{round_count}",
    ]
    if args.lane_weights:
        cmd.extend(["--lane-weights", args.lane_weights])
    if init_m2:
        cmd.extend(["--init-M2", ",".join(init_m2)])
    print("running:", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)
    with out.open() as f:
        data = json.load(f)
    best_hw, best_m2, best_source = true_best(data)
    print(f"stage {stage_idx} r{round_count}: best_hw={best_hw} source={best_source}", flush=True)
    return out, best_hw, best_m2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed-jsonl", type=Path, required=True)
    ap.add_argument("--rank", type=int, default=0)
    ap.add_argument("--rounds", default="16,20,24")
    ap.add_argument("--out-dir", type=Path, required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--pair-pool", type=int, default=1024)
    ap.add_argument("--beam-width", type=int, default=1024)
    ap.add_argument("--max-pairs", type=int, default=6)
    ap.add_argument("--max-radius", type=int, default=12)
    ap.add_argument("--top-records", type=int, default=30)
    ap.add_argument("--objective", choices=["hw", "cg", "weighted"], default="hw")
    ap.add_argument("--pair-rank", choices=["hw", "cg", "weighted"], default="hw")
    ap.add_argument("--lane-weights", default="")
    ap.add_argument("--cg-weight", type=float, default=1.0)
    args = ap.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    script = Path(__file__).with_name("block2_m2_pair_beam.py")
    rounds = [int(item.strip()) for item in args.rounds.split(",") if item.strip()]
    init_m2 = None
    summary = []
    for stage_idx, round_count in enumerate(rounds, start=1):
        out, best_hw, init_m2 = run_stage(script, args, round_count, stage_idx, init_m2)
        summary.append({"stage": stage_idx, "rounds": round_count, "artifact": str(out), "best_hw": best_hw})

    summary_path = args.out_dir / f"{args.label}_summary.json"
    with summary_path.open("w") as f:
        json.dump({
            "label": args.label,
            "seed_rank": args.rank,
            "rounds": rounds,
            "summary": summary,
        }, f, indent=2)
        f.write("\n")
    print(f"wrote {summary_path}", flush=True)


if __name__ == "__main__":
    main()
