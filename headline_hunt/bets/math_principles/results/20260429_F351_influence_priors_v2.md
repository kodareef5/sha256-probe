---
date: 2026-04-29
bet: math_principles
status: INFLUENCE_PRIORS
---

# F351: empirical influence priors

## Summary

Positive threshold: score <= 90.
Background records: 2744; positive records: 22.

## Top active words

| Rank | Word | Positive | Background | Lift |
|---:|---:|---:|---:|---:|
| 1 | 3 | 12 | 935 | 1.594706 |
| 2 | 11 | 9 | 767 | 1.47727 |
| 3 | 9 | 8 | 755 | 1.342762 |
| 4 | 6 | 8 | 800 | 1.267279 |
| 5 | 1 | 11 | 1125 | 1.219458 |
| 6 | 15 | 7 | 742 | 1.205534 |
| 7 | 12 | 7 | 743 | 1.203912 |
| 8 | 2 | 12 | 1266 | 1.17793 |
| 9 | 8 | 7 | 763 | 1.172376 |
| 10 | 7 | 6 | 731 | 1.060507 |
| 11 | 4 | 4 | 725 | 0.740269 |
| 12 | 5 | 4 | 735 | 0.730204 |

## Top active-word pairs

| Rank | Pair | Positive | Background | Lift |
|---:|---|---:|---:|---:|
| 1 | `6,11` | 6 | 201 | 3.84993 |
| 2 | `3,8` | 6 | 228 | 3.395015 |
| 3 | `8,9` | 4 | 173 | 3.095477 |
| 4 | `6,12` | 4 | 184 | 2.910923 |
| 5 | `1,3` | 9 | 408 | 2.775531 |
| 6 | `3,15` | 4 | 203 | 2.639141 |
| 7 | `4,15` | 3 | 159 | 2.618918 |
| 8 | `7,9` | 3 | 159 | 2.618918 |
| 9 | `7,15` | 3 | 162 | 2.570569 |
| 10 | `2,15` | 6 | 315 | 2.45883 |
| 11 | `11,12` | 3 | 170 | 2.449955 |
| 12 | `5,11` | 3 | 171 | 2.43567 |
| 13 | `8,12` | 3 | 171 | 2.43567 |
| 14 | `11,15` | 3 | 171 | 2.43567 |
| 15 | `3,9` | 4 | 221 | 2.424674 |
| 16 | `2,11` | 6 | 321 | 2.412942 |

## Decision

`{1,3}` stats: {'feature': [1, 3], 'positive_count': 9, 'background_count': 408, 'positive_frequency': 0.413043, 'background_frequency': 0.148816, 'lift': 2.775531}.
Use `{1,3}` as a candidate sampler axis, but preserve F248 as the explicit outlier control.
