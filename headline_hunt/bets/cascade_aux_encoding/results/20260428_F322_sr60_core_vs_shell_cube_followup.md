---
date: 2026-04-28
bet: cascade_aux_encoding
status: SR60_CORE_VS_SHELL_CUBE_FOLLOWUP
---

# F322: sr60 bit10 universal-core continuation and W1_58 shell control

## Purpose

F321 found a coherent but shallow universal-core dW59 signal on sr60 bit10:
all 24 depth-2 cubes were UNKNOWN at 50k, with `dw[59].b3=0` as the strongest
repeated assignment. F322 extends the top F321 cubes to 200k and runs a matched
W1_58 shell-side control using the same bit positions.

This tests two questions:

- does the F321 top ranking survive a deeper 200k CaDiCaL cap?
- does the universal-shell W1_58 surface behave solver-easier than the
  universal-core dW59 surface?

## Universal-core dW59 top-4 at 200k

Command:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/run_schedule_cubes.py \
  --manifest headline_hunt/bets/cascade_aux_encoding/results/20260428_F321_sr60_bit10_dw59_universal_core_depth2_manifest.jsonl \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F322_sr60_bit10_dw59_universal_core_top4_cadical_200k_stats.jsonl \
  --solver cadical --conflicts 200000 --stats \
  --cube-id dwr59b01v1__dwr59b03v0 \
  --cube-id dwr59b29v1__dwr59b03v0 \
  --cube-id dwr59b29v1__dwr59b01v0 \
  --cube-id dwr59b29v0__dwr59b03v0
```

All four cubes remained `UNKNOWN`.

| Metric | Min | Mean | Max |
|---|---:|---:|---:|
| Wall seconds | 5.647 | 5.720 | 5.830 |
| Decisions | 1072370 | 1146026 | 1196790 |
| Propagations | 22310246 | 24907102 | 26121969 |

Top 200k decision cubes:

| Rank | Cube | Decisions | Status |
|---:|---|---:|---|
| 1 | `dwr59b29v1__dwr59b03v0` | 1196790 | UNKNOWN |
| 2 | `dwr59b29v1__dwr59b01v0` | 1183162 | UNKNOWN |
| 3 | `dwr59b29v0__dwr59b03v0` | 1131783 | UNKNOWN |
| 4 | `dwr59b01v1__dwr59b03v0` | 1072370 | UNKNOWN |

The deeper run preserves the F321 assignment signal around `b3=0`, but moves
the top pair from `b1=1,b3=0` to `b29=1,b3=0`.

## Matched W1_58 shell control at 50k

Manifest:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/schedule_cube_planner.py \
  --cnf headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit10_m3304caa0_fill80000000.cnf \
  --target w1 --round 58 --bits 29,19,1,3 --depth 2 \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F322_sr60_bit10_w1r58_shell_matched_depth2_manifest.jsonl
```

Run:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/run_schedule_cubes.py \
  --manifest headline_hunt/bets/cascade_aux_encoding/results/20260428_F322_sr60_bit10_w1r58_shell_matched_depth2_manifest.jsonl \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F322_sr60_bit10_w1r58_shell_matched_depth2_cadical_50k_stats.jsonl \
  --solver cadical --conflicts 50000 --stats
```

All 24 shell-control cubes returned `UNKNOWN`.

| Metric | Min | Mean | Max |
|---|---:|---:|---:|
| Wall seconds | 1.510 | 1.689 | 1.851 |
| Decisions | 359778 | 382985 | 440612 |
| Propagations | 6257260 | 7022843 | 8216564 |

Top shell-control decision cubes:

| Rank | Cube | Decisions | Status |
|---:|---|---:|---|
| 1 | `w1r58b01v1__w1r58b29v0` | 440612 | UNKNOWN |
| 2 | `w1r58b01v0__w1r58b19v1` | 438094 | UNKNOWN |
| 3 | `w1r58b01v0__w1r58b03v1` | 405842 | UNKNOWN |
| 4 | `w1r58b01v0__w1r58b29v1` | 393152 | UNKNOWN |
| 5 | `w1r58b01v1__w1r58b03v1` | 391787 | UNKNOWN |
| 6 | `w1r58b03v1__w1r58b29v1` | 388645 | UNKNOWN |

## Interpretation

F322 is a useful negative/control result:

- The dW59 universal-core continuation does not crack anything at 200k, but
  `b3=0` remains a stable hard assignment signal.
- W1_58 being universally shell-eliminable does not make W1_58 a solver-easy
  cube surface. At 50k, its mean decisions are essentially the same as F321's
  dW59 depth-2 mean, and its best shell cube is slightly higher than F321's best
  dW59 cube.

That separates two concepts that were easy to conflate:

```
shell-eliminable variable != useful shallow cube split
```

The next targeted run should compare the top F322 core cube
`dwr59b29v1__dwr59b03v0` against the top F322 shell cube
`w1r58b01v1__w1r58b29v0` at a shared 1M cap. If both stay UNKNOWN with similar
decision rates, cube targeting should move away from shell/core labels alone
and toward learned per-cube solver-stat transfer.
