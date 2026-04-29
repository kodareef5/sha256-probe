---
date: 2026-04-28
bet: cascade_aux_encoding
status: SCHEDULE_CUBE_RANKING_BASELINE
---

# F303: first schedule-cube ranking baseline

## Purpose

F302 shipped the schedule-aware cube planner. F303 uses it to test whether
cheap bounded cube runs expose any useful ranking signal over the high-bit
`W[60]` band.

All runs use the same base CNF:

```
headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit31_m17149975_fillffffffff.cnf
```

and CaDiCaL with a 10k conflict cap per cube.

## Runs

### 1. Depth-2 joint dW[60], bits 22..29

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/schedule_cube_planner.py \
  --cnf headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit31_m17149975_fillffffffff.cnf \
  --target dw --round 60 --bits 22-29 --depth 2 \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F303_dw60_bits22_29_depth2_cube_manifest.jsonl

python3 headline_hunt/bets/cascade_aux_encoding/encoders/run_schedule_cubes.py \
  --manifest headline_hunt/bets/cascade_aux_encoding/results/20260428_F303_dw60_bits22_29_depth2_cube_manifest.jsonl \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F303_dw60_bits22_29_depth2_cadical_10k.jsonl \
  --solver cadical --conflicts 10000
```

Result:

```
112 cubes
112 UNKNOWN at 10k conflicts
mean wall:   0.464352s
median wall: 0.450877s
min/max:     0.343984s / 0.775004s
```

Slowest depth-2 dW cubes:

| Cube | Wall seconds |
|---|---:|
| `dwr60b22v0__dwr60b26v0` | 0.775004 |
| `dwr60b22v0__dwr60b26v1` | 0.768267 |
| `dwr60b25v0__dwr60b28v0` | 0.746131 |
| `dwr60b27v1__dwr60b28v0` | 0.651338 |
| `dwr60b23v1__dwr60b27v0` | 0.610507 |

Per-bit mean wall across depth-2 cubes:

| Bit | Mean wall |
|---:|---:|
| 22 | 0.469857 |
| 23 | 0.472230 |
| 24 | 0.451238 |
| 25 | 0.450105 |
| 26 | 0.462277 |
| 27 | 0.488572 |
| 28 | 0.473242 |
| 29 | 0.447291 |

The largest signal is bit 27, with value-0 on bits 27 and 28 also heavier
than value-1 in the per-value breakdown.

### 2. Depth-1 W1/W2/dW comparison, bits 22..29

Compared raw `W1[60]`, raw `W2[60]`, and joint `dW[60]` cubes over the same
bit band at the same 10k conflict cap.

| Target | Cubes | Status | Mean wall | Median wall | Min | Max |
|---|---:|---|---:|---:|---:|---:|
| `dW[60]` | 16 | 16 UNKNOWN | 0.450396 | 0.462801 | 0.324303 | 0.545213 |
| `W1[60]` | 16 | 16 UNKNOWN | 0.496917 | 0.467806 | 0.436820 | 0.646558 |
| `W2[60]` | 16 | 16 UNKNOWN | 0.435179 | 0.403022 | 0.325674 | 0.662203 |

Slowest raw-coordinate cubes:

| Target | Cube | Wall seconds |
|---|---|---:|
| `W1[60]` | `w1r60b26v0` | 0.646558 |
| `W1[60]` | `w1r60b23v0` | 0.639528 |
| `W2[60]` | `w2r60b28v0` | 0.662203 |
| `W2[60]` | `w2r60b29v0` | 0.529441 |

## Interpretation

No cube solved within 10k conflicts, which is expected. The useful output is
ranking and skew, not SAT/UNSAT separation.

Early signals:

- `W1[60]` cubes are slightly slower on average than `W2[60]` or `dW[60]`
  cubes on this band.
- `W2[60]` has the largest single-bit outlier: bit 28 value 0.
- Depth-2 `dW` cubes identify a few candidate hard pairs: 22/26, 25/28,
  and 27/28.

This is a plausible cube-and-conquer selection rule for the next run: allocate
more budget to the ranked hard pairs instead of sweeping all schedule bits
uniformly.

## Next move

Run 50k-conflict follow-up on the top ranked cube families:

- `dW[60]` depth-2 pairs 22/26, 25/28, 27/28
- raw `W1[60]` bit 26 value 0 and bit 23 value 0
- raw `W2[60]` bit 28 value 0 and bit 29 value 0

If rankings persist at 50k, promote these cube families to the first real
parallel cube-and-conquer batch.
