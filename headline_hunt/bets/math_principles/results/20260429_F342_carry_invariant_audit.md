---
date: 2026-04-29
bet: math_principles
status: CARRY_INVARIANT_AUDIT
---

# F342: carry / hard-core invariant audit

## Summary

- sr60: `holds_exact` (128/128 last-two bits stable core)
- sr61: `holds_with_single_exception` (127/128 last-two bits stable core)

## Mode summaries

### sr60

| Word round | Stable core | Stable shell | Variable | Mean core fraction |
|---|---:|---:|---:|---:|
| w1[57] | 1 | 1 | 30 | 0.401042 |
| w1[58] | 0 | 32 | 0 | 0.0 |
| w1[59] | 32 | 0 | 0 | 1.0 |
| w1[60] | 32 | 0 | 0 | 1.0 |
| w2[57] | 2 | 4 | 26 | 0.447917 |
| w2[58] | 8 | 1 | 23 | 0.75 |
| w2[59] | 32 | 0 | 0 | 1.0 |
| w2[60] | 32 | 0 | 0 | 1.0 |

### sr61

| Word round | Stable core | Stable shell | Variable | Mean core fraction |
|---|---:|---:|---:|---:|
| w1[57] | 1 | 3 | 28 | 0.414062 |
| w1[58] | 31 | 0 | 1 | 0.984375 |
| w1[59] | 32 | 0 | 0 | 1.0 |
| w2[57] | 1 | 5 | 26 | 0.40625 |
| w2[58] | 32 | 0 | 0 | 1.0 |
| w2[59] | 32 | 0 | 0 | 1.0 |

## Decision

Promote the last-two-free-round rule as a structural coordinate for selector/BP work. Keep first-free-round behavior candidate-specific.
