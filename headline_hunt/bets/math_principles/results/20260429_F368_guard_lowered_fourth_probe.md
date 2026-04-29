---
date: 2026-04-29
bet: math_principles
status: GUARD_REPAIR_THIRD_PROBE
---

# F368: guard-repair next-move probe

## Summary

Verdict: `third_move_no_guard_repair`.
Source: `headline_hunt/bets/math_principles/results/20260429_F367_guard_repair_third_probe.json` candidate `best_guard`.
Seed: score 51.1 a57=6 D61=13 chart=`dSig1,dCh`.
Third moves scanned: 2560.

| Candidate | Score | a57 | D61 | Chart | Move |
|---|---:|---:|---:|---|---|
| `best_score` | 53.5 | 6 | 15 | `dSig1,dT2` | `[{'mode': 'common_add', 'word': 1, 'bit': 25, 'sign': 1}]` |
| `best_guard` | 53.5 | 6 | 15 | `dSig1,dT2` | `[{'mode': 'common_add', 'word': 1, 'bit': 25, 'sign': 1}]` |
| `best_preserve` | 58.3 | 11 | 8 | `dCh,dh` | `[{'mode': 'common_add', 'word': 4, 'bit': 16, 'sign': -1}]` |

## Counts

- a57-lowering moves: 0
- chart-preserving moves: 460
- D61<=seed moves: 509
- a57-lowering with chart and D61<=seed: 0
- target a57/chart/D61 moves: 0

## Decision

The F366 D61/chart repaired pair has no one-move guard repair in this neighborhood.
