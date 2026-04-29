---
date: 2026-04-29
bet: math_principles
status: KERNEL_SAFE_BRIDGE_ANCHOR_CONTINUATION
---

# F375: strict-kernel bridge-anchor continuation

## Summary

Verdict: `bridge_anchor_continuation_improves_profile`.
Source: `headline_hunt/bets/math_principles/results/20260429_F374_kernel_safe_pareto_bridge.json`.
Strict benchmark hits: 0.

| Label | Profile | Seed score | Seed a57 | Seed D61 | Best score | Best a57 | Best D61 | Best chart | Invalid |
|---|---|---:|---:|---:|---:|---:|---:|---|---:|
| `best_score` | `repair_low_guard_chart_D61` | 74.8 | 4 | 11 | 74.8 | 4 | 11 | `dT2,dCh` | 0 |
| `best_balanced` | `balanced_chart_D61_pressure` | 81.0 | 6 | 13 | 81.0 | 6 | 13 | `dh,dCh` | 0 |
| `best_d61` | `repair_low_D61_guard` | 131.1 | 12 | 5 | 69.1 | 5 | 13 | `dCh,dh` | 0 |

## Coordinate Bests

| Label | Best guard | Best D61 | Best chart candidate |
|---|---|---|---|
| `best_score` | a57=4 D61=11 chart=`dT2,dCh` | a57=11 D61=5 chart=`dT2,dh` | score=78.55 a57=6 D61=16 chart=`dCh,dh` |
| `best_balanced` | a57=5 D61=14 chart=`dCh,dT2` | a57=20 D61=5 chart=`dh,dSig1` | score=81.0 a57=6 D61=13 chart=`dh,dCh` |
| `best_d61` | a57=4 D61=16 chart=`dSig1,dh` | a57=12 D61=5 chart=`dCh,dh` | score=69.1 a57=5 D61=13 chart=`dCh,dh` |

## Decision

Continue the improved target-weighted anchor with deterministic neighborhood checks.
