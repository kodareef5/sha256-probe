---
date: 2026-05-01
bet: block2_wang
status: PATH_C_BIT13_HW44_RADIUS6_CONFIRMED
parent: F436 bit13 HW=44, F437 Hamming-3 closure
evidence_level: VERIFIED
compute: 0 solver search; 132.8s seeded annealing; 0 cert-pin runs
author: yale-codex
---

# F438: bit13 HW=44 survives radius-6 seeded anneal

## Setup

F436 found bit13 HW=44 using radius-6 seeded anneal from HW=49.
F437 then proved the HW=44 point is Hamming-3 isolated. F438 repeats
the F436 radius-6 pass, now seeded from the HW=44 record itself.

Parameters:

- candidate: `bit13_m916a56aa`
- init W1[57..60]: `0x5228ed8d, 0x61a1a29c, 0xea6a8c21, 0x3dbfd852`
- 12 restarts x 200,000 iterations
- `method=anneal`, `max_flips=6`
- temperature 0.5 -> 0.01
- tabu size 1024

Artifact:

`headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F438_bit13_hw44_radius6_seeded.json`

## Result

All 12/12 restarts stayed at the HW=44 seed:

| Outcome | Seeds | Best score | Best HW |
|---|---:|---:|---:|
| Stayed at HW=44 seed | 12 | 71.526 | 44 |
| Found HW < 44 | 0 | n/a | n/a |

No new cert-pin runs were needed.

## Findings

### Finding 1: the F436 breakthrough does not immediately repeat

F436 showed a radius-4 escape from HW=49 to HW=44. F438 shows that
seeding from HW=44 and allowing radius-6 mutations does not produce a
further record at the same compute scale.

### Finding 2: bit13 now matches bit24/bit28 local stability

After F438:

- bit24 HW=43: Hamming-3 closed, radius-6 seeded stable.
- bit13 HW=44: Hamming-3 closed, radius-6 seeded stable.
- bit28 HW=45: Hamming-3 closed, radius-6 seeded stable.

This makes the top three Path C records locally stable under the same
two tests.

## Verdict

- bit13 HW=44 is stable under radius-6 seeded anneal at 12 x 200k.
- The current top-three residual panel is bit24 HW=43, bit13 HW=44,
  bit28 HW=45.
- Further Path C progress probably needs a new operator, larger radius,
  or geometry relaxation rather than repeating the same seeded anneal.

## Next

1. Build a focused joint W59/W60 operator around bit13, because F436's
   record used one W59 bit plus three W60 bits.
2. Try geometry relaxation (`c/g` sub-fingerprint variants) to see
   whether the HW floor is fingerprint-bound.
