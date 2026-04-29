---
date: 2026-04-28
bet: cascade_aux_encoding
status: DEPTH3_OUTLIER_EXPANSION_NO_SPLIT
---

# F309: depth-3 expansion around F308 outlier

## Purpose

F308 showed that the F307 outlier cube
`dwr59b19v1__dwr59b29v0` remains UNKNOWN after a 60-second CaDiCaL timeout.
F309 tests the least wasteful depth-3 expansion: keep `19=1,29=0` fixed and
add one of bits 3, 1, 31, or 27.

## Commands

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/schedule_cube_planner.py \
  --cnf headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr61_n32_bit25_m09990bd2_fill80000000.cnf \
  --target dw --round 59 \
  --combos 19:29:3,19:29:1,19:29:31,19:29:27 \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F309_auxforce_sr61_bit25_dw59_depth3_outlier_expansion_manifest.jsonl
```

Executed only the eight children with `19=1,29=0`:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/run_schedule_cubes.py \
  --manifest headline_hunt/bets/cascade_aux_encoding/results/20260428_F309_auxforce_sr61_bit25_dw59_depth3_outlier_expansion_manifest.jsonl \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F309_auxforce_sr61_bit25_dw59_depth3_outlier_expansion_cadical_100k_stats.jsonl \
  --solver cadical --conflicts 100000 --stats \
  --cube-id dwr59b19v1__dwr59b29v0__dwr59b03v0 \
  --cube-id dwr59b19v1__dwr59b29v0__dwr59b03v1 \
  --cube-id dwr59b19v1__dwr59b29v0__dwr59b01v0 \
  --cube-id dwr59b19v1__dwr59b29v0__dwr59b01v1 \
  --cube-id dwr59b19v1__dwr59b29v0__dwr59b31v0 \
  --cube-id dwr59b19v1__dwr59b29v0__dwr59b31v1 \
  --cube-id dwr59b19v1__dwr59b29v0__dwr59b27v0 \
  --cube-id dwr59b19v1__dwr59b29v0__dwr59b27v1
```

## Result

```
8 cubes
8 UNKNOWN at 100k conflicts
```

Stats summary:

| Metric | Mean | Min | Max |
|---|---:|---:|---:|
| Conflicts | 100000.750 | 100000 | 100002 |
| Decisions | 676905.500 | 609538 | 811152 |
| Propagations | 18081746.500 | 17439894 | 19395538 |
| Restarts | 8517.750 | 7646 | 10349 |
| Learned clauses | 94188.750 | 93824 | 94676 |
| Process seconds | 3.580 | 3.360 | 3.770 |

Ranked children by decisions:

| Cube | Decisions | Propagations | Process seconds |
|---|---:|---:|---:|
| `dwr59b19v1__dwr59b29v0__dwr59b27v1` | 811152 | 19395538 | 3.73 |
| `dwr59b19v1__dwr59b29v0__dwr59b01v0` | 739243 | 18432886 | 3.36 |
| `dwr59b19v1__dwr59b29v0__dwr59b03v0` | 670601 | 18619844 | 3.74 |
| `dwr59b19v1__dwr59b29v0__dwr59b01v1` | 654842 | 17747249 | 3.41 |
| `dwr59b19v1__dwr59b29v0__dwr59b27v0` | 652873 | 17651560 | 3.49 |
| `dwr59b19v1__dwr59b29v0__dwr59b31v0` | 647116 | 17545908 | 3.77 |
| `dwr59b19v1__dwr59b29v0__dwr59b03v1` | 629879 | 17821093 | 3.51 |
| `dwr59b19v1__dwr59b29v0__dwr59b31v1` | 609538 | 17439894 | 3.63 |

## Interpretation

Depth-3 manual expansion still produces no SAT/UNSAT split at 100k conflicts.
The highest-counter child is:

```
dW[59] bits 19=1, 29=0, 27=1
```

But this is still a ranking signal only. It is not evidence of tractability.

At this point, manual shallow cubing has a consistent negative result:

- F306 depth-1: no split.
- F307 targeted depth-2: no split.
- F308 outlier 60s timeout: no solve.
- F309 targeted depth-3 children: no split.

The next useful work is not more hand-selected shallow cubes. The branch needs
a smarter selector: BP/BDD marginals, hard-core variable scoring, or a learned
policy over CaDiCaL stats.
