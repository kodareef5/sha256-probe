---
date: 2026-04-29
bet: math_principles
status: CHAMBER_SEED_LINEAR_LIFT
---

# F356: chamber-seed no-carry linear lift

## Summary

Verdict: `linear_lift_partial_seed`.
Chamber: `0:0x370fef5f:0x6ced4182:0x9af03606`.
Rank/free columns: 96/416.
Samples: 5000.
Best true W57..W59 mismatch: 30 bits.
Best atlas rec under kernel-pair check: a57=17 D61=18 chart=`dh,dT2`.

| Round | Target | Linear | True | Linear HW | True HW |
|---:|---|---|---|---:|---:|
| 57 | `0x370fef5f` | `0x370fef5f` | `0x5f457457` | 0 | 12 |
| 58 | `0x6ced4182` | `0x6ced4182` | `0xeecfc8c2` | 0 | 8 |
| 59 | `0x9af03606` | `0x9af03606` | `0x98f8059f` | 0 | 10 |

## Decision

The no-carry lift has signal, but it needs carry-aware correction before atlas search.
