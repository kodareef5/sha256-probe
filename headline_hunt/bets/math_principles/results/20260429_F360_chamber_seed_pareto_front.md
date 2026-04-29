---
date: 2026-04-29
bet: math_principles
status: CHAMBER_SEED_PARETO_FRONT
---

# F360: chamber-seed Pareto front

## Summary

Verdict: `pareto_preserved_low_guard_member`.
Front size: 43; evaluations: 84000.
Chamber: `0:0x370fef5f:0x6ced4182:0x9af03606`.

| Representative | Mismatch | Chart | a57 | D61 | Tail |
|---|---:|---|---:|---:|---:|
| `best_mismatch` | 26 | `dT2,dSig1` | 12 | 12 | 126 |
| `best_a57` | 50 | `dh,dCh` | 5 | 14 | 135 |
| `best_chart` | 50 | `dh,dCh` | 5 | 14 | 135 |
| `best_D61` | 53 | `dSig1,dCh` | 11 | 5 | 118 |

## Front Preview

| Rank | Mismatch | Chart | a57 | D61 | msgHW |
|---:|---:|---|---:|---:|---:|
| 1 | 50 | `dh,dCh` | 5 | 14 | 265 |
| 2 | 44 | `dh,dCh` | 6 | 17 | 251 |
| 3 | 41 | `dCh,dh` | 7 | 17 | 268 |
| 4 | 43 | `dh,dCh` | 7 | 16 | 263 |
| 5 | 45 | `dCh,dh` | 7 | 13 | 269 |
| 6 | 48 | `dCh,dh` | 7 | 11 | 249 |
| 7 | 36 | `dCh,dh` | 8 | 17 | 246 |
| 8 | 40 | `dh,dCh` | 8 | 13 | 273 |
| 9 | 34 | `dCh,dh` | 9 | 14 | 254 |
| 10 | 38 | `dh,dCh` | 9 | 10 | 266 |
| 11 | 54 | `dh,dCh` | 9 | 9 | 251 |
| 12 | 41 | `dCh,dh` | 10 | 7 | 249 |
| 13 | 32 | `dCh,dh` | 11 | 20 | 242 |
| 14 | 37 | `dCh,dh` | 11 | 13 | 250 |
| 15 | 37 | `dh,dCh` | 11 | 13 | 282 |
| 16 | 38 | `dh,dCh` | 11 | 9 | 258 |
| 17 | 30 | `dh,dCh` | 12 | 17 | 240 |
| 18 | 31 | `dh,dCh` | 12 | 9 | 271 |
| 19 | 49 | `dCh,dh` | 13 | 6 | 252 |
| 20 | 40 | `dh,dCh` | 17 | 7 | 269 |
| 21 | 28 | `dCh,dh` | 18 | 11 | 251 |
| 22 | 38 | `dh,dCh` | 20 | 6 | 250 |
| 23 | 45 | `dSig1,dCh` | 5 | 20 | 246 |
| 24 | 51 | `dh,dSig1` | 5 | 13 | 254 |

## Decision

Keep low-guard and low-mismatch members separate; scalar weighting should stay demoted.
