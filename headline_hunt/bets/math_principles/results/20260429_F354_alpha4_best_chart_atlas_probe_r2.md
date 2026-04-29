---
date: 2026-04-29
bet: math_principles
status: ATLAS_NEIGHBORHOOD_PROBE
---

# F354: atlas-neighborhood probe

## Summary

Verdict: `local_probe_score_improves_only`.
Source: `headline_hunt/bets/math_principles/results/20260429_F352_new88_atlas_alpha4_4x20k.json` selector `best_chart`.
Base score: 43.3 a57=5 D61=17 chart=`dCh,dh`.

| Mode | Radius | Scanned | Score-improved | a57-improved | Chart-improved | Best score | Best a57 | Best chart |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `raw_m2` | 2 | 12880 | 0 | 0 | 0 | 45.55 | 7 | `dCh,dh` |
| `common_xor` | 2 | 12880 | 1 | 0 | 0 | 37.9 | 5 | `dh,dCh` |
| `common_add` | 2 | 51360 | 1 | 0 | 0 | 39.4 | 5 | `dh,dCh` |

## Decision

Local message moves can polish the scalar atlas loss, but the missing ingredient is still a chart-aware proposal.
