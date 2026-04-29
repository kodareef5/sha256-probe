---
date: 2026-04-29
bet: math_principles
status: CHAMBER_SEED_FREEVAR_OPT
---

# F357: chamber-seed free-variable optimization

## Summary

Verdict: `freevar_opt_improved_partial_seed`.
Chamber: `0:0x370fef5f:0x6ced4182:0x9af03606`.
Warmup samples: 5000; hill steps: 50000; restarts: 4.
Warmup best mismatch: 30 bits.
Optimized best mismatch: 25 bits.
Best atlas rec: a57=9 D61=11 chart=`dh,dT2`.

| Round | Target | Linear | True | Linear HW | True HW |
|---:|---|---|---|---:|---:|
| 57 | `0x370fef5f` | `0x370fef5f` | `0x772affcf` | 0 | 7 |
| 58 | `0x6ced4182` | `0x6ced4182` | `0x142c5002` | 0 | 10 |
| 59 | `0x9af03606` | `0x9af03606` | `0x0aa09246` | 0 | 8 |

## Decision

The free variables carry real correction signal; continue with larger restarts or add a carry-feature objective.
