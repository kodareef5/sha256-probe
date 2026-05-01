---
date: 2026-05-01
bet: block2_wang
status: PATH_C_HW35_PAIR_BEAM_RESTART_NEGATIVE
parent: F488-F491 HW35 closure and decomposition
evidence_level: VERIFIED
compute: two pair-beam runs; no solver runs
author: yale-codex
---

# F492/F493: direct HW35 pair-beam restarts are negative

## Setup

F488/F489 closed the F487 HW35 witness through relaxed radius 4. F490 then
showed that the HW35 breakthrough itself required at least one selected-pool
pair as deep as rank 348, so F492/F493 tested direct restarts from HW35:

- F492: pair pool 1024, beam 1024, pair rank hw, c/g penalty.
- F493: pair pool 2048, beam 1024, pair rank hw, c/g penalty.

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F492_bit13_hw35_pair_beam_cg.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F493_bit13_hw35_pair_beam_cg_pool2048.json`

## Results

| Run | Pair pool | Expanded | Bridge pass | Best selected non-seed | Seed stayed best | Wall |
|---|---:|---:|---:|---:|---|---:|
| F492 | 1024 | 3,477,116 | 3,476,515 | HW39 | yes | 273.84s |
| F493 | 2048 | 7,999,859 | 7,999,223 | HW39 | yes | 650.32s |

Both runs converged to the same best non-seed:

- W1=`0x5228ed8d 0x61a1a29c 0x6a7a8409 0xccd551fb`
- HW=39
- score=82.757
- move from HW35 seed: W60 bits 5,10,14,24,25,27.

Depth summary was identical in both runs:

| Depth | Best HW | Best score |
|---:|---:|---:|
| 1 | 48 | 74.391 |
| 2 | 47 | 75.333 |
| 3 | 39 | 82.757 |
| 4 | 39 | 82.757 |
| 5 | 39 | 82.757 |
| 6 | 39 | 82.757 |

## Verdict

The direct HW35 seed is boxed in under the current pair-beam family. Doubling
the pair pool from 1024 to 2048 did not change the best basin. The next useful
move is not another larger direct HW35 restart; it is a seed change using the
F491 manifest, especially the new F486/F487-derived HW40 basins that are not
just the prior HW36/HW35 neighborhood.
