---
date: 2026-05-01
bet: block2_wang
status: PATH_C_BIT13_HW35_RADIUS4_CLOSED
parent: F487 manifest-rank HW35 breakthrough
evidence_level: VERIFIED
compute: 11367264 exact forward evaluations; bridge relaxed; decomposition and manifest tooling
author: yale-codex
---

# F488/F491: bit13 HW35 radius-4 closure plus post-breakthrough tooling

## Setup

F487 found the new bit13 floor:

`bit13_m916a56aa`, HW=35, W1=`0x5228ed8d 0x61a1a29c 0x6a7a8409 0xc7d515db`

F488/F489 test whether this point has a raw-Hamming escape in W57..W60.
Both runs use `--relax-bridge`, so bridge-rejected cascade-valid neighbors
still count for HW ties/improvements.

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F488_bit13_hw35_hamming3_relaxed.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F489_bit13_hw35_full_radius4_relaxed.json`
- `headline_hunt/bets/block2_wang/encoders/analyze_pair_beam_decomposition.py`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F490_F487_hw35_pair_decomposition.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F491_bit13_basin_seed_manifest_post_hw35.json`

## Radius-4 Closure Result

| Radius set | Total | Cascade-1 pass | Bridge pass | Bridge reject | HW <= 35 | HW < 35 |
|---|---:|---:|---:|---:|---:|---:|
| Hamming 1..3 | 349,632 | 349,632 | 341,755 | 7,877 | 0 | 0 |
| Hamming 1..4 | 11,017,632 | 11,017,632 | 10,691,879 | 325,753 | 0 | 0 |

Best seen remained the seed:

- HW=35
- score=86.364
- W1=`0x5228ed8d 0x61a1a29c 0x6a7a8409 0xc7d515db`
- hw63=`[10,7,1,0,9,7,1,0]`

## F490 Pair-Decomposition Tool

F490 adds `analyze_pair_beam_decomposition.py`, which reads a pair-beam
artifact and explains how a target record is covered by the selected two-bit
pair pool. On the F487 HW35 record:

- selected pair count: 1024
- internal pairs fully inside the HW35 move: 59
- frontier pairs touching one HW35 bit: 386
- exact six-pair covers found: yes

Lowest rank-sum exact cover:

| Pair rank | Pair |
|---:|---|
| 348 | W59:b22 + W60:b29 |
| 114 | W60:b13 + W60:b22 |
| 28 | W60:b30 + W60:b31 |
| 23 | W60:b3 + W60:b15 |
| 5 | W60:b16 + W60:b17 |
| 32 | W60:b19 + W60:b27 |

The useful lesson is that the HW35 basin required at least one locally weak
pair: rank 348 by standalone pair HW. Future searches should not over-prune
pair pools just because the best individual two-bit moves look mediocre.

## F491 Refreshed Seed Manifest

F491 regenerates the reusable bit13 basin manifest after the HW35 result.
It includes F458/F462/F467/F471/F472 plus F486/F487 and contains 43 deduped
seeds. Top entries:

| Rank | HW | Score | W1 |
|---:|---:|---:|---|
| 1 | 35 | 86.364 | `0x5228ed8d 0x61a1a29c 0x6a7a8409 0xc7d515db` |
| 2 | 36 | 85.471 | `0x5228ed8d 0x61a1a29c 0x6a3a8409 0x2c9e917b` |
| 3 | 38 | 83.667 | `0x5228ed8d 0x61a1a29c 0xea3a8429 0x2d9f1a3b` |
| 4 | 38 | 83.667 | `0x5228ed8d 0x61a1a29c 0xea3a8c29 0x258bfd92` |
| 5 | 39 | 82.757 | `0x5228ed8d 0x61a1a29c 0xea3a8c29 0x2589119a` |
| 6 | 39 | 82.757 | `0x5228ed8d 0x61a1a29c 0xea3a8c29 0x2d8b5d92` |

## Verdict

The bit13 HW35 near-residual is full W57..W60 radius-4 closed, including
bridge-rejected neighbors. The closure result says local raw Hamming shells
remain boxed in; the decomposition result says productive escapes can still
use individually poor two-bit primitives when they are composed in the right
basin.

Current Path C panel:

- bit13 HW=35
- bit28 HW=42
- bit24 HW=43

Next useful work: restart pair beam from HW35 with a wider/deeper pair pool,
then sample the refreshed F491 manifest ranks that are structurally distinct
from the HW35/HW36 basin.
