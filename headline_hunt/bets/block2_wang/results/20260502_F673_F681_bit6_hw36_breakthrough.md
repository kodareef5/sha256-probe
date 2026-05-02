---
date: 2026-05-02
bet: block2_wang
status: PATH_C_BIT6_HW36_BREAKTHROUGH
parent: F650/F670-F672 bit6 tail manifests
evidence_level: VERIFIED_AND_LOCALLY_CLOSED
author: yale-codex
---

# F673/F681: bit6 drops from HW42 to HW36

## Setup

After F664 moved bit28 to HW39, `bit6_m6e173e58` was the lone HW42 tail.
F670/F672 had consumed F650 ranks 4-6 without improving the floor, but F670
exposed an alternate HW42 seed:

`0x58e6e512 0xf2a359c0 0x2a4a0de5 0x5d7dda4d`

F673/F676 tested direct HW42 continuation plus the next two side ranks.

## Pair-beam results

| Run | Source | Init HW | Best HW | Score | Best W57..W60 |
|---|---|---:|---:|---:|---|
| F673 | current HW42 rank 1 | 42 | 42 | 78.385 | `0x58e6e512 0xf2a359c0 0x22420dc5 0x9d542a79` |
| F674 | alternate HW42 from F670 | 42 | 36 | 83.545 | `0x58e6e512 0xf2a359c0 0x2a4a0de5 0x2f7e1a4d` |
| F675 | F650 rank 7 | 46 | 42 | 78.385 | `0x58e6e512 0xf2a359c0 0x22420dc5 0x9d542a79` |
| F676 | F650 rank 8 | 46 | 41 | 77.514 | `0x58e6e512 0xf2a359c0 0x28420d45 0xe45c2a5e` |

F674 is the headline. The HW36 residual breakdown is:

`[11, 5, 2, 0, 9, 8, 1, 0]`

The move from the alternate HW42 seed is W60-only at bits:

`14, 15, 16, 17, 25, 28, 29, 30`

## Cert-pin validation

F674 is a confirmed near-residual, not a full collision:

| Witness | kissat | cadical |
|---|---|---|
| F674 bit6 HW36 | UNSAT, 0.014s | UNSAT, 0.022s |

## Local closure

Exact bridge-relaxed closure around F674:

| Run | Floor | Slots | Radius | Total at max radius | Bridge pass | Bridge reject | HW<=floor | HW<floor |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| F677 | 36 | W60 | 6 | 906,192 | 906,192 | 0 | 0 | 0 |
| F678 | 36 | W59,W60 | 4 | 635,376 | 635,376 | 0 | 0 | 0 |

F679 refreshed the bit6 post-HW36 manifest with 103 seeds. Top seeds:

| Rank | HW | Score | W57..W60 |
|---:|---:|---:|---|
| 1 | 36 | 83.545 | `0x58e6e512 0xf2a359c0 0x2a4a0de5 0x2f7e1a4d` |
| 2 | 39 | 79.143 | `0x58e6e512 0xf2a359c0 0x2a4a0de5 0xad7cca4e` |
| 3 | 41 | 77.514 | `0x58e6e512 0xf2a359c0 0x28420d45 0xe45c2a5e` |

## Post-HW36 follow-up

| Run | Source | Init HW | Best HW | Score | Best W57..W60 |
|---|---|---:|---:|---:|---|
| F680 | F679 rank 1 | 36 | 36 | 83.545 | `0x58e6e512 0xf2a359c0 0x2a4a0de5 0x2f7e1a4d` |
| F681 | F679 rank 2 | 39 | 36 | 83.545 | `0x58e6e512 0xf2a359c0 0x2a4a0de5 0x2f7e1a4d` |

No sub-HW36 record was found. F681 shows the rank-2 HW39 side seed reconnects
to the HW36 basin.

## Updated panel

The old HW42 tail is gone. Current Path C panel tail:

| Floor HW | Cands |
|---:|---|
| 35 | bit13, bit1, bit4 |
| 36 | bit3, bit6 |
| 37 | bit15, bit18, bit25, bit29, bit14 |
| 38 | bit20 |
| 39 | bit2, bit12, bit26, bit28 |
| 40 | bit24 |

The new practical tail is bit24 HW40, followed by the HW39 tier
`bit2/bit12/bit26/bit28`.
