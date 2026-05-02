---
date: 2026-05-02
bet: block2_wang
status: PATH_C_TAIL_FOLLOWUP_BIT28_HW39
parent: F650 tail manifests; F532/F533 remote updates
evidence_level: VERIFIED_AND_LOCALLY_CLOSED
author: yale-codex
---

# F653/F672: bit28 drops to HW39; bit6 remains tail

## Setup

After rebasing over Mac's F532/F533 work, bit12 already had a stronger F532
HW39 record and bit2 had a wider-param HW39 floor check. The remaining open
tail work was:

- test whether the F650 bit12/bit26 manifests contained anything below the
  now-known floors,
- consume the under-tested bit28 manifest ranks, and
- continue bit6 ranks after F644/F645.

All pair-beams used the standard c/g settings:
`pair_pool=1024`, `beam_width=1024`, `max_pairs=6`, `max_radius=12`,
`pair_rank=hw`, `penalty_regs=c,g`, `penalty_weight=2.0`.

## F653/F656: bit12 and bit26

| Run | Cand | Source rank | Init HW | Best HW | Score | Best W57..W60 |
|---|---|---:|---:|---:|---:|---|
| F653 | bit12 | F650 rank 2 | 40 | 40 | 81.842 | `0x6e835350 0x8322f4cf 0x30dd0ed5 0x818a358c` |
| F654 | bit12 | F650 rank 4 | 41 | 40 | 81.842 | `0x6e835350 0x8322f4cf 0x30dd0ed1 0x927f3e65` |
| F655 | bit26 | F650 rank 2 | 41 | 39 | 81.000 | `0xbfe07c65 0x012df925 0xae91ccb9 0x715d9e89` |
| F656 | bit26 | F650 rank 3 | 41 | 40 | 81.842 | `0xbfe07c65 0x012df925 0xac91cc39 0x65755d06` |

These are useful negatives/reconnects only. F532 already owns bit12 HW39, and
F642/F655 own bit26 HW39.

## F657/F669: bit28

The F521 bit28 manifest had not been consumed deeply. Ranks 2-5 exposed a new
HW41 layer, and a direct continuation from the best HW41 seed then dropped to
HW39.

| Run | Source | Init HW | Best HW | Score | Best W57..W60 |
|---|---|---:|---:|---:|---|
| F657 | manifest rank 2 | 42 | 42 | 80.000 | `0x307cf0e7 0x853d504a 0x78f16a7e 0xccf479b4` |
| F658 | manifest rank 3 | 44 | 41 | 77.514 | `0x307cf0e7 0x853d504a 0x78f06a7e 0xf67271e6` |
| F659 | manifest rank 4 | 44 | 41 | 75.667 | `0x307cf0e7 0x853d504a 0x78f16a5e 0x62f489f2` |
| F660 | manifest rank 5 | 44 | 41 | 75.667 | `0x307cf0e7 0x853d504a 0x78f16a5e 0x62f489f2` |
| F664 | post-HW41 rank 1 | 41 | 39 | 79.143 | `0x307cf0e7 0x853d504a 0x38f06a6e 0x7f7479d4` |
| F665 | post-HW41 rank 2 | 41 | 41 | 80.923 | `0x307cf0e7 0x853d504a 0x78f16a5d 0x44e3a9d2` |
| F666 | post-HW41 rank 3 | 41 | 41 | 69.455 | `0x307cf0e7 0x853d504a 0x78f16a76 0xbff45dfc` |

F664 is the headline. The HW39 residual breakdown is:

`[11, 9, 2, 0, 8, 7, 2, 0]`

Cert-pin validation was run on both HW41 basins and on the F664 HW39 witness.
All were UNSAT with kissat and cadical.

## Local closure

The best F658 HW41 witness was closed before the F664 continuation:

| Run | Floor | Slots | Radius | Total at max radius | Bridge pass | Bridge reject | HW<=floor | HW<floor |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| F661 | 41 | W60 | 6 | 906,192 | 906,159 | 33 | 0 | 0 |
| F662 | 41 | W59,W60 | 4 | 635,376 | 635,370 | 6 | 0 | 0 |

The F664 HW39 witness was then closed:

| Run | Floor | Slots | Radius | Total at max radius | Bridge pass | Bridge reject | HW<=floor | HW<floor |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| F667 | 39 | W60 | 6 | 906,192 | 906,192 | 0 | 0 | 0 |
| F668 | 39 | W59,W60 | 4 | 635,376 | 635,376 | 0 | 0 | 0 |

F663 and F669 refreshed bit28 manifests:

- `search_artifacts/20260502_F663_bit28_post_hw41_basin_manifest.json`: 115 seeds.
- `search_artifacts/20260502_F669_bit28_post_hw39_basin_manifest.json`: 99 seeds.

## F670/F672: bit6

| Run | Source rank | Init HW | Best HW | Score | Best W57..W60 |
|---|---:|---:|---:|---:|---|
| F670 | F650 rank 4 | 45 | 42 | 76.684 | `0x58e6e512 0xf2a359c0 0x2a4a0de5 0x5d7dda4d` |
| F671 | F650 rank 5 | 45 | 42 | 78.385 | `0x58e6e512 0xf2a359c0 0x22420dc5 0x9d542a79` |
| F672 | F650 rank 6 | 45 | 45 | 77.209 | `0x58e6e512 0xf2a359c0 0x28460dd5 0x9d5aa2cc` |

No bit6 improvement. It remains the lone HW42 tail.

## Updated panel

After F532 and F664, the current Path C panel tail is:

| Floor HW | Cands |
|---:|---|
| 35 | bit13, bit1, bit4 |
| 36 | bit3 |
| 37 | bit15, bit18, bit25, bit29, bit14 |
| 38 | bit20 |
| 39 | bit2, bit12, bit26, bit28 |
| 40 | bit24 |
| 42 | bit6 |

The practical next target is bit6. Bit28 should continue from F669 ranks 2+
later, but F664/F667/F668 make HW39 the current verified bit28 floor.
