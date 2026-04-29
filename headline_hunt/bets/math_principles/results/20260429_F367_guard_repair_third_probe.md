---
date: 2026-04-29
bet: math_principles
status: GUARD_REPAIR_THIRD_PROBE
---

# F367: guard-repair third-move probe

## Summary

Verdict: `third_move_lowers_guard_only`.
Source: `headline_hunt/bets/math_principles/results/20260429_F366_d61_repair_pair_probe.json` candidate `best_d61`.
Seed: score 58.3 a57=11 D61=8 chart=`dCh,dh`.
Third moves scanned: 2560.

| Candidate | Score | a57 | D61 | Chart | Move |
|---|---:|---:|---:|---|---|
| `best_score` | 50.55 | 7 | 16 | `dCh,dh` | `[{'mode': 'common_add', 'word': 14, 'bit': 16, 'sign': -1}]` |
| `best_guard` | 51.1 | 6 | 13 | `dSig1,dCh` | `[{'mode': 'common_add', 'word': 4, 'bit': 16, 'sign': 1}]` |
| `best_preserve` | 62.15 | 12 | 8 | `dCh,dh` | `[{'mode': 'common_add', 'word': 2, 'bit': 7, 'sign': -1}]` |

## Counts

- a57-lowering moves: 51
- chart-preserving moves: 458
- D61<=seed moves: 11
- a57-lowering with chart and D61<=seed: 0

## Decision

Guard can move locally, but not yet while preserving the D61/chart pair.
