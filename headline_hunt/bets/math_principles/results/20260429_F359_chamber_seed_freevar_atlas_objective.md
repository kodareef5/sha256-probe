---
date: 2026-04-29
bet: math_principles
status: CHAMBER_SEED_FREEVAR_OPT
---

# F359: chamber-seed free-variable optimization

## Summary

Verdict: `freevar_opt_improved_partial_seed`.
Chamber: `0:0x370fef5f:0x6ced4182:0x9af03606`.
Warmup samples: 2000; hill steps: 20000; restarts: 4.
Warmup best mismatch: 36 bits.
Optimized best mismatch: 29 bits.
Best atlas rec: a57=17 D61=13 chart=`dCh,dh`.

| Round | Target | Linear | True | Linear HW | True HW |
|---:|---|---|---|---:|---:|
| 57 | `0x370fef5f` | `0x370fef5f` | `0x191c771d` | 0 | 12 |
| 58 | `0x6ced4182` | `0x6ced4182` | `0x3eec4d92` | 0 | 7 |
| 59 | `0x9af03606` | `0x9af03606` | `0xc090a506` | 0 | 10 |

## Decision

The free variables carry real correction signal; continue with larger restarts or add a carry-feature objective.
