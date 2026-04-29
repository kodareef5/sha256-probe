---
date: 2026-04-28
bet: cascade_aux_encoding
status: DEPTH2_CUBE_STATS_100K
---

# F307: targeted depth-2 dW[59] cubes on aux-force sr61 bit25

## Purpose

F306 found no tractable depth-1 split on the aux-force sr61 bit25 proxy, but
it produced a ranked set of high-counter `dW[59]` bits. F307 expands those into
targeted depth-2 cube families and runs them at 100k conflicts with CaDiCaL
stats capture.

Base CNF:

```
headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr61_n32_bit25_m09990bd2_fill80000000.cnf
```

Targeted pairs:

```
3/29, 3/19, 29/31, 1/29, 19/29
```

## Commands

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/schedule_cube_planner.py \
  --cnf headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr61_n32_bit25_m09990bd2_fill80000000.cnf \
  --target dw --round 59 \
  --combos 3:29,3:19,29:31,1:29,19:29 \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F307_auxforce_sr61_bit25_dw59_ranked_pairs_cube_manifest.jsonl

python3 headline_hunt/bets/cascade_aux_encoding/encoders/run_schedule_cubes.py \
  --manifest headline_hunt/bets/cascade_aux_encoding/results/20260428_F307_auxforce_sr61_bit25_dw59_ranked_pairs_cube_manifest.jsonl \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F307_auxforce_sr61_bit25_dw59_ranked_pairs_cadical_100k_stats.jsonl \
  --solver cadical --conflicts 100000 --stats
```

## Result

```
20 cubes
20 UNKNOWN at 100k conflicts
```

Stats summary:

| Metric | Mean | Min | Max |
|---|---:|---:|---:|
| Conflicts | 100000.600 | 100000 | 100002 |
| Decisions | 664795.650 | 605902 | 936107 |
| Propagations | 17813260.850 | 14869660 | 19213056 |
| Restarts | 8216.350 | 7507 | 9135 |
| Learned clauses | 94174.400 | 92910 | 94613 |
| Process seconds | 3.846 | 3.060 | 4.200 |

Highest-decision cubes:

| Cube | Decisions | Propagations | Process seconds |
|---|---:|---:|---:|
| `dwr59b19v1__dwr59b29v0` | 936107 | 14869660 | 3.06 |
| `dwr59b03v0__dwr59b29v1` | 713126 | 19213056 | 3.91 |
| `dwr59b29v1__dwr59b31v0` | 702676 | 19097694 | 3.85 |
| `dwr59b01v0__dwr59b29v1` | 697967 | 18716514 | 3.99 |
| `dwr59b01v1__dwr59b29v1` | 694824 | 18951335 | 3.88 |

Lowest-decision cubes:

| Cube | Decisions | Propagations | Process seconds |
|---|---:|---:|---:|
| `dwr59b03v1__dwr59b19v0` | 605902 | 16971602 | 3.91 |
| `dwr59b01v0__dwr59b29v0` | 611436 | 16971682 | 3.88 |
| `dwr59b03v0__dwr59b19v1` | 616210 | 17312472 | 3.81 |
| `dwr59b03v0__dwr59b19v0` | 625210 | 17474933 | 3.44 |
| `dwr59b19v1__dwr59b29v1` | 626166 | 17397928 | 3.80 |

## Interpretation

Depth-2 targeted cubes still do not produce a SAT/UNSAT split at 100k
conflicts. That agrees with macbook F262/F263: shallow cube-and-conquer is not
enough to crack the F235-class hardness.

However, stats mode exposes a sharper structural outlier:

```
dW[59] bit19 = 1, bit29 = 0
```

This cube has 936k decisions, far above the batch mean of 665k, while having
the lowest propagation count in the high-decision set. It may represent a
different CaDiCaL search trajectory rather than merely more expensive unit
propagation.

## Next move

Do not keep sweeping broad shallow cubes. The next meaningful cube test should
be one of:

1. Timeout-based conquer test on `dwr59b19v1__dwr59b29v0` at 60s/120s.
2. Depth-3 expansion around `19=1,29=0`, adding one of bits `3,1,31,27`.
3. Compare the same cube on `aux_expose_sr61` to see whether force-mode
   constraints are masking or amplifying the search trajectory.
