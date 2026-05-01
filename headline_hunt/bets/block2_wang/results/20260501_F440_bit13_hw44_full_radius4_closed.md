---
date: 2026-05-01
bet: block2_wang
status: PATH_C_BIT13_HW44_FULL_RADIUS4_CLOSED
parent: F436 bit13 HW=44, F437 Hamming-3 closure, F439 W59/W60 radius-4 closure
evidence_level: VERIFIED
compute: 11017632 exact forward evaluations; 578.99s wall; 0 solver runs
author: yale-codex
---

# F440: bit13 HW=44 full W57..W60 radius-4 closure

## Setup

F436 showed that a Hamming-distance-4 move can escape an apparently stable
bit13 basin: the prior HW=49 point was Hamming-3 closed, but a radius-4
change reached HW=44.

F440 closes the corresponding exact radius-4 question around the new HW=44
record by enumerating every Hamming radius 1..4 bit flip over all 128 bits
of W1[57..60].

Input witness:

`W1 = 0x5228ed8d 0x61a1a29c 0xea6a8c21 0x3dbfd852`

Artifact:

`headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F440_bit13_hw44_full_radius4_enumeration.json`

## Result

| Radius | Total | Cascade-1 pass | Bridge pass | HW <= 44 | HW < 44 |
|---:|---:|---:|---:|---:|---:|
| 1 | 128 | 128 | 127 | 0 | 0 |
| 2 | 8,128 | 8,128 | 8,003 | 0 | 0 |
| 3 | 341,376 | 341,376 | 333,625 | 0 | 0 |
| 4 | 10,668,000 | 10,668,000 | 10,350,125 | 0 | 0 |
| total | 11,017,632 | 11,017,632 | 10,691,880 | 0 | 0 |

Best seen remained the seed itself:

- HW=44
- score=71.526
- `hw63=[13,8,3,0,10,7,3,0]`
- `diff63=[0x30af3824,0x15254400,0x80020800,0x00000000,0x0325b082,0x0d024410,0x80020800,0x00000000]`

## Verdict

The bit13 HW=44 point is exactly closed through radius 4 across the full
W57..W60 coordinate system. This is stronger than F437's Hamming-3 closure
and directly addresses the escape distance that produced the F436
breakthrough.

Next productive directions:

1. Try radius >= 5 only if compute is cheap enough, because radius 4 is now
   exhausted exactly.
2. Move to a different coordinate system, such as carry-chart preserving
   operators, schedule-derived masks, or geometry relaxation.
3. Spend exact enumeration budget on bit24 HW=43, because it is now the
   global Path C floor and may have a different escape geometry.
