---
date: 2026-05-02
bet: block2_wang
status: PATH_C_BIT24_HW40_FLOOR_FOLLOWUP
parent: F527 bit24 post-HW40 manifest; F673/F681 bit6 breakthrough
evidence_level: SEARCH_NEGATIVE
author: yale-codex
---

# F682/F686: bit24 HW40 follow-up

## Setup

After F674 moved bit6 from HW42 to HW36, `bit24_mdc27e18c` became the
highest-HW Path C candidate at HW40. Prior work had already closed the F521
HW40 witness under W59/W60 radius 4 and had tested several post-floor side
ranks. F682/F685 fills remaining obvious gaps:

- direct standard pair-beam restart from the HW40 witness,
- F527 post-HW40 manifest rank 11,
- F527 post-HW40 manifest ranks 13 and 14.

## Results

| Run | Source | Init HW | Best HW | Score | Best W57..W60 |
|---|---|---:|---:|---:|---|
| F682 | HW40 rank 1 | 40 | 40 | 74.412 | `0x4be5074f 0x429efff2 0xf09458a7 0xa4fe0078` |
| F683 | F527 rank 11 | 44 | 40 | 74.412 | `0x4be5074f 0x429efff2 0xf09458a7 0xa4fe0078` |
| F684 | F527 rank 13 | 45 | 41 | 77.514 | `0x4be5074f 0x429efff2 0xe89458af 0x2979e27d` |
| F685 | F527 rank 14 | 45 | 41 | 77.514 | `0x4be5074f 0x429efff2 0xe89458af 0x2979e27d` |

No sub-HW40 record was found.

The direct HW40 restart is especially useful as negative evidence:

- expanded: 3,741,489 states
- bridge pass: 3,740,840
- HW<=40: 0
- HW<40: 0

F683 shows rank 11 reconnects to the known HW40 floor. F684/F685 expose a
shared HW41 side basin but do not threaten the floor.

F686 refreshed a bit24 post-follow-up manifest with 104 seeds.

## Updated tail

The active Path C tail remains:

| Floor HW | Cands |
|---:|---|
| 39 | bit2, bit12, bit26, bit28 |
| 40 | bit24 |

Bit24 remains the highest-HW candidate, but this checkpoint strengthens the
case that the current coordinate system is boxed in around HW40.
