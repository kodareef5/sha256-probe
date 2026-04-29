---
date: 2026-04-29
bet: math_principles
status: RADIUS1_NEW88_CONTINUATION
---

# F350: radius-one score-88 continuation

## Summary

Verdict: `narrow_reproducible_score88_no_descent`.
Discovery mask: `2,6,11,12,13`.

| Run | Restarts | Iterations | Kicks | Polish | Best | msgHW | Words |
|---|---:|---:|---:|---|---:|---:|---:|
| `kicked_8x50k` | 8 | 50000 | 2 | False | 94 | 66 | 5 |
| `seeded_8x50k` | 8 | 50000 | 0 | False | 88 | 77 | 5 |
| `polish` | 1 | 1 | 0 | True | 88 | 77 | 5 |

## Decision

The score-88 mask is real but narrow. No-kick seeding preserves it; kicked continuation loses it; single-bit polish finds no immediate descent. Promote it as a basin seed and rebuild the shared manifest before using it in later priors.
