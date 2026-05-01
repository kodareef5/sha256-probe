---
date: 2026-05-01
bet: block2_wang
status: PATH_C_MANIFEST_RANK39_NEGATIVES
parent: F473 basin seed manifest
evidence_level: VERIFIED
compute: two pair-beam runs; no solver runs
author: yale-codex
---

# F474/F475: manifest rank-4 and rank-5 HW39 seeds are negative

## Setup

F474/F475 used the F473 seed manifest directly, testing the top two
untested HW39 basins:

- F474: rank 4, W1=`0x5228ed8d 0x61a1a29c 0xea3a8c29 0x2589119a`
- F475: rank 5, W1=`0x5228ed8d 0x61a1a29c 0xea3a8c29 0x2d8b5d92`

Both used the standard wider c/g beam: pool 1024, beam 1024, max pairs 6,
max radius 12.

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F474_bit13_manifest_rank4_hw39_pair_beam_cg.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F475_bit13_manifest_rank5_hw39_pair_beam_cg.json`

## Results

| Run | Manifest rank | Start HW | Best selected non-seed | Seed stayed best |
|---|---:|---:|---:|---|
| F474 | 4 | 39 | 38 | yes |
| F475 | 5 | 39 | 38 | yes |

Neither run reached the current HW36 floor.

F474 counters:

- expanded: 3,447,407
- bridge pass: 3,446,738
- HW <= 39: 7
- HW < 39: 3
- wall: 294.18s

F475 counters:

- expanded: 3,467,948
- bridge pass: 3,467,872
- HW <= 39: 9
- HW < 39: 5
- wall: 297.03s

## Verdict

Manifest ranks 4 and 5 are not productive under the current c/g beam. The
next manifest seeds to test are the rank-6+ HW40 basins, especially those
with W59=`0x6a3a8409`, which differ more from the earlier failed HW39
cluster.
