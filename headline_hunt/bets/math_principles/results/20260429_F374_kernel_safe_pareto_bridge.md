---
date: 2026-04-29
bet: math_principles
status: KERNEL_SAFE_PARETO_BRIDGE
---

# F374: strict-kernel Pareto bridge

## Summary

Verdict: `pareto_bridge_keeps_split_front`.
Source: `headline_hunt/bets/math_principles/results/20260429_F372_kernel_safe_beam_probe.json`.
Base excluded from bridge: score 37.8 a57=6 D61=8 chart=`dh,dCh`.
Evaluated: 126486; global front size: 57.

| Anchor | Score | a57 | D61 | Chart | Source | Depth |
|---|---:|---:|---:|---|---|---:|
| `best_score` | 40.8 | 4 | 11 | `dT2,dCh` | `best_guard` | 2 |
| `best_balanced` | 43.0 | 6 | 13 | `dh,dCh` | `best_guard` | 2 |
| `best_guard` | 40.8 | 4 | 11 | `dT2,dCh` | `best_guard` | 2 |
| `best_d61` | 59.1 | 12 | 5 | `dCh,dh` | `best_d61` | 2 |

## Front

- chart histogram: `{'dh,dCh': 15, 'dCh,dh': 12, 'dT2,dCh': 3, 'dh,dSig1': 9, 'dSig1,dT2': 2, 'dCh,dSig1': 2, 'dT2,dSig1': 4, 'dCh,dT2': 2, 'dT2,dh': 3, 'dSig1,dCh': 3, 'dSig1,dh': 2}`
- strict benchmark hits: 0

## Decision

Use the nontrivial front as bridge seeds; the combined strict target is still absent.
