---
date: 2026-05-01
bet: block2_wang
status: PATH_C_CROSS_PANEL_OBJECTIVE_NEGATIVE
parent: F480/F483 objective pair-pool tests
evidence_level: VERIFIED
compute: two pair-beam runs; no solver runs
author: yale-codex
---

# F484/F485: objective-ranked pair pool is negative on bit28 and bit24

## Setup

F484/F485 tested the objective-ranked pair-pool construction outside bit13:

- F484: bit28 HW42 seed, c/g objective pair pool.
- F485: bit24 HW43 seed, c/g objective pair pool.

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F484_bit28_hw42_pair_beam_objective_cg.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F485_bit24_hw43_pair_beam_objective_cg.json`

## Results

| Run | Candidate | Start HW | Best selected non-seed | Seed stayed best |
|---|---|---:|---:|---|
| F484 | bit28_md1acca79 | 42 | 44 | yes |
| F485 | bit24_mdc27e18c | 43 | 45 | yes |

F484 counters:

- expanded: 3,456,131
- bridge pass: 3,454,734
- HW <= 42: 0
- HW < 42: 0
- wall: 294.27s

F485 counters:

- expanded: 3,467,330
- bridge pass: 3,466,984
- HW <= 43: 0
- HW < 43: 0
- wall: 299.50s

## Verdict

Objective-ranked pair-pool selection is broadly negative across the current
panel. It is useful as a pruning tool, but the next productive direction
should not be another objective-pool rerun on the same seeds.
