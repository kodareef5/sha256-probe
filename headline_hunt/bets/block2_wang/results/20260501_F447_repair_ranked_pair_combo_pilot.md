---
date: 2026-05-01
bet: block2_wang
status: PATH_C_REPAIR_RANKED_PAIR_COMBO_NEGATIVE
parent: F446 carry-chart pair atlas
evidence_level: VERIFIED
compute: 1018782 selected pair-combo evaluations; 24384 pair-rank evaluations; 0 solver runs
author: yale-codex
---

# F447: repair-ranked pair-combo pilot

## Setup

F446 showed pair moves can repair individual lanes, but compensation damage
dominates. F447 tests whether composing the strongest repair pairs cancels
that compensation:

- extend `pair_combo_search.py` with `--pair-rank repair`.
- enumerate all exact two-bit pairs.
- rank by total lane repair first, then net damage.
- keep top 128 repair pairs.
- enumerate unique 3-pair unions at radius 5..6.

Artifacts:

- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F447_bit24_hw43_top128_repair_pair3.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F447_bit13_hw44_top128_repair_pair3.json`
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260501_F447_bit28_hw45_top128_repair_pair3.json`

## Result

| Candidate | Init HW | Evaluated repair-pair unions | HW <= init | Best selected non-seed |
|---|---:|---:|---:|---:|
| bit24_mdc27e18c | 43 | 339,973 | 0 | 54 |
| bit13_m916a56aa | 44 | 339,927 | 0 | 61 |
| bit28_md1acca79 | 45 | 338,882 | 0 | 58 |

The seed remained best in all three cases.

## Interpretation

Repair-ranked pairs perform worse than HW-ranked pairs:

- F445 HW-ranked best non-seed: bit24 48, bit13 49, bit28 48.
- F447 repair-ranked best non-seed: bit24 54, bit13 61, bit28 58.

That means the strongest lane-repair pairs are not complementary. They
mostly stack the same compensation damage rather than cancel it.

## Verdict

Local pair repair is not enough. The next useful search needs either:

1. a constraint-aware composition objective that explicitly penalizes
   repeated compensation lanes, or
2. a geometry change that alters the c/g lane locks, rather than trying to
   patch them with local W-bit pairs.
