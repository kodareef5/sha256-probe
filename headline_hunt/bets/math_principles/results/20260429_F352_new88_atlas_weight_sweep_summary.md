---
date: 2026-04-29
bet: math_principles
status: ATLAS_WEIGHT_SWEEP
---

# F352: new score-88 mask atlas-loss weight sweep

## Summary

Verdict: `a57_improves_but_chart_not_locked`.
Active words: `2,6,11,12,13`.

| Alpha | Best score | Best a57 | Best a57 chart | Best chart-match a57 | Best chart-match D61 |
|---:|---:|---:|---|---:|---:|
| 4.0 | 43.3 | 5 | `dCh,dh` | 5 | 17 |
| 8.0 | 63.85 | 5 | `dCh,dh` | 5 | 17 |
| 12.0 | 75.7 | 4 | `dCh,dSig1` | 6 | 17 |
| 16.0 | 109.45 | 5 | `dSig1,dh` | 6 | 17 |

## Decision

Raising the `a57_xor` weight alone is not enough to lock the score-88 mask into the `(dh,dCh)` chamber. Keep the mask as a useful basin seed, but treat chart membership as a coordinate that needs its own proposal operator rather than a scalar penalty.
