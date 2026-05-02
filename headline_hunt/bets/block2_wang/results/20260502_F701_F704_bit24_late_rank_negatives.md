---
date: 2026-05-02
bet: block2_wang
status: PATH_C_BIT24_LATE_RANK_NEGATIVES
parent: F527 bit24 post-HW40 manifest; F694/F700 alternate HW40
evidence_level: SEARCH_NEGATIVE
author: yale-codex
---

# F701/F704: bit24 late-rank negatives

## Setup

F697 showed that late F527 bit24 manifest ranks could still uncover distinct
basins, even though the alternate basin remained at HW40. F701/F704 therefore
continued the same standard pair-beam pass over the next untested F527 ranks:
19, 20, 21, and 22.

Same pair-beam configuration as the prior tranche:

- slots: W57..W60
- pair pool: 1024
- beam width: 1024
- max pairs: 6
- max radius: 12
- pair rank: HW
- penalty regs: c,g

## Results

| Run | Source | Init HW | Best HW | Score | Best W57..W60 |
|---|---|---:|---:|---:|---|
| F701 | F527 rank 19 | 45 | 41 | 77.514 | `0x4be5074f 0x429efff2 0xe89458af 0x2979e27d` |
| F702 | F527 rank 20 | 45 | 43 | 75.846 | `0x4be5074f 0x429efff2 0xec9458af 0x3209edfa` |
| F703 | F527 rank 21 | 45 | 44 | 78.143 | `0x4be5074f 0x429efff2 0xe89458af 0x3a19ebf5` |
| F704 | F527 rank 22 | 46 | 42 | 71.000 | `0x4be5074f 0x429efff2 0xe8b458af 0x2a118bfc` |

No run found HW40, and no run threatened the HW40 floor.

Counters:

| Run | Expanded | Bridge pass | HW<=init | HW<init |
|---|---:|---:|---:|---:|
| F701 | 3,708,182 | 3,706,545 | 18 | 9 |
| F702 | 3,812,660 | 3,812,221 | 5 | 3 |
| F703 | 3,644,500 | 3,643,319 | 20 | 5 |
| F704 | 3,560,848 | 3,559,670 | 30 | 21 |

## Selector tool

Added:

- `headline_hunt/bets/block2_wang/encoders/select_manifest_followups.py`

The helper scans a basin manifest, matches seed `W` values against existing
pair-beam artifact `init_W` values, and prints the next untested seeds. It was
used as a sanity check before this tranche: the next untested F527 bit24 ranks
were exactly 19..22. After F701/F704, the next F527 bit24 ranks are 23..26.

This should reduce accidental duplicate runs and stale-W hand selection in the
next tail passes.

## Tail

The active Path C tail remains unchanged:

| Floor HW | Cands |
|---:|---|
| 39 | bit2, bit12, bit26, bit28 |
| 40 | bit24 |

Bit24 remains the sole HW40 candidate, but ranks 1..22 of the original F527
post-HW40 manifest have now been consumed or superseded by direct follow-up.
