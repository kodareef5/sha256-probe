---
date: 2026-04-28
bet: cascade_aux_encoding
status: F235_PROXY_CUBE_PILOT
---

# F306: aux-force sr61 bit25 cube pilot

## Purpose

Macbook suggested the F235 hard instance as the natural test target for the
new cube planner. The exact true-sr61 CNF named in the note,
`cnfs_n32/sr61_cascade_m09990bd2_f80000000_bit25.cnf`, is not present in this
checkout. The compatible cascade_aux proxy is present:

```
headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr61_n32_bit25_m09990bd2_fill80000000.cnf
```

Because this is `sr=61`, the cascade_aux encoder reports `n_free=3`, so the
free schedule window is `W[57..59]`. F306 therefore cubes `dW[59]`, not
`dW[60]`.

## Commands

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/schedule_cube_planner.py \
  --cnf headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr61_n32_bit25_m09990bd2_fill80000000.cnf \
  --target dw --round 59 --bits 0-31 --depth 1 \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F306_auxforce_sr61_bit25_dw59_depth1_cube_manifest.jsonl

python3 headline_hunt/bets/cascade_aux_encoding/encoders/run_schedule_cubes.py \
  --manifest headline_hunt/bets/cascade_aux_encoding/results/20260428_F306_auxforce_sr61_bit25_dw59_depth1_cube_manifest.jsonl \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F306_auxforce_sr61_bit25_dw59_depth1_cadical_50k_stats.jsonl \
  --solver cadical --conflicts 50000 --stats
```

## Result

```
64 cubes
64 UNKNOWN at 50k conflicts
```

Stats summary:

| Metric | Mean | Min | Max |
|---|---:|---:|---:|
| Conflicts | 50000.562 | 50000 | 50005 |
| Decisions | 368814.297 | 301911 | 410185 |
| Propagations | 8612153.359 | 7337661 | 9891553 |
| Restarts | 4559.203 | 3365 | 5338 |
| Learned clauses | 46359.312 | 45940 | 46734 |
| Process seconds | 1.978 | 1.650 | 2.460 |

Highest-decision cubes:

| Cube | Decisions | Propagations | Process seconds |
|---|---:|---:|---:|
| `dwr59b29v1` | 410185 | 9287208 | 2.33 |
| `dwr59b03v1` | 405018 | 9891553 | 2.22 |
| `dwr59b31v0` | 403948 | 8905941 | 2.01 |
| `dwr59b31v1` | 403465 | 9122168 | 2.14 |
| `dwr59b01v1` | 399696 | 9060123 | 2.20 |

Highest-propagation cubes:

| Cube | Propagations | Decisions |
|---|---:|---:|
| `dwr59b03v1` | 9891553 | 405018 |
| `dwr59b19v0` | 9744430 | 398471 |
| `dwr59b02v1` | 9399521 | 370959 |
| `dwr59b27v1` | 9346065 | 383926 |
| `dwr59b29v1` | 9287208 | 410185 |

Mean decisions by value:

| dW bit value | Mean decisions |
|---:|---:|
| 0 | 367176.312 |
| 1 | 370452.281 |

## Interpretation

No single depth-1 cube becomes tractable at 50k conflicts on the aux-force
sr61 bit25 proxy. This does not refute cube-and-conquer; it says a one-bit
split is too shallow to separate the hard instance.

Useful signal:

- The decision spread is real: ~302k to ~410k decisions under the same conflict
  cap.
- The highest-counter bits are not simply the high-band bits from F303/F305.
  On this sr61 bit25 proxy, bit 3 value 1 and bit 29 value 1 are prominent.
- Value 1 is slightly heavier on average than value 0, but the difference is
  small.

## Next move

Run a targeted depth-2 expansion around the top F306 bits:

```
dW[59] bit pairs: 3/29, 3/19, 29/31, 1/29, 19/29
```

Use `--combos` and stats mode at 50k or 100k. If depth-2 still shows no
SAT/UNSAT separation, the cube pilot should move to parallel timeout tests
instead of fixed conflict caps.
