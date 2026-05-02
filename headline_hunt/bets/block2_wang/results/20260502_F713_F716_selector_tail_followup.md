---
date: 2026-05-02
bet: block2_wang
status: PATH_C_SELECTOR_TAIL_FOLLOWUP_NEGATIVE
parent: F709/F712 selector-ranked tail follow-up
evidence_level: SEARCH_NEGATIVE
author: yale-codex
---

# F713/F716: selector-ranked tail follow-up

## Setup

This tranche continued the selector-ranked pass:

- bit24 F527 ranks 27 and 28,
- bit26 F650 rank 7,
- bit28 F669 rank 8.

All four used the standard W57..W60 pair-beam configuration
(`pair_pool=1024`, `beam_width=1024`, `max_pairs=6`, `max_radius=12`,
`pair_rank=hw`, `penalty_regs=c,g`).

## Results

| Run | Cand | Source | Init HW | Best HW | Score | Best W57..W60 |
|---|---|---|---:|---:|---:|---|
| F713 | bit24 | F527 rank 27 | 46 | 43 | 79.073 | `0x4be5074f 0x429efff2 0xf09458a7 0x51f6fdf8` |
| F714 | bit24 | F527 rank 28 | 46 | 42 | 80.000 | `0x4be5074f 0x429efff2 0xf0b458a7 0x50fe6a79` |
| F715 | bit26 | F650 rank 7 | 42 | 41 | 80.923 | `0xbfe07c65 0x012df925 0xae91cdb9 0x53d9ce15` |
| F716 | bit28 | F669 rank 8 | 42 | 41 | 69.455 | `0x307cf0e7 0x853d504a 0x78f16a76 0xbff45dfc` |

No run found a new floor.

Counters:

| Run | Expanded | Bridge pass | HW<=init | HW<init |
|---|---:|---:|---:|---:|
| F713 | 3,624,118 | 3,623,119 | 31 | 26 |
| F714 | 3,714,815 | 3,713,933 | 24 | 13 |
| F715 | 3,598,424 | 3,598,424 | 8 | 5 |
| F716 | 3,658,560 | 3,656,364 | 6 | 3 |

## Tail

The active Path C tail remains unchanged:

| Floor HW | Cands |
|---:|---|
| 39 | bit2, bit12, bit26, bit28 |
| 40 | bit24 |

At this point, F527 bit24 ranks 1..28 have been consumed or superseded by
direct follow-up, and the current operator has not found a sub-HW40 escape.
