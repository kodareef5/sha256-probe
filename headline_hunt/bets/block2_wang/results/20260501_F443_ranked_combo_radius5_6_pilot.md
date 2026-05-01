---
date: 2026-05-01
bet: block2_wang
status: PATH_C_RANKED_COMBO_RADIUS5_6_NEGATIVE
parent: F440/F441/F442 full radius-4 closures
evidence_level: VERIFIED
compute: 3322704 selected forward evaluations; 0 solver runs
author: yale-codex
---

# F443: ranked soft-bit radius-5/6 pilot

## Setup

After F440/F441/F442 closed full W57..W60 radius 4 around the top-three
Path C records, F443 tested a selective nonlocal jump:

1. Rank all 128 one-bit neighbors by residual HW and bridge score.
2. Keep the top 32 soft directions.
3. Exhaustively enumerate Hamming radius 5 and 6 inside those 32 bits.

This is not a closure proof. It is a cheap test of whether the obvious
soft coordinates combine into a deeper nonlocal move.

New tool:

`headline_hunt/bets/block2_wang/encoders/ranked_combo_search.py`

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F443_bit24_hw43_top32_ranked_combo_r5_r6.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F443_bit13_hw44_top32_ranked_combo_r5_r6.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F443_bit28_hw45_top32_ranked_combo_r5_r6.json`

## Result

| Candidate | Init HW | Selected combos | Cascade-1 pass | Bridge pass | HW <= init | Best selected non-seed |
|---|---:|---:|---:|---:|---:|---:|
| bit24_mdc27e18c | 43 | 1,107,568 | 1,107,568 | 1,107,568 | 0 | 48 |
| bit13_m916a56aa | 44 | 1,107,568 | 1,107,568 | 1,107,568 | 0 | 48 |
| bit28_md1acca79 | 45 | 1,107,568 | 1,107,568 | 1,107,568 | 0 | 52 |

The seed remained the best seen in every run:

- bit24: HW=43, score=79.073
- bit13: HW=44, score=71.526
- bit28: HW=45, score=74.146

## Soft-Bit Pattern

The learned top-32 bit sets are heavily W60-dominated:

- bit24: 26/32 selected bits are in W60.
- bit13: 23/32 selected bits are in W60.
- bit28: 25/32 selected bits are in W60.

That is informative but also limiting. It says the local one-bit gradient
mostly points back into the same W60-heavy coordinate system already closed
at radius 4 and probed by prior W60-specific sweeps.

## Verdict

Top-32 soft-bit radius-5/6 combinations do not beat or tie the top-three
Path C records. The negative result is stronger than another random
annealing pass because it specifically tests the locally least-damaging
coordinates.

Next steps should not be "more of the same" unless a new prior is added.
The useful pivots are:

1. Rank by pair or carry-chart deltas instead of one-bit residual HW.
2. Force cross-word diversity, e.g. require W57/W58/W59 participation.
3. Use geometry relaxation to test whether the current floor is tied to the
   bridge fingerprint rather than W-space locality.
