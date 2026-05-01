---
date: 2026-05-01
bet: block2_wang
status: PATH_C_HW36_BASIN_NEGATIVES
parent: F469/F470 HW36 closure
evidence_level: VERIFIED
compute: two pair-beam runs; no solver runs
author: yale-codex
---

# F471/F472: HW36 record and F467 HW38 basin do not continue

## Setup

F471 restarted the wider c/g pair beam from the HW36 record. F472 restarted
the same beam from the best F467 non-record HW38 basin.

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F471_bit13_hw36_pair_beam_cg_wider.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F472_bit13_hw38_f467_intermediate_pair_beam_cg.json`

## Results

| Run | Seed | Start HW | Best selected non-seed | Seed stayed best |
|---|---|---:|---:|---|
| F471 | HW36 record | 36 | 40 | yes |
| F472 | F467 HW38 intermediate | 38 | 39 | yes |

F471 counters:

- expanded: 3,479,120
- skipped duplicate: 1,764,784
- bridge pass: 3,478,594
- HW <= 36: 0
- HW < 36: 0
- wall: 298.28s

F472 counters:

- expanded: 3,421,229
- skipped duplicate: 1,822,675
- bridge pass: 3,421,214
- HW <= 38: 0
- HW < 38: 0
- wall: 291.73s

## Verdict

The first HW40 intermediate-basin detour was productive, but the immediate
next record/HW38 restarts are boxed in. The next search should either mine
additional non-record basins from F467 top records, or change pair-pool
construction rather than only changing the seed.
