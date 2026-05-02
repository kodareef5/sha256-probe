---
date: 2026-05-02
bet: block2_wang
status: PATH_C_BIT24_ALT_HW40_FOLLOWUP
parent: F527 bit24 post-HW40 manifest; F682/F686 bit24 floor follow-up
evidence_level: SEARCH_NEGATIVE
author: yale-codex
---

# F694/F700: bit24 late-rank follow-up and alternate HW40

## Setup

After F682/F686, `bit24_mdc27e18c` remained the lone HW40 tail in the
16-candidate Path C panel. F694/F697 consumed four later F527 post-HW40
manifest ranks, then F698/F700 checked the new HW40 side witness exposed by
F697.

This is not a new floor. It is useful because F697 found a distinct HW40
witness with a stronger bridge score than the earlier F521/F682 HW40 seed:

- prior HW40 score: 74.412
- F697 alternate HW40 score: 76.429

## Results

| Run | Source | Init HW | Best HW | Score | Best W57..W60 |
|---|---|---:|---:|---:|---|
| F694 | F527 rank 15 | 45 | 43 | 77.500 | `0x4be5074f 0x429efff2 0xec9458af 0x3d6c8e7b` |
| F695 | F527 rank 16 | 45 | 43 | 79.073 | `0x4be5074f 0x429efff2 0xf09458a7 0x51f6fdf8` |
| F696 | F527 rank 17 | 45 | 43 | 74.105 | `0x4be5074f 0x429efff2 0xec9458af 0x360b8e79` |
| F697 | F527 rank 18 | 45 | 40 | 76.429 | `0x4be5074f 0x429efff2 0xe9b458af 0xf51ded35` |
| F700 | F697 HW40 direct restart | 40 | 40 | 76.429 | `0x4be5074f 0x429efff2 0xe9b458af 0xf51ded35` |

F697 residual breakdown:

- `hw63 = [9, 8, 2, 0, 9, 9, 3, 0]`
- active registers: `a,b,c,e,f,g`
- `da_eq_de = false`
- W59/W60 move from its rank-18 init flips W59 bits 27,28 and W60 bits
  0,2,3,6,9,21,24,26,28,30.

## Cert-pin

F697 is a confirmed near-residual, not a full collision:

| Witness | kissat | cadical |
|---|---|---|
| F697 bit24 HW40 | UNSAT, 0.011s | UNSAT, 0.023s |

Validation record:

- `headline_hunt/bets/block2_wang/results/20260502_F697_certpin_validation.json`

## Local closure around F697

| Run | Neighborhood | Candidates | Bridge pass | HW<=40 | HW<40 | Best |
|---|---|---:|---:|---:|---:|---|
| F698 | W60 radius 6 | 1,149,016 | 1,149,016 | 0 | 0 | HW40 score 76.429 |
| F699 | W59/W60 radius 4 | 679,120 | 679,120 | 0 | 0 | HW40 score 76.429 |
| F700 | standard pair-beam restart | 3,700,178 expanded | 3,700,178 | 0 | 0 | HW40 score 76.429 |

No HW39 witness was found around the alternate HW40 seed.

## Tail

The active Path C tail remains:

| Floor HW | Cands |
|---:|---|
| 39 | bit2, bit12, bit26, bit28 |
| 40 | bit24 |

This strengthens the current conclusion: bit24 has at least two distinct HW40
basins under the present W-cube operators, but both are locally boxed in.
