---
date: 2026-05-01
bet: block2_wang
status: PATH_C_CROSSWORD_RANKED_RADIUS5_NEGATIVE
parent: F443 ranked combo radius-5/6 pilot
evidence_level: VERIFIED
compute: 13050552 selected forward evaluations; 0 solver runs
author: yale-codex
---

# F444: cross-word ranked radius-5 pilot

## Setup

F443 showed that one-bit soft directions are mostly W60-dominated. F444
modifies the ranked-combo operator to force cross-word diversity:

- rank one-bit W57..W60 directions as before.
- keep top 64 soft bits.
- enumerate radius-5 combinations only if they touch at least 3 W slots.
- reject combinations with more than 3 bits in any one W slot.

Tool update:

`headline_hunt/bets/block2_wang/encoders/ranked_combo_search.py`

New options:

- `--min-distinct-slots`
- `--max-per-slot`

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F444_bit24_hw43_top64_crossword_r5.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F444_bit13_hw44_top64_crossword_r5.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F444_bit28_hw45_top64_crossword_r5.json`

## Result

| Candidate | Init HW | Evaluated | Skipped by slot filter | HW <= init | Best selected non-seed |
|---|---:|---:|---:|---:|---:|
| bit24_mdc27e18c | 43 | 3,874,188 | 3,750,324 | 0 | 57 |
| bit13_m916a56aa | 44 | 4,093,698 | 3,530,814 | 0 | 56 |
| bit28_md1acca79 | 45 | 5,082,720 | 2,541,792 | 0 | 50 |

The seed remained best in all three cases.

## Notes

Forcing cross-word diversity makes the selected moves much less locally
gentle than the W60-heavy top-32 pilot:

- bit24 worsens sharply: best selected non-seed HW=57.
- bit13 worsens sharply: best selected non-seed HW=56.
- bit28 is less hostile: best selected non-seed HW=50, still above the
  HW=45 seed but closer than the other two records.

This suggests bit28 may have more cross-word slack than bit24/bit13, but
the slack is not enough under this simple ranking.

## Verdict

Cross-word top-64 radius-5 combinations do not beat or tie the top-three
Path C records. The raw local W-coordinate picture is now heavily boxed in:

- exact full radius-4 closure for bit24, bit13, bit28.
- W60-heavy ranked radius-5/6 negative.
- forced cross-word ranked radius-5 negative.

The next useful operator should use a different score for ranking, probably
pair/carry-chart deltas, rather than ranking by one-bit residual HW alone.
