---
date: 2026-04-29
bet: math_principles
status: STRICT_KERNEL_BASIN_COMPARISON
---

# F377: strict-kernel basin comparison

## Summary

Verdict: `strict_kernel_basins_split_with_bridges`.
The strict-kernel front has distinct basins and coordinate bridges, but no combined chamber-attractor hit.

| Basin | Label | Source | Score | Profile | a57 | D61 | Chart | Note |
|---|---|---|---:|---:|---:|---:|---|---|
| `chamber_seed` | `F374_low_guard` | `F374` | 40.8 |  | 4 | 11 | `dT2,dCh` | nontrivial a57=4 corner |
| `bridge` | `F375_D61_to_guard` | `F375` | 39.1 |  | 5 | 13 | `dCh,dh` | D61-side bridge repairs guard but loses D61=5 |
| `random_init` | `F322_seed_F336` | `F336` | 39.65 |  | 5 | 14 | `dh,dCh` | depth-1 local minimum |
| `chamber_seed` | `F372_best_score` | `F372` | 37.8 |  | 6 | 8 | `dh,dCh` | best strict scalar score |
| `chamber_seed` | `F374_balanced` | `F374` | 43.0 |  | 6 | 13 | `dh,dCh` | chart bridge anchor |
| `chamber_seed` | `F374_low_D61` | `F374` | 59.1 |  | 12 | 5 | `dCh,dh` | Pareto D61=5 anchor |
| `chamber_seed` | `F372_best_D61` | `F372` | 71.45 |  | 15 | 5 | `dCh,dh` | strict D61=5 corner |

## Local Checks

| Probe | Base | Moves | Score improves | Guard improves | D61 improves | Target repairs | Strict hits |
|---|---|---:|---:|---:|---:|---:|---:|
| `F336_depth1_from_F322` | a57=5 D61=14 chart=dh,dCh | 1536 | 0 | 0 | 302 | 0 | 0 |
| `F376_depth1_from_F375_bridge` | a57=5 D61=13 chart=dCh,dh | 1536 | 0 | 0 | 179 | 0 | 0 |

## Conclusion

The current strict-kernel evidence is not a single basin slowly approaching the chamber attractor. It is a split Pareto front: random-init holds the low-a57 chamber-chart corner, the chamber-seed path holds the D61=5 corner and an off-chart a57=4 corner, and F375 proves one bridge direction exists only by trading D61 back away.
