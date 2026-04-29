---
date: 2026-04-29
bet: math_principles
status: CLUSTER_ATLAS
---

# F345: active-mask cluster atlas

## Summary

Verdict: `low_scores_have_direct_clusters`.
Observed masks: 2624.
Low threshold: 90; bridge threshold: 95; edge distance: 2.

## Threshold Graphs

| Threshold | Nodes | Edges | Components | Largest |
|---:|---:|---:|---:|---:|
| 90 | 15 | 3 | 12 | 2 |
| 92 | 49 | 25 | 27 | 12 |
| 95 | 252 | 539 | 5 | 248 |

## Low-Score Radius Stats

| Mask | Score | Neighbors | Best neighbor | <=90 | <=92 | <=95 |
|---|---:|---:|---:|---:|---:|---:|
| `0,1,3,8,9` | 87 | 55 | 89 | 1 | 2 | 4 |
| `1,3,5,6,11` | 88 | 37 | 94 | 0 | 0 | 6 |
| `1,7,10,11,15` | 88 | 35 | 95 | 0 | 0 | 2 |
| `2,6,8,11,12` | 88 | 37 | 95 | 0 | 0 | 1 |
| `0,2,3,8,9` | 89 | 55 | 87 | 1 | 4 | 10 |
| `2,4,6,11,13` | 89 | 42 | 90 | 1 | 2 | 6 |
| `0,1,2,7,15` | 90 | 55 | 92 | 0 | 1 | 8 |
| `0,7,9,12,14` | 90 | 45 | 91 | 0 | 1 | 2 |
| `1,2,3,4,15` | 90 | 55 | 95 | 0 | 0 | 1 |
| `1,3,6,8,12` | 90 | 43 | 96 | 0 | 0 | 0 |
| `2,3,11,12,15` | 90 | 38 | 94 | 0 | 0 | 2 |
| `2,3,7,13,15` | 90 | 40 | 93 | 0 | 0 | 5 |
| `2,4,6,11,15` | 90 | 42 | 89 | 1 | 2 | 4 |
| `2,5,7,9,10` | 90 | 39 | 90 | 1 | 2 | 6 |
| `2,5,9,10,11` | 90 | 39 | 90 | 1 | 1 | 7 |

## Bridge Components

- Component 1: size=248 best=87 best_masks=['0,1,3,8,9'] top_pairs=[('0,2', 52), ('0,8', 45), ('2,4', 44), ('0,10', 41)]
- Component 2: size=1 best=94 best_masks=['0,1,12,13,14'] top_pairs=[('0,1', 1), ('0,12', 1), ('0,13', 1), ('0,14', 1)]
- Component 3: size=1 best=90 best_masks=['1,3,6,8,12'] top_pairs=[('1,3', 1), ('1,6', 1), ('1,8', 1), ('1,12', 1)]
- Component 4: size=1 best=94 best_masks=['1,6,10,11,12'] top_pairs=[('1,6', 1), ('1,10', 1), ('1,11', 1), ('1,12', 1)]
- Component 5: size=1 best=94 best_masks=['2,5,6,8,15'] top_pairs=[('2,5', 1), ('2,6', 1), ('2,8', 1), ('2,15', 1)]

## Decision

Treat the best masks as basin seeds with near-score bridge neighborhoods, not as a single connected critical component. The next operator should walk radius-one neighborhoods around the known controls and track whether <=95 bridges reproduce before expanding.
