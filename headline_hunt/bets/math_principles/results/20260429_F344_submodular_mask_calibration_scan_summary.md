---
date: 2026-04-29
bet: math_principles
status: SUBMODULAR_SCAN_CALIBRATION
---

# F344: submodular mask calibration scan

## Summary

Verdict: `negative_but_near_control`.
Selector verdict entering scan: `needs_unseen_scan_but_fails_observed_calibration`.
Subsets scanned: 24.
Best scan score: 92 on `2,4,6,11,13` (known_good_control).
Best unseen score: 96 on `3,6,8,11,15` (selector rank 98).

## Ranked Scan Rows

| Rank | Mask | Label | Score | Hist | Delta | msgHW | Selector rank |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | `2,4,6,11,13` | `known_good_control` | 92 | 89 | +3 | 36 | 3222 |
| 2 | `2,4,6,11,15` | `known_good_control` | 94 | 90 | +4 | 66 | 2224 |
| 3 | `0,2,3,8,9` | `known_good_control` | 95 | 89 | +6 | 74 | 551 |
| 4 | `3,6,8,11,15` | `top_unseen_rank_98` | 96 | - | - | 36 | 98 |
| 5 | `0,1,3,8,9` | `known_good_control` | 97 | 87 | +10 | 46 | 537 |
| 6 | `1,2,3,4,15` | `known_good_control` | 97 | 90 | +7 | 78 | 492 |
| 7 | `3,8,9,11,15` | `top_unseen_rank_59` | 98 | - | - | 71 | 59 |
| 8 | `2,5,9,10,11` | `known_good_control` | 98 | 90 | +8 | 82 | 2090 |
| 9 | `3,7,8,9,11` | `top_unseen_rank_86` | 98 | - | - | 82 | 86 |
| 10 | `3,6,9,11,15` | `top_unseen_rank_107` | 99 | - | - | 40 | 107 |
| 11 | `3,6,8,9,11` | `top_unseen_rank_16` | 99 | - | - | 57 | 16 |
| 12 | `3,5,8,9,11` | `top_unseen_rank_103` | 99 | - | - | 85 | 103 |
| 13 | `2,3,11,12,15` | `known_good_control` | 99 | 90 | +9 | 87 | 488 |
| 14 | `3,8,9,11,12` | `top_unseen_rank_91` | 100 | - | - | 56 | 91 |
| 15 | `1,3,6,8,12` | `known_good_control` | 100 | 90 | +10 | 62 | 117 |
| 16 | `1,7,10,11,15` | `known_good_control` | 100 | 88 | +12 | 65 | 2289 |
| 17 | `0,7,9,12,14` | `known_good_control` | 100 | 90 | +10 | 73 | 3827 |
| 18 | `1,3,11,12,15` | `top_unseen_rank_115` | 100 | - | - | 85 | 115 |
| 19 | `0,1,2,7,15` | `known_good_control` | 101 | 90 | +11 | 60 | 981 |
| 20 | `1,3,5,6,11` | `known_good_control` | 101 | 88 | +13 | 62 | 380 |
| 21 | `1,2,3,8,11` | `free_greedy` | 101 | 101 | +0 | 73 | - |
| 22 | `2,6,8,11,12` | `known_good_control` | 102 | 88 | +14 | 37 | 1242 |
| 23 | `2,5,7,9,10` | `known_good_control` | 102 | 90 | +12 | 81 | 3338 |
| 24 | `2,3,7,13,15` | `known_good_control` | 103 | 90 | +13 | 73 | 2139 |

## Decision

This budget does not validate the submodular selector as a search accelerator. Keep the F343 priors as descriptive features, but do not spend broad scan budget on the raw coverage objective without adding outcome-aware calibration.
