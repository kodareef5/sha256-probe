---
date: 2026-04-30
bet: programmatic_sat_propagator
status: DECISION_PRIORITY_SPECS
---

# F397: decision-priority specs

## Summary

Source: `headline_hunt/bets/cascade_aux_encoding/results/20260428_F332_sr60_6cand_hard_core_stability.json`.
Candidates: 6.
Completeness: `{'f286_132_conservative': True, 'f332_139_stable6': True}`.

## Priority Sets

| Set | Requested vars |
|---|---:|
| `f286_132_conservative` | 132 |
| `f332_139_stable6` | 139 |

## Candidate Var Counts

| Candidate | F286 132 | F332 139 |
|---|---:|---:|
| `bit10_m3304caa0_fill80000000` | 132 | 139 |
| `bit11_m45b0a5f6_fill00000000` | 132 | 139 |
| `bit13_m4d9f691c_fill55555555` | 132 | 139 |
| `bit0_m8299b36f_fill80000000` | 132 | 139 |
| `bit17_m427c281d_fill80000000` | 132 | 139 |
| `bit18_m347b0144_fill00000000` | 132 | 139 |

## Use

- Feed `priority_sets.f286_132_conservative.vars` to a `cb_decide` hook first.
- Use `f332_139_stable6` as the broader comparison arm; it includes n=6-stable extras beyond F286.
- Run baseline / existing propagator / F286-priority / F332-priority under the same conflict or time cap.
