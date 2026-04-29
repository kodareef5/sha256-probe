---
date: 2026-04-29
bet: math_principles
status: KERNEL_SAFE_JUNCTION_SEARCH
---

# F373: strict-kernel junction search

## Summary

Verdict: `junction_reduces_target_distance`.
Source: `headline_hunt/bets/math_principles/results/20260429_F372_kernel_safe_beam_probe.json`.
Base: score 37.8 a57=6 D61=8 chart=`dh,dCh`.
Literal union: score 85.25 a57=15 D61=11 chart=`dT2,dh` kernel=True.

| Branch | Target | Evaluated | Hits | Best target score | a57 | D61 | Chart | Violation |
|---|---|---:|---:|---:|---:|---:|---|---|
| `best_guard` | `guard_branch_preserve_guard_repair_D61` | 48071 | 0 | 43.0 | 6 | 13 | `dh,dCh` | `[0, 2, 5]` |
| `best_d61` | `D61_branch_guard_repair_preserve_D61` | 48069 | 0 | 50.25 | 6 | 20 | `dCh,dh` | `[0, 0, 15]` |

## Decision

The repair beams move toward the target constraints but do not close them.
