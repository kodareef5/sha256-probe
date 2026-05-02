---
date: 2026-05-02
bet: block2_wang
status: ABSORBER_PROFILE_TABLE
parent: F512 absorber matrix, F513-F515 pair-beam follow-up
evidence_level: VERIFIED
author: yale-codex
---

# F516: absorber profile table

## Question

F512 ranked residuals by scalar absorber HW. F513/F515 showed that scalar
absorber ranking does not directly translate into block-1 pair-beam record
improvement. F516 asks a more two-block-native question:

Which residuals preserve, clear, or introduce state-difference bits under the
absorber probe, especially at later rounds?

## Tooling

Added:

- `headline_hunt/bets/block2_wang/encoders/analyze_absorber_profiles.py`
- `headline_hunt/bets/block2_wang/encoders/select_absorber_followups.py`

It joins the F512 residual JSONL with the absorber CSV matrix and computes:

- per-lane input HW from block-1 `diff63`
- per-lane final absorber HW
- original residual bits still overlapping final state
- original residual bits cleared
- new final-state bits introduced
- c/g final HW proxy
- late-round best rows

Artifacts:

- `search_artifacts/20260502_absorber_matrix_overnight/F516_f491_absorber_profile_summary.json`
- `search_artifacts/20260502_absorber_matrix_overnight/F516_f491_absorber_profile_summary.md`
- `search_artifacts/20260502_absorber_matrix_overnight/F517_absorber_followup_selector.json`
- `search_artifacts/20260502_absorber_matrix_overnight/F517_absorber_followup_selector.md`
- `search_artifacts/20260502_absorber_matrix_overnight/F518_absorber_m2_late_round_seeds.jsonl`
- `search_artifacts/20260502_absorber_matrix_overnight/F518_absorber_m2_late_round_seeds.md`

## Ranking Shift

When ranked by late-round quality first, the shortlist changes:

| Rank | Block-1 HW | Best HW | Late Best | Max Cleared | Mean New | Min c/g HW |
|---:|---:|---:|---:|---:|---:|---:|
| 36 | 42 | 75 | 91 | 31 | 80.062 | 22 |
| 21 | 41 | 71 | 93 | 37 | 78.062 | 21 |
| 14 | 41 | 81 | 93 | 35 | 79.875 | 16 |
| 22 | 41 | 79 | 94 | 37 | 81.062 | 21 |
| 8 | 40 | 80 | 94 | 33 | 79.938 | 21 |
| 38 | 43 | 83 | 94 | 33 | 78.250 | 21 |
| 4 | 38 | 74 | 95 | 34 | 79.562 | 17 |
| 32 | 42 | 79 | 95 | 34 | 78.375 | 21 |
| 11 | 40 | 72 | 96 | 35 | 78.250 | 19 |
| 20 | 41 | 73 | 96 | 34 | 78.812 | 17 |

This differs from the F512 scalar-min list, where ranks 34 and 15 led.
Profile ranking promotes rank 36 because it has the best 24-round result
and promotes ranks 14/22 because their late-round absorber behavior is
better than their short-round scalar minima suggest.

## Round Winners

| Rounds | Best rank | Best HW | Cleared | New | c/g HW |
|---:|---:|---:|---:|---:|---:|
| 12 | 20 | 73 | 34 | 66 | 20 |
| 16 | 34 | 69 | 32 | 59 | 21 |
| 20 | 21 | 93 | 26 | 78 | 28 |
| 24 | 36 | 91 | 28 | 77 | 25 |

## Interpretation

The absorber view is not one scalar objective. There are at least three
different selectors:

1. **short-round collapse**: ranks 20/28/34/15
2. **late-round survival**: ranks 36/21/14/22/8/38
3. **low c/g final profile**: ranks 14/20/28/33/4

The old pair-beam operator tested ranks 34/21/20 and did not improve the
HW35 floor. That suggests the next useful search should use the absorber's
second-block `M2` masks or final-state lane profile directly, not just the
block-1 W57..W60 seed.

## Verdict

Use F516 as the selector for the next two-block-native experiment:

- control: HW35 rank 1
- late-round absorber: ranks 36, 21, 14, 22
- c/g-profile control: ranks 14, 20, 28, 33
- known reconnect control: rank 4

Do not spend primary compute on more scalar F491 pair-beam continuation until
there is a new operator that consumes the absorber profile.

## F517 Follow-Up Selector

F517 joins the F516 profile ranking with known pair-beam coverage so future
runs avoid known reruns. Current untested suggested order:

1. rank 22, late_best=94, c/g min=21
2. rank 38, late_best=94, c/g min=21
3. rank 32, late_best=95, c/g min=21
4. rank 33, late_best=96, c/g min=15
5. rank 39, late_best=96, c/g min=19
6. rank 16, late_best=96, c/g min=20
7. rank 25, late_best=97, c/g min=21
8. rank 43, late_best=97, c/g min=22
9. rank 23, late_best=97, c/g min=20
10. rank 41, late_best=98, c/g min=21

These are not recommendations to run the old pair-beam unchanged. They are
the candidates to feed into the next operator that uses absorber `M2` masks
and final-state lane profiles directly.

## F518 M2 Seed Bundle

Added `extract_absorber_m2_seeds.py` and extracted late-round seeds for:

- controls: ranks 1, 4, 20, 21, 36
- profile candidates: ranks 14, 22, 32, 33, 38, 39

The bundle has 22 rows, one per selected rank and round for rounds 20/24.
Each row includes:

- block-1 W57..W60 residual seed
- absorber `M2[0..15]`
- absorber final state diff
- lane deltas, cleared/new/overlap counts
- c/g profile fields

This is the handoff format for the next operator.
