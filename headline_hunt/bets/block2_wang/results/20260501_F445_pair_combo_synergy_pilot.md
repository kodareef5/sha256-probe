---
date: 2026-05-01
bet: block2_wang
status: PATH_C_PAIR_COMBO_SYNERGY_NEGATIVE
parent: F443/F444 ranked combo pilots
evidence_level: VERIFIED
compute: 697335 selected pair-combo evaluations; 24384 pair-rank evaluations; 0 solver runs
author: yale-codex
---

# F445: pair-delta combo synergy pilot

## Setup

F443 ranked by one-bit softness and F444 forced cross-word diversity. F445
changes the primitive from one-bit moves to exact two-bit deltas:

1. Enumerate all 8,128 two-bit moves over W57..W60.
2. Rank pairs by residual HW and bridge score.
3. Keep the top 128 pairs.
4. Enumerate unique 3-pair unions with radius 5..6.

New tool:

`headline_hunt/bets/block2_wang/encoders/pair_combo_search.py`

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F445_bit24_hw43_top128_pair3.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F445_bit13_hw44_top128_pair3.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F445_bit28_hw45_top128_pair3.json`

## Result

| Candidate | Init HW | Pair bridge pass | Unique pair-combos | HW <= init | Best selected non-seed |
|---|---:|---:|---:|---:|---:|
| bit24_mdc27e18c | 43 | 8,128 / 8,128 | 199,483 | 0 | 48 |
| bit13_m916a56aa | 44 | 8,003 / 8,128 | 267,377 | 0 | 49 |
| bit28_md1acca79 | 45 | 8,125 / 8,128 | 230,475 | 0 | 48 |

The seed remained best in all three cases.

## Notes

Pair ranking still mostly selects W60-heavy structure:

- bit24 top pair: `W60.28 + W60.29` gives HW=49.
- bit13 top pair: `W59.31 + W60.25` gives HW=58.
- bit28 top pair: `W60.18 + W60.30` gives HW=52.

The best 3-pair unions are close enough to be informative but not close
enough to threaten the records:

- bit24 best selected non-seed: HW=48.
- bit13 best selected non-seed: HW=49.
- bit28 best selected non-seed: HW=48.

## Verdict

Pair-delta synergy does not produce a top-three Path C improvement at this
budget. Together with F443/F444, this says local ranking over raw W bits is
not enough, even when the ranking primitive is upgraded from single bits to
pairs.

Next useful work should inspect the carry-chart deltas directly and rank
operators by which register lanes they repair, not just by final HW.
