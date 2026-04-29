---
date: 2026-04-28
bet: cascade_aux_encoding
status: CUBE_STATS_CAPTURE_ENABLED
---

# F305: cube runner stats mode

## Purpose

F304 showed that wall-time ranking alone is too noisy while every cube hits the
same conflict cap. F305 updates the cube runner to capture CaDiCaL statistics
into JSONL so ranked cube batches can be compared by decisions, propagations,
restarts, learned clauses, eliminated variables, and process time.

## Tool change

`run_schedule_cubes.py` now accepts:

```bash
--stats
```

For CaDiCaL this runs without `-q`, adds `--stats`, parses top-level statistic
rows, and stores them under each result's `stats` object.

Important parser detail: CaDiCaL has nested statistic rows, so the parser skips
indented rows and keeps only top-level keys. This avoids cases like nested
`learned: 0` or nested `conflicts: 0` overwriting the real totals.

## 50k stats rerun

Reran the F304 selected cube families at 50k conflicts with stats capture.
All still reached the conflict cap.

| Family | Cubes | Conflicts mean | Decisions mean | Propagations mean | Restarts mean | Process seconds mean |
|---|---:|---:|---:|---:|---:|---:|
| `dW[60]` ranked pairs | 12 | 50000.333 | 371561 | 6575130.583 | 3613.417 | 1.668 |
| `W1[60]` ranked bits | 4 | 50000.500 | 371272.500 | 6643233.750 | 3643.500 | 1.680 |
| `W2[60]` ranked bits | 4 | 50001.750 | 370232.500 | 6633996.500 | 3639.500 | 1.647 |

Highest-decision cubes:

| Cube | Decisions | Propagations | Learned |
|---|---:|---:|---:|
| `dwr60b22v1__dwr60b26v1` | 408171 | 7178431 | 46435 |
| `dwr60b25v0__dwr60b28v0` | 390462 | 6820778 | 46462 |
| `w1r60b23v1` | 388728 | 6958344 | 46605 |
| `w2r60b29v0` | 388260 | 6819713 | 46363 |
| `dwr60b25v0__dwr60b28v1` | 384380 | 6798169 | 46504 |

Highest-propagation cubes:

| Cube | Propagations | Decisions |
|---|---:|---:|
| `dwr60b22v1__dwr60b26v1` | 7178431 | 408171 |
| `w1r60b23v1` | 6958344 | 388728 |
| `dwr60b27v0__dwr60b28v0` | 6824587 | 382958 |
| `dwr60b25v0__dwr60b28v0` | 6820778 | 390462 |
| `w2r60b29v0` | 6819713 | 388260 |

## Interpretation

Stats mode gives a better ranking signal than wall time. The strongest repeated
candidate from the selected set is:

```
dW[60] bits 22=1 and 26=1
```

It has the highest decisions and propagations at 50k conflicts. Raw-coordinate
outliers remain visible too:

```
W1[60] bit 23 = 1
W2[60] bit 29 = 0
```

This still is not SAT/UNSAT separation. It is a practical way to prioritize
which cube families deserve deeper conquer budget or parallel expansion.

## Next move

Use stats-ranked cubes for a small depth-3 expansion. The natural first target
is to extend the `dW[60]` hard pair `22=1,26=1` by one more high-band bit
from 23, 25, 27, 28, or 29, then run at 50k/100k and rank by decisions and
propagations.
