---
date: 2026-04-28
bet: cascade_aux_encoding
status: RANKED_CUBE_FOLLOWUP_50K
---

# F304: ranked schedule cubes at 50k conflicts

## Purpose

F303 ranked cheap 10k-conflict schedule cubes. F304 follows up on the top
ranked cube families at 50k conflicts to see whether the ranking persists.

Also added explicit bit-combo support to the planner:

```bash
--combos 22:26,25:28,27:28
```

This lets workers generate targeted cube manifests without broad generation
and external filtering.

## Selected cube families

From F303:

- `dW[60]` depth-2 pairs: 22/26, 25/28, 27/28
- `W1[60]` bits: 26 and 23
- `W2[60]` bits: 28 and 29

Base CNF:

```
headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit31_m17149975_fillffffffff.cnf
```

## Commands

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/schedule_cube_planner.py \
  --cnf headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit31_m17149975_fillffffffff.cnf \
  --target dw --round 60 --combos 22:26,25:28,27:28 \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F304_dw60_ranked_pairs_cube_manifest.jsonl

python3 headline_hunt/bets/cascade_aux_encoding/encoders/schedule_cube_planner.py \
  --cnf headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit31_m17149975_fillffffffff.cnf \
  --target w1 --round 60 --combos 26,23 \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F304_w1_60_ranked_bits_cube_manifest.jsonl

python3 headline_hunt/bets/cascade_aux_encoding/encoders/schedule_cube_planner.py \
  --cnf headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit31_m17149975_fillffffffff.cnf \
  --target w2 --round 60 --combos 28,29 \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F304_w2_60_ranked_bits_cube_manifest.jsonl
```

Then each manifest was run with:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/run_schedule_cubes.py \
  --manifest <manifest.jsonl> \
  --out-jsonl <results.jsonl> \
  --solver cadical --conflicts 50000
```

## Results

All selected cubes reached the 50k conflict cap.

| Family | Cubes | Status | Mean wall | Median wall | Min | Max |
|---|---:|---|---:|---:|---:|---:|
| `dW[60]` ranked pairs | 12 | 12 UNKNOWN | 1.665368 | 1.703233 | 1.396052 | 1.835999 |
| `W1[60]` ranked bits | 4 | 4 UNKNOWN | 1.697224 | 1.695678 | 1.670156 | 1.727384 |
| `W2[60]` ranked bits | 4 | 4 UNKNOWN | 1.677536 | 1.671300 | 1.576559 | 1.790983 |

Slowest 50k cubes:

| Cube | Wall seconds |
|---|---:|
| `dwr60b27v0__dwr60b28v1` | 1.835999 |
| `dwr60b22v0__dwr60b26v1` | 1.794310 |
| `w2r60b29v0` | 1.790983 |
| `dwr60b22v1__dwr60b26v1` | 1.738049 |
| `w2r60b28v1` | 1.733401 |
| `w1r60b23v0` | 1.727384 |

## Interpretation

The ranking signal is weak so far. At 10k, the slowest depth-2 `dW` cube was
`22v0/26v0`; at 50k, the slowest was `27v0/28v1`. The selected families are all
in the same small wall-time band and all remain UNKNOWN.

This means F303/F304 should be treated as infrastructure and measurement
baselines, not evidence that these cubes are genuinely harder or easier. Fixed
conflict caps mostly measure per-conflict runtime and preprocessing effects
until a cube actually solves or separates on conflicts-to-UNSAT/SAT.

Still useful:

- The planner can now generate exact targeted cube families.
- The runner can execute them reproducibly and record JSONL results.
- The first ranked batch shows that deeper budget is needed before cube choice
  becomes a real conquer signal.

## Next move

Add a runner mode that captures CaDiCaL statistics without `-q`, especially
decisions, propagations, and conflicts per cube. Wall time alone is too noisy
for ranking while every cube hits the same conflict cap.
