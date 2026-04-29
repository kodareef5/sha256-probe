---
date: 2026-04-29
bet: math_principles
status: CHAMBER_SEED_FREEVAR_OPT
---

# F358: chamber-seed free-variable optimization

## Summary

Verdict: `freevar_opt_near_chamber_schedule`.
Chamber: `0:0x370fef5f:0x6ced4182:0x9af03606`.
Warmup samples: 8000; hill steps: 100000; restarts: 8.
Warmup best mismatch: 31 bits.
Optimized best mismatch: 24 bits.
Best atlas rec: a57=14 D61=15 chart=`dSig1,dh`.

| Round | Target | Linear | True | Linear HW | True HW |
|---:|---|---|---|---:|---:|
| 57 | `0x370fef5f` | `0x370fef5f` | `0xb20d8f5f` | 0 | 6 |
| 58 | `0x6ced4182` | `0x6ced4182` | `0xabec5289` | 0 | 12 |
| 59 | `0x9af03606` | `0x9af03606` | `0x8bf02717` | 0 | 6 |

## Decision

Run a longer free-variable search and then test atlas-loss continuation from the best seed.
