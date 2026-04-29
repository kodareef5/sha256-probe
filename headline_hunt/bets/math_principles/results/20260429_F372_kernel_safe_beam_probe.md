---
date: 2026-04-29
bet: math_principles
status: KERNEL_SAFE_BEAM_PROBE
---

# F372: kernel-safe beam probe

## Summary

Verdict: `kernel_beam_found_split_guard_D61_descent`.
Source: `headline_hunt/bets/math_principles/results/20260429_F370_kernel_safe_descendant_continuation.json` label `best_D61`.
Base score: 37.8 a57=6 D61=8 chart=`dh,dCh`.
Evaluated: 64718; invalid rejected: 0.

| Candidate | Score | a57 | D61 | Chart | Depth |
|---|---:|---:|---:|---|---:|
| `best_score` | 37.8 | 6 | 8 | `dh,dCh` | 0 |
| `best_guard` | 51.8 | 4 | 22 | `dSig1,dT2` | 2 |
| `best_d61` | 71.45 | 15 | 5 | `dCh,dh` | 2 |

## Depth Summary

| Depth | Generated | Invalid | Beam best score | Beam best a57 | Beam best D61 |
|---:|---:|---:|---:|---:|---:|
| 1 | 1008 | 0 | 51.65 | 6 | 13 |
| 2 | 31631 | 0 | 47.25 | 7 | 13 |
| 3 | 32079 | 0 | 48.3 | 8 | 10 |

## Decision

Guard and D61 both move under strict kernel, but on separate higher-score branches.
