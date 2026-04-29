---
date: 2026-04-28
bet: cascade_aux_encoding
status: CUBE_SURFACE_RANKER_ADDED
---

# F324: labelled cube-surface ranker

## Purpose

F321-F323 showed that structural labels are not enough by themselves:
universal-core dW59 and universal-shell W1_58 cubes need to be compared by
observed solver stats. F324 adds a small labelled ranker so future runs can
compare cube surfaces in one JSON table instead of hand-merging separate
`rank_cube_stats.py` outputs.

New tool:

```
headline_hunt/bets/cascade_aux_encoding/encoders/rank_cube_surfaces.py
```

Inputs are labelled `run_schedule_cubes.py` JSONL files:

```
--input LABEL=path/to/results.jsonl
```

The tool emits:

- per-surface metric and wall-time summaries
- top cubes across all labelled surfaces
- top assignments across all labelled surfaces, preserving surface counts

The default rank direction is descending, matching the current "hard cube"
workflow where more decisions/propagations are treated as stronger stress
signals.

## Smoke outputs

### 50k full-surface comparison

Command:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/rank_cube_surfaces.py \
  --input core_dw59_50k=headline_hunt/bets/cascade_aux_encoding/results/20260428_F321_sr60_bit10_dw59_universal_core_depth2_cadical_50k_stats.jsonl \
  --input shell_w1r58_50k=headline_hunt/bets/cascade_aux_encoding/results/20260428_F322_sr60_bit10_w1r58_shell_matched_depth2_cadical_50k_stats.jsonl \
  --metric decisions --top 12 --min-assignment-count 4 \
  --out-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F324_sr60_bit10_core_shell_50k_surface_rank.json
```

Surface summary:

| Surface | Rows | Status | Mean wall s | Mean decisions | Max decisions |
|---|---:|---|---:|---:|---:|
| `core_dw59_50k` | 24 | 24 UNKNOWN | 1.634 | 379529 | 424826 |
| `shell_w1r58_50k` | 24 | 24 UNKNOWN | 1.689 | 382985 | 440612 |

Top cross-surface cubes by decisions:

| Rank | Surface | Cube | Decisions |
|---:|---|---|---:|
| 1 | `shell_w1r58_50k` | `w1r58b01v1__w1r58b29v0` | 440612 |
| 2 | `shell_w1r58_50k` | `w1r58b01v0__w1r58b19v1` | 438094 |
| 3 | `core_dw59_50k` | `dwr59b01v1__dwr59b03v0` | 424826 |
| 4 | `core_dw59_50k` | `dwr59b29v1__dwr59b03v0` | 424815 |
| 5 | `core_dw59_50k` | `dwr59b29v1__dwr59b01v0` | 423965 |

Top assignment means:

| Rank | Assignment | Mean decisions | Surface |
|---:|---|---:|---|
| 1 | `w1[58].b1=0` | 395093 | shell |
| 2 | `dw[59].b3=0` | 394287 | core |
| 3 | `w1[58].b1=1` | 386414 | shell |
| 4 | `w1[58].b19=1` | 385496 | shell |
| 5 | `w1[58].b29=0` | 385006 | shell |

### 1M top-cube comparison

Command:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/rank_cube_surfaces.py \
  --input core_dw59_1M=headline_hunt/bets/cascade_aux_encoding/results/20260428_F323_sr60_bit10_top_core_cadical_1M_stats.jsonl \
  --input shell_w1r58_1M=headline_hunt/bets/cascade_aux_encoding/results/20260428_F323_sr60_bit10_top_shell_cadical_1M_stats.jsonl \
  --metric decisions --top 8 --min-assignment-count 1 \
  --out-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F324_sr60_bit10_core_shell_1M_surface_rank.json
```

The 1M labelled output preserves the F323 conclusion: shell is heavier than
core on this pair, but both are still UNKNOWN.

| Surface | Cube | Decisions | Wall s |
|---|---|---:|---:|
| `shell_w1r58_1M` | `w1r58b01v1__w1r58b29v0` | 5188785 | 41.053 |
| `core_dw59_1M` | `dwr59b29v1__dwr59b03v0` | 4642809 | 31.632 |

## Interpretation

F324 is a tooling step, not a solver breakthrough. It removes the manual
comparison friction that appeared in F321-F323 and makes the next selector
iteration straightforward:

1. gather result JSONLs from multiple structural surfaces;
2. label them by surface and cap;
3. rank all cubes and assignments together;
4. feed the top cross-surface candidates into the next manifest.

This supports the F323 direction: structural class should be a feature, while
observed solver stats should drive the next cube frontier.
