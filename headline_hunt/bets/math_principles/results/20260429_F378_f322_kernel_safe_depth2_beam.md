---
date: 2026-04-29
bet: math_principles
status: F322_KERNEL_SAFE_DEPTH2_BEAM
---

# F378: F322 strict-kernel depth-2 beam

## Summary

Verdict: `f322_depth2_beam_coordinate_descent_only`.
Source: `headline_hunt/bets/block2_wang/results/search_artifacts/20260429_F336_kernel_safe_depth1_from_F322.json`.
Base: score 39.65 a57=5 D61=14 chart=`dh,dCh`.
Evaluated: 63248; invalid rejected: 0; target D61=8.

| Candidate | Score | a57 | D61 | Chart | Depth |
|---|---:|---:|---:|---|---:|
| `best_score` | 43.7 | 6 | 13 | `dh,dCh` | 2 |
| `best_target` | 43.7 | 6 | 13 | `dh,dCh` | 2 |
| `best_guard` | 48.8 | 5 | 14 | `dSig1,dh` | 2 |
| `best_d61` | 86.1 | 19 | 4 | `dCh,dh` | 2 |

## Counts

- score improvements: 0
- guard-lowering candidates: 0
- D61-lowering candidates: 11994
- chart/guard-preserving D61 target hits: 0

## Decision

Depth-2 beam moves coordinates but does not combine them into the target.
