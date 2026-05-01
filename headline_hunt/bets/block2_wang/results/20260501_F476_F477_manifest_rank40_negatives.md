---
date: 2026-05-01
bet: block2_wang
status: PATH_C_MANIFEST_RANK40_NEGATIVES
parent: F473 basin seed manifest
evidence_level: VERIFIED
compute: two pair-beam runs; no solver runs
author: yale-codex
---

# F476/F477: manifest rank-6 and rank-7 HW40 seeds re-find HW36 but do not improve

## Setup

F476/F477 continued the F473 manifest sweep after the rank-4/rank-5 HW39
negatives. Both seeds have W59=`0x6a3a8409`, which made them structurally
more distinct from the failed HW39 cluster.

- F476 rank 6: W1=`0x5228ed8d 0x61a1a29c 0x6a3a8409 0x149f957b`
- F477 rank 7: W1=`0x5228ed8d 0x61a1a29c 0x6a3a8409 0x2daf75f3`

Both used the standard wider c/g beam: pool 1024, beam 1024, max pairs 6,
max radius 12.

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F476_bit13_manifest_rank6_hw40_pair_beam_cg.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F477_bit13_manifest_rank7_hw40_pair_beam_cg.json`

## Results

| Run | Manifest rank | Start HW | Best selected non-seed | Seed stayed best |
|---|---:|---:|---:|---|
| F476 | 6 | 40 | 36 | no; found current HW36 floor |
| F477 | 7 | 40 | 36 | no; found current HW36 floor |

Neither run improved the current HW36 floor.

F476 counters:

- expanded: 3,492,095
- bridge pass: 3,492,055
- HW <= 40: 7
- HW < 40: 4
- wall: 303.36s

F477 counters:

- expanded: 3,477,548
- bridge pass: 3,477,267
- HW <= 40: 18
- HW < 40: 12
- wall: 300.25s

## Verdict

The rank-6/rank-7 HW40 basins are connected back to the known HW36 basin but
do not expose a lower record under the current pair-pool/objective. The
manifest sweep should continue, but the next useful change is likely either
rank-8's slightly different W59 or a different pair-pool construction.
