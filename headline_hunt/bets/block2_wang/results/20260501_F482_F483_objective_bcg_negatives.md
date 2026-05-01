---
date: 2026-05-01
bet: block2_wang
status: PATH_C_OBJECTIVE_BCG_NEGATIVE
parent: F480/F481 objective pair-pool tests
evidence_level: VERIFIED
compute: two pair-beam runs; no solver runs
author: yale-codex
---

# F482/F483: objective-ranked b/c/g protection is negative

## Setup

F482/F483 kept the objective-ranked pair-pool construction but changed the
protected lanes from c,g to b,c,g. The hypothesis was that the HW36 record's
low b/c/g lane signature might be structurally important:

- HW36 hw63=`[11,3,1,0,13,7,1,0]`

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F482_bit13_hw36_pair_beam_objective_bcg.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F483_bit13_manifest_rank8_hw40_pair_beam_objective_bcg.json`

## Results

| Run | Seed | Start HW | Pair rank | Protected lanes | Best selected non-seed | Seed stayed best |
|---|---|---:|---|---|---:|---|
| F482 | HW36 record | 36 | objective | b,c,g | 40 | yes |
| F483 | manifest rank 8 | 40 | objective | b,c,g | 42 | yes |

F482 counters:

- expanded: 3,414,097
- bridge pass: 3,413,690
- HW <= 36: 0
- HW < 36: 0
- wall: 289.28s

F483 counters:

- expanded: 3,402,770
- bridge pass: 3,402,372
- HW <= 40: 0
- HW < 40: 0
- wall: 288.66s

## Verdict

Adding b-lane protection makes the objective too conservative for these
seeds. It does not improve HW36 and prevents the rank-8 basin from
reconnecting to HW36. Future variants should avoid over-protecting b unless
there is a more targeted repair objective.
