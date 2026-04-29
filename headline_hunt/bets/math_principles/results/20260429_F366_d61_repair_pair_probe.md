---
date: 2026-04-29
bet: math_principles
status: D61_REPAIR_PAIR_PROBE
---

# F366: D61-lowering repair pair probe

## Summary

Verdict: `repair_pair_chart_repairs_with_d61_preserved`.
Base: score 35.4 a57=5 D61=9 chart=`dh,dCh`.
Fixed D61 move: score 66.85 a57=11 D61=8 chart=`dT2,dCh`.
Repair moves scanned: 2559.

| Candidate | Score | a57 | D61 | Chart | Move |
|---|---:|---:|---:|---|---|
| `best_score` | 51.95 | 8 | 14 | `dh,dCh` | `[{'mode': 'raw_m2', 'word': 5, 'bit': 21}, {'mode': 'common_xor', 'word': 4, 'bit': 31}]` |
| `best_repair` | 51.95 | 8 | 14 | `dh,dCh` | `[{'mode': 'raw_m2', 'word': 5, 'bit': 21}, {'mode': 'common_xor', 'word': 4, 'bit': 31}]` |
| `best_d61` | 58.3 | 11 | 8 | `dCh,dh` | `[{'mode': 'raw_m2', 'word': 5, 'bit': 21}, {'mode': 'common_xor', 'word': 9, 'bit': 31}]` |

## Counts

- Better than fixed D61 move: 35
- Better than original base: 0
- Chart repaired: 456
- D61 preserved at <= fixed: 9

## Decision

Use the repaired D61-preserving pair as a new front member, even though scalar score is worse.
