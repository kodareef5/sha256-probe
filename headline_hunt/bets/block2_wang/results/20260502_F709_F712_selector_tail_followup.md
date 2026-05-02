---
date: 2026-05-02
bet: block2_wang
status: PATH_C_SELECTOR_TAIL_FOLLOWUP_NEGATIVE
parent: F705/F708 mixed tail follow-up
evidence_level: SEARCH_NEGATIVE
author: yale-codex
---

# F709/F712: selector-ranked tail follow-up

## Setup

The manifest selector chose the next untested low-HW seeds:

- bit24 F527 ranks 25 and 26,
- bit26 F650 rank 6,
- bit28 F669 rank 6.

All four used the standard W57..W60 pair-beam configuration
(`pair_pool=1024`, `beam_width=1024`, `max_pairs=6`, `max_radius=12`,
`pair_rank=hw`, `penalty_regs=c,g`).

## Results

| Run | Cand | Source | Init HW | Best HW | Score | Best W57..W60 |
|---|---|---|---:|---:|---:|---|
| F709 | bit24 | F527 rank 25 | 46 | 41 | 80.923 | `0x4be5074f 0x429efff2 0xe89458a7 0xc5380a74` |
| F710 | bit24 | F527 rank 26 | 46 | 40 | 74.412 | `0x4be5074f 0x429efff2 0xf09458a7 0xa4fe0078` |
| F711 | bit26 | F650 rank 6 | 42 | 39 | 81.000 | `0xbfe07c65 0x012df925 0xae91ccb9 0x715d9e89` |
| F712 | bit28 | F669 rank 6 | 42 | 41 | 80.923 | `0x307cf0e7 0x853d504a 0x78f16a7d 0xe1d42d72` |

No run found a new floor.

F710 reconnects to the known bit24 HW40 witness from F521/F682. F711
reconnects to the known bit26 HW39 witness from F642/F693.

Counters:

| Run | Expanded | Bridge pass | HW<=init | HW<init |
|---|---:|---:|---:|---:|
| F709 | 3,673,010 | 3,671,420 | 39 | 17 |
| F710 | 3,676,394 | 3,675,183 | 28 | 18 |
| F711 | 3,555,750 | 3,555,750 | 5 | 4 |
| F712 | 3,665,706 | 3,664,406 | 10 | 10 |

## Tail

The active Path C tail remains unchanged:

| Floor HW | Cands |
|---:|---|
| 39 | bit2, bit12, bit26, bit28 |
| 40 | bit24 |

The selector-ranked tranches are now behaving consistently: bit24 side ranks
either reconnect to HW40 or land at HW41+, while bit26/bit28 side ranks
reconnect to or remain above their HW39 floors.
