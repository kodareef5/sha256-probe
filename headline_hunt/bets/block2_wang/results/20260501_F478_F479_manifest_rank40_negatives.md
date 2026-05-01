---
date: 2026-05-01
bet: block2_wang
status: PATH_C_MANIFEST_RANK40_NEGATIVES_2
parent: F476/F477 manifest rank40 negatives
evidence_level: VERIFIED
compute: two pair-beam runs; no solver runs
author: yale-codex
---

# F478/F479: manifest rank-8 and rank-10 HW40 seeds are negative

## Setup

F478/F479 continued the F473 manifest sweep:

- F478 rank 8: W1=`0x5228ed8d 0x61a1a29c 0x6a3a8429 0x6b9e01d3`
- F479 rank 10: W1=`0x5228ed8d 0x61a1a29c 0xea3a8c29 0x258bdd92`

Both used the standard wider c/g beam: pool 1024, beam 1024, max pairs 6,
max radius 12.

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F478_bit13_manifest_rank8_hw40_pair_beam_cg.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F479_bit13_manifest_rank10_hw40_pair_beam_cg.json`

## Results

| Run | Manifest rank | Start HW | Best selected non-seed | Seed stayed best |
|---|---:|---:|---:|---|
| F478 | 8 | 40 | 36 | no; found current HW36 floor |
| F479 | 10 | 40 | 39 | no; did not reach HW36 |

F478 counters:

- expanded: 3,483,767
- bridge pass: 3,483,588
- HW <= 40: 2
- HW < 40: 2
- wall: 294.05s

F479 counters:

- expanded: 3,493,418
- bridge pass: 3,493,343
- HW <= 40: 12
- HW < 40: 10
- wall: 296.69s

## Verdict

F478 is connected back to the known HW36 basin but does not improve it.
F479 appears to sit in a shallower HW39 basin under the current objective.
The remaining manifest seeds are lower-priority unless paired with a new
pair-pool construction or an objective that deliberately preserves the
non-record basin instead of falling back into HW36.
