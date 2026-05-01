---
date: 2026-05-01
bet: block2_wang
status: PATH_C_OBJECTIVE_PAIR_POOL_NEGATIVE
parent: F478/F479 manifest rank40 negatives
evidence_level: VERIFIED
compute: pair-beam tool update; two pair-beam runs; no solver runs
author: yale-codex
---

# F480/F481: objective-ranked pair pool is negative

## Setup

F480/F481 changed pair-pool construction in `pair_beam_search.py` by adding:

`--pair-rank objective`

This ranks candidate two-bit pair moves by the same lane-penalized objective
used by the beam:

`hw_total + penalty_weight * lane_damage - 0.001 * score`

The goal was to avoid filling the pair pool with raw-HW-good pairs that are
poor under the eventual c/g objective.

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F480_bit13_hw36_pair_beam_objective_cg.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F481_bit13_manifest_rank8_hw40_pair_beam_objective_cg.json`

## Results

| Run | Seed | Start HW | Pair rank | Best selected non-seed | Seed stayed best |
|---|---|---:|---|---:|---|
| F480 | HW36 record | 36 | objective | 40 | yes |
| F481 | manifest rank 8 | 40 | objective | 36 | no; re-found current floor |

F480 counters:

- expanded: 3,304,760
- bridge pass: 3,304,260
- HW <= 36: 0
- HW < 36: 0
- wall: 280.15s

F481 counters:

- expanded: 3,301,786
- bridge pass: 3,301,591
- HW <= 40: 2
- HW < 40: 2
- wall: 276.14s

## Verdict

Objective-ranked pair-pool selection is implemented and works, but it does
not improve the current HW36 floor on these seeds. It also reduces expansion
counts somewhat by increasing duplicate pressure, so it is a useful pruning
variant even though this first test was negative.
