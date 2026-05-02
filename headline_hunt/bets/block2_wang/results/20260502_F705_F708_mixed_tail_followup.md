---
date: 2026-05-02
bet: block2_wang
status: PATH_C_MIXED_TAIL_FOLLOWUP_NEGATIVE
parent: F701/F704 bit24 late-rank negatives; F690/F693 HW39 tier follow-up
evidence_level: SEARCH_NEGATIVE
author: yale-codex
---

# F705/F708: mixed tail follow-up

## Setup

After F701/F704 consumed bit24 ranks 19..22, the next compute slice mixed:

- two more bit24 side ranks, because bit24 remains the only HW40 candidate,
- one bit26 HW41 side rank, because bit26 is in the HW39 tier and still had
  low-HW untested side seeds,
- one bit28 HW42 side rank, for the same HW39-tier pressure.

All four used the standard pair-beam configuration:

- slots: W57..W60
- pair pool: 1024
- beam width: 1024
- max pairs: 6
- max radius: 12
- pair rank: HW
- penalty regs: c,g

## Results

| Run | Cand | Source | Init HW | Best HW | Score | Best W57..W60 |
|---|---|---|---:|---:|---:|---|
| F705 | bit24 | F527 rank 23 | 46 | 43 | 79.073 | `0x4be5074f 0x429efff2 0xe09458af 0xe6560e70` |
| F706 | bit24 | F527 rank 24 | 46 | 41 | 77.514 | `0x4be5074f 0x429efff2 0xe89458af 0x2979e27d` |
| F707 | bit26 | F650 rank 4 | 41 | 39 | 81.000 | `0xbfe07c65 0x012df925 0xae91ccb9 0x715d9e89` |
| F708 | bit28 | F669 rank 5 | 42 | 42 | 80.000 | `0x307cf0e7 0x853d504a 0x78f06a76 0xbf7463dc` |

No run found a new floor.

F707 is useful but not new: it reconnects the bit26 side seed back to the
known HW39 witness from F642/F693.

Counters:

| Run | Expanded | Bridge pass | HW<=init | HW<init |
|---|---:|---:|---:|---:|
| F705 | 3,600,643 | 3,599,399 | 39 | 23 |
| F706 | 3,563,798 | 3,562,536 | 41 | 34 |
| F707 | 3,591,702 | 3,591,702 | 6 | 2 |
| F708 | 3,649,207 | 3,645,781 | 6 | 0 |

## Tail

The active Path C tail remains unchanged:

| Floor HW | Cands |
|---:|---|
| 39 | bit2, bit12, bit26, bit28 |
| 40 | bit24 |

This tranche reinforces the current pattern: bit24 late ranks are falling into
HW41+ side basins, while bit26/bit28 side ranks mostly reconnect to or stay
above their current HW39 floors.
