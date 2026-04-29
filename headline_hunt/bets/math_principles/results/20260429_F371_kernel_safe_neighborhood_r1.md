---
date: 2026-04-29
bet: math_principles
status: KERNEL_SAFE_NEIGHBORHOOD_PROBE
---

# F371: kernel-safe neighborhood probe

## Summary

Verdict: `kernel_probe_no_local_descent`.
Source: `headline_hunt/bets/math_principles/results/20260429_F370_kernel_safe_descendant_continuation.json` label `best_D61`.
Base score: 37.8 a57=6 D61=8 chart=`dh,dCh`.
Scanned valid moves: 1536; invalid rejected: 0.

| Candidate | Score | a57 | D61 | Chart | Move |
|---|---:|---:|---:|---|---|
| `best_score` | 51.65 | 6 | 13 | `dSig1,dT2` | `[{'mode': 'common_add', 'word': 3, 'bit': 14, 'sign': -1}]` |
| `best_guard` | 51.65 | 6 | 13 | `dSig1,dT2` | `[{'mode': 'common_add', 'word': 3, 'bit': 14, 'sign': -1}]` |
| `best_d61` | 73.85 | 13 | 8 | `dT2,dh` | `[{'mode': 'common_xor', 'word': 8, 'bit': 16}]` |

## Counts

- Better than base: 0
- a57-lowering: 0
- D61-lowering: 0

## Decision

No strict-kernel single common move improves score, guard, or D61.
