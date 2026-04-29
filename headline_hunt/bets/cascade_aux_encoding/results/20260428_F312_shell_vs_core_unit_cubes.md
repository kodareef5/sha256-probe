---
date: 2026-04-28
bet: cascade_aux_encoding
status: SHELL_UNIT_CUBES_NO_SPLIT
---

# F312: shell W57 unit cubes versus dW59 hard-core baseline

## Purpose

F311 showed that the sr61 bit25 proxy's schedule shell is concentrated in W57,
while every `dW[59]` bit is fully hard-core. F312 tests whether shell schedule
unit cubes produce an easy split at the same 50k CaDiCaL conflict budget used
by the F306 dW59 depth-1 baseline.

## Shell Bits Tested

Selected shell variables from the F311 hard-core JSON:

- `W1_57` bits: 4, 6, 7, 8, 10, 11, 13, 14
- `W2_57` bits: 1, 2, 3, 5, 9, 10, 11, 12

Each bit was tested as a unit cube for both values.

## Commands

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/schedule_cube_planner.py \
  --cnf headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr61_n32_bit25_m09990bd2_fill80000000.cnf \
  --target w1 --round 57 --bits 4,6,7,8,10,11,13,14 --depth 1 \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F312_auxforce_sr61_bit25_w1r57_shell_depth1_manifest.jsonl

python3 headline_hunt/bets/cascade_aux_encoding/encoders/schedule_cube_planner.py \
  --cnf headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr61_n32_bit25_m09990bd2_fill80000000.cnf \
  --target w2 --round 57 --bits 1,2,3,5,9,10,11,12 --depth 1 \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F312_auxforce_sr61_bit25_w2r57_shell_depth1_manifest.jsonl
```

Both manifests were run with:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/run_schedule_cubes.py \
  --manifest MANIFEST.jsonl \
  --out-jsonl OUT.jsonl \
  --solver cadical --conflicts 50000 --stats
```

Stats summaries were generated with `rank_cube_stats.py`.

## Result

All 32 shell unit cubes remained `UNKNOWN` at 50k conflicts.

Comparison against F306 dW59 depth-1 baseline:

| Batch | Cubes | Status | Mean decisions | Min | Max | Mean propagations | Mean wall s |
|---|---:|---|---:|---:|---:|---:|---:|
| F306 `dW[59]` depth-1 | 64 | all UNKNOWN | 368814.297 | 301911 | 410185 | 8612153.359 | 1.984 |
| F312 `W1_57` shell units | 16 | all UNKNOWN | 346669.188 | 311798 | 379221 | 8235592.375 | 1.934 |
| F312 `W2_57` shell units | 16 | all UNKNOWN | 361933.375 | 346262 | 388582 | 8402942.812 | 1.978 |

Top shell cubes by decisions:

| Cube | Decisions | Propagations |
|---|---:|---:|
| `w2r57b02v0` | 388582 | 9367801 |
| `w1r57b11v0` | 379221 | 8750878 |
| `w1r57b07v0` | 376617 | 8424307 |
| `w2r57b10v1` | 374216 | 8561955 |
| `w2r57b12v1` | 373777 | 8277334 |
| `w2r57b09v1` | 372907 | 7486801 |

## Interpretation

Shell membership is not a one-step cube split. The selected W57 shell unit
cubes did not create SAT/UNSAT outcomes and did not beat the dW59 hard-core
baseline on average solver effort.

The result narrows the role of shell variables:

- not promising as standalone depth-1 cube splits;
- still plausible as decision-order hints or preprocessing/elimination targets;
- useful as a contrast class for hard-core dW variables.

The next productive probe is either true shell elimination/reduction or solver
decision-priority control. More unit-cube pilots on shell bits are unlikely to
change the picture.
