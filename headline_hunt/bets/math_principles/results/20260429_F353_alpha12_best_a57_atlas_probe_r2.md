---
date: 2026-04-29
bet: math_principles
status: ATLAS_NEIGHBORHOOD_PROBE
---

# F353: atlas-neighborhood probe

## Summary

Verdict: `local_probe_no_descent`.
Source: `headline_hunt/bets/math_principles/results/20260429_F352_new88_atlas_alpha12_4x20k.json` selector `best_a57`.
Base score: 75.7 a57=4 D61=14 chart=`dCh,dSig1`.

| Mode | Radius | Scanned | Score-improved | a57-improved | Chart-improved | Best score | Best a57 | Best chart |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `raw_m2` | 2 | 12880 | 0 | 0 | 2384 | 108.25 | 7 | `dh,dCh` |
| `common_xor` | 2 | 12880 | 0 | 0 | 2401 | 108.9 | 6 | `dSig1,dT2` |
| `common_add` | 2 | 51360 | 0 | 0 | 9336 | 75.7 | 4 | `dCh,dSig1` |

## Decision

This basin is locally stiff under the tested message moves; next try schedule-coordinate or two-side structured moves.
