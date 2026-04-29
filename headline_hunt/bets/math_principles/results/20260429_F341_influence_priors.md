---
date: 2026-04-29
bet: math_principles
status: INFLUENCE_PRIORS
---

# F341: empirical influence priors

## Summary

Positive threshold: score <= 90.
Background records: 2688; positive records: 21.

## Top active words

| Rank | Word | Positive | Background | Lift |
|---:|---:|---:|---:|---:|
| 1 | 3 | 12 | 905 | 1.68729 |
| 2 | 11 | 8 | 726 | 1.430051 |
| 3 | 9 | 8 | 736 | 1.410634 |
| 4 | 1 | 11 | 1109 | 1.266889 |
| 5 | 15 | 7 | 724 | 1.265293 |
| 6 | 8 | 7 | 737 | 1.242989 |
| 7 | 6 | 7 | 769 | 1.191299 |
| 8 | 2 | 11 | 1242 | 1.131279 |
| 9 | 7 | 6 | 724 | 1.096587 |
| 10 | 12 | 6 | 726 | 1.093568 |
| 11 | 4 | 4 | 716 | 0.767652 |
| 12 | 5 | 4 | 716 | 0.767652 |

## Top active-word pairs

| Rank | Pair | Positive | Background | Lift |
|---:|---|---:|---:|---:|
| 1 | `6,11` | 5 | 172 | 3.897101 |
| 2 | `3,8` | 6 | 210 | 3.774239 |
| 3 | `8,9` | 4 | 161 | 3.405713 |
| 4 | `1,3` | 9 | 399 | 2.906531 |
| 5 | `3,15` | 4 | 195 | 2.813415 |
| 6 | `4,15` | 3 | 155 | 2.751096 |
| 7 | `5,11` | 3 | 155 | 2.751096 |
| 8 | `7,9` | 3 | 155 | 2.751096 |
| 9 | `11,15` | 3 | 156 | 2.733517 |
| 10 | `7,15` | 3 | 159 | 2.682103 |
| 11 | `8,12` | 3 | 161 | 2.648888 |
| 12 | `3,9` | 4 | 209 | 2.625407 |
| 13 | `3,6` | 4 | 210 | 2.612935 |
| 14 | `2,15` | 6 | 306 | 2.592096 |
| 15 | `6,12` | 3 | 173 | 2.46568 |
| 16 | `6,8` | 3 | 176 | 2.42377 |

## Decision

`{1,3}` stats: {'feature': [1, 3], 'positive_count': 9, 'background_count': 399, 'positive_frequency': 0.431818, 'background_frequency': 0.148568, 'lift': 2.906531}.
Use `{1,3}` as a candidate sampler axis, but preserve F248 as the explicit outlier control.
