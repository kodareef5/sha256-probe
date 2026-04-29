---
date: 2026-04-28
bet: cascade_aux_encoding
status: OUTLIER_CUBE_TIMEOUT
---

# F308: 60-second timeout test on F307 outlier cube

## Purpose

F307 identified one depth-2 `dW[59]` cube on the aux-force sr61 bit25 proxy
with an unusually high decision count at 100k conflicts:

```
dW[59] bit19 = 1
dW[59] bit29 = 0
```

F308 tests whether that cube becomes tractable under a solver-native 60-second
CaDiCaL timeout.

## Tool update

`run_schedule_cubes.py` now supports:

```bash
--cube-id <id>
--solver-time-sec <seconds>
```

`--cube-id` runs an exact cube from a manifest. `--solver-time-sec` passes a
native time limit to CaDiCaL (`-t`) so CaDiCaL exits cleanly and emits stats.

## Command

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/run_schedule_cubes.py \
  --manifest headline_hunt/bets/cascade_aux_encoding/results/20260428_F307_auxforce_sr61_bit25_dw59_ranked_pairs_cube_manifest.jsonl \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F308_auxforce_sr61_bit25_outlier_cube_cadical_60s_stats.jsonl \
  --solver cadical --solver-time-sec 60 --stats \
  --cube-id dwr59b19v1__dwr59b29v0
```

## Result

```
status: UNKNOWN
wall:   60.008084s
```

Stats:

| Metric | Value |
|---|---:|
| Conflicts | 1,445,583 |
| Decisions | 7,176,242 |
| Propagations | 214,798,229 |
| Restarts | 82,588 |
| Learned clauses | 1,395,164 |
| Fixed vars | 1,266 |
| Eliminated vars | 7,212 |
| Substituted vars | 2,113 |
| Max RSS | 31.04 MB |

## Interpretation

The F307 outlier cube is not tractable at 60 seconds. This reinforces the
current cube-and-conquer picture:

- F262/F263: macbook depth-1/depth-2 `dW[58]` on F235 did not split into
  tractable subproblems.
- F306: Yale depth-1 `dW[59]` on the aux-force sr61 bit25 proxy produced no
  tractable single-bit cube at 50k conflicts.
- F307/F308: targeted depth-2 `dW[59]` produces a strong stats outlier, but
  the outlier still times out at 60 seconds.

Shallow schedule cubing is not enough. If cube-and-conquer remains alive, it
needs either deeper cubes or a more informed branching policy than single
schedule-bit/differential-bit selection.

## Next move

Depth-3 expansion around `dW[59] bit19=1, bit29=0` is the least wasteful next
test, but it should be capped tightly. If depth-3 also yields only UNKNOWN at
modest budgets, this branch should pivot toward BDD/BP-style guidance rather
than manual cube selection.
