---
date: 2026-04-28
bet: cascade_aux_encoding
status: SR60_CORE_SHELL_1M_COMPARE
---

# F323: sr60 bit10 top core vs top shell at 1M conflicts

## Purpose

F322 suggested a direct shared-cap comparison between:

- top universal-core dW59 cube: `dwr59b29v1__dwr59b03v0`
- top matched W1_58 shell cube: `w1r58b01v1__w1r58b29v0`

Both use the same sr60 bit10 aux-force base CNF and CaDiCaL with stats at a
1M conflict cap.

## Commands

Core:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/run_schedule_cubes.py \
  --manifest headline_hunt/bets/cascade_aux_encoding/results/20260428_F321_sr60_bit10_dw59_universal_core_depth2_manifest.jsonl \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F323_sr60_bit10_top_core_cadical_1M_stats.jsonl \
  --solver cadical --conflicts 1000000 --stats \
  --cube-id dwr59b29v1__dwr59b03v0
```

Shell:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/run_schedule_cubes.py \
  --manifest headline_hunt/bets/cascade_aux_encoding/results/20260428_F322_sr60_bit10_w1r58_shell_matched_depth2_manifest.jsonl \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F323_sr60_bit10_top_shell_cadical_1M_stats.jsonl \
  --solver cadical --conflicts 1000000 --stats \
  --cube-id w1r58b01v1__w1r58b29v0
```

## Result

Both cubes remained `UNKNOWN`.

| Surface | Cube | Wall s | Decisions | Propagations | Restarts |
|---|---|---:|---:|---:|---:|
| dW59 universal core | `dwr59b29v1__dwr59b03v0` | 31.632 | 4642809 | 115236323 | 49311 |
| W1_58 shell | `w1r58b01v1__w1r58b29v0` | 41.053 | 5188785 | 156333038 | 55537 |

Relative to the core cube, the shell cube used:

- 1.30x wall time
- 1.12x decisions
- 1.36x propagations

## Interpretation

The matched 1M run strengthens F322's control result:

```
shell-eliminable variable != solver-easy cube split
```

For sr60 bit10, the best W1_58 shell cube is heavier than the best dW59
universal-core cube at the same conflict cap. The structural label still
matters for understanding the formula, but it is not enough as a cube-selection
policy.

The useful path is now to treat structural class as one feature among several
and let observed solver stats drive the next cube frontier. Concretely, the
next selector improvement should ingest F321/F322/F323 stats and emit a
cross-surface candidate list, rather than separately ranking "core" and "shell"
families by hand.
