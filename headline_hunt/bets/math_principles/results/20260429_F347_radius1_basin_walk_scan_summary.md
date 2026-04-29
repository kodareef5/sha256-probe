---
date: 2026-04-29
bet: math_principles
status: RADIUS1_BASIN_WALK_SCAN
---

# F347: radius-one basin-walk scan

## Summary

Verdict: `radius1_unseen_basin_hit`.
Subsets scanned: 32.
Low hits: 1; unseen low hits: 1.
Best score: 88 on `2,6,11,12,13` (unseen_radius1).
Best unseen: 88 on `2,6,11,12,13`, parent 2,6,8,11,12.

## Ranked Rows

| Rank | Mask | Label | Score | Hist | Delta | Parent best | msgHW |
|---:|---|---|---:|---:|---:|---:|---:|
| 1 | `2,6,11,12,13` | `unseen_radius1` | 88 | - | - | 88 | 77 |
| 2 | `1,4,5,6,11` | `unseen_radius1` | 91 | - | - | 88 | 82 |
| 3 | `3,5,6,9,11` | `unseen_radius1` | 93 | - | - | 88 | 76 |
| 4 | `2,4,6,11,15` | `known_bridge_control` | 94 | 90 | +4 | 89 | 53 |
| 5 | `0,1,5,8,9` | `known_bridge_control` | 94 | 93 | +1 | 87 | 72 |
| 6 | `2,4,6,11,13` | `known_bridge_control` | 95 | 89 | +6 | 90 | 43 |
| 7 | `3,6,8,11,12` | `unseen_radius1` | 95 | - | - | 88 | 79 |
| 8 | `6,8,9,11,12` | `unseen_radius1` | 95 | - | - | 88 | 79 |
| 9 | `2,5,9,10,11` | `known_bridge_control` | 95 | 90 | +5 | 90 | 81 |
| 10 | `6,8,11,12,15` | `unseen_radius1` | 96 | - | - | 88 | 28 |
| 11 | `0,1,2,3,8` | `known_bridge_control` | 96 | 94 | +2 | 87 | 57 |
| 12 | `1,5,6,11,15` | `unseen_radius1` | 96 | - | - | 88 | 76 |
| 13 | `0,1,3,8,9` | `known_bridge_control` | 96 | 87 | +9 | 89 | 80 |
| 14 | `2,3,6,8,9` | `known_bridge_control` | 96 | 91 | +5 | 89 | 80 |
| 15 | `2,3,5,6,11` | `known_bridge_control` | 96 | 94 | +2 | 88 | 87 |
| 16 | `3,5,6,11,12` | `unseen_radius1` | 96 | - | - | 88 | 87 |
| 17 | `3,4,5,6,11` | `unseen_radius1` | 97 | - | - | 88 | 58 |
| 18 | `3,5,6,8,11` | `unseen_radius1` | 97 | - | - | 88 | 67 |
| 19 | `2,8,11,12,15` | `unseen_radius1` | 97 | - | - | 88 | 79 |
| 20 | `5,6,8,11,12` | `unseen_radius1` | 97 | - | - | 88 | 82 |
| 21 | `2,5,7,9,10` | `known_bridge_control` | 97 | 90 | +7 | 90 | 87 |
| 22 | `2,3,8,11,12` | `known_bridge_control` | 97 | 95 | +2 | 88 | 89 |
| 23 | `2,6,11,13,15` | `unseen_radius1` | 98 | - | - | 89 | 18 |
| 24 | `1,5,6,8,11` | `unseen_radius1` | 98 | - | - | 88 | 45 |
| 25 | `3,5,6,11,15` | `unseen_radius1` | 98 | - | - | 88 | 77 |
| 26 | `2,6,11,12,15` | `unseen_radius1` | 98 | - | - | 88 | 79 |
| 27 | `4,6,8,11,12` | `unseen_radius1` | 98 | - | - | 88 | 83 |
| 28 | `4,6,11,13,15` | `unseen_radius1` | 98 | - | - | 89 | 85 |
| 29 | `1,5,6,11,12` | `unseen_radius1` | 99 | - | - | 88 | 71 |
| 30 | `3,5,6,10,11` | `unseen_radius1` | 99 | - | - | 88 | 81 |
| 31 | `0,1,3,8,10` | `known_bridge_control` | 100 | 92 | +8 | 87 | 68 |
| 32 | `0,2,3,8,9` | `known_bridge_control` | 100 | 89 | +11 | 87 | 79 |

## Decision

Promote the unseen score-88 mask to a focused continuation. The radius-one queue is a better next operator than the raw F343 submodular objective.
