---
date: 2026-04-29
bet: math_principles
status: BRIDGE_ANCHOR_NEIGHBORHOOD
---

# F376: bridge-anchor deterministic neighborhood

## Summary

Verdict: `bridge_neighborhood_coordinate_descent_only`.
Source: `headline_hunt/bets/math_principles/results/20260429_F375_kernel_safe_bridge_anchor_continuation.json` label `best_d61` candidate `best_profile`.
Seed: default score 39.1 profile score 69.1 a57=5 D61=13 chart=`dCh,dh`.
Scanned valid moves: 1536; invalid rejected: 0.

| Candidate | Default score | Profile score | a57 | D61 | Chart | Move |
|---|---:|---:|---:|---:|---|---|
| `best_default` | 51.2 | 99.2 | 8 | 13 | `dh,dCh` | `{'mode': 'common_add', 'word': 6, 'bit': 30, 'sign': 1}` |
| `best_profile` | 51.2 | 99.2 | 8 | 13 | `dh,dCh` | `{'mode': 'common_add', 'word': 6, 'bit': 30, 'sign': 1}` |
| `best_guard` | 51.2 | 99.2 | 8 | 13 | `dh,dCh` | `{'mode': 'common_add', 'word': 6, 'bit': 30, 'sign': 1}` |
| `best_d61` | 73.25 | 159.25 | 13 | 7 | `dh,dT2` | `{'mode': 'common_xor', 'word': 6, 'bit': 20}` |
| `best_target` | 51.2 | 99.2 | 8 | 13 | `dh,dCh` | `{'mode': 'common_add', 'word': 6, 'bit': 30, 'sign': 1}` |

## Counts

- default-score improvements: 0
- profile-score improvements: 0
- guard-lowering moves: 0
- D61-lowering moves: 179
- D61-lowering with guard/chart preserved: 0
- strict benchmark hits: 0

## Decision

Coordinates move locally, but not while preserving the repaired guard/chart target.
