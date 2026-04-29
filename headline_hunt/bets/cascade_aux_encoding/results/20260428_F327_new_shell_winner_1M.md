---
date: 2026-04-28
bet: cascade_aux_encoding
status: NEW_SHELL_WINNER_1M
---

# F327: new W1_58 shell winner at 1M

## Purpose

F326 promoted the W1_58 shell top-four to 200k and found a new shell winner:

```
w1r58b01v0__w1r58b19v1
```

F323 had already run the stale 50k shell winner at 1M. F327 runs the new 200k
winner at the same 1M cap.

## Command

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/run_schedule_cubes.py \
  --manifest headline_hunt/bets/cascade_aux_encoding/results/20260428_F322_sr60_bit10_w1r58_shell_matched_depth2_manifest.jsonl \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F327_sr60_bit10_new_top_shell_cadical_1M_stats.jsonl \
  --solver cadical --conflicts 1000000 --stats \
  --cube-id w1r58b01v0__w1r58b19v1
```

## Result

The cube remained `UNKNOWN`.

| Cube | Wall s | Decisions | Propagations | Restarts |
|---|---:|---:|---:|---:|
| `w1r58b01v0__w1r58b19v1` | 39.364 | 5273226 | 149085802 | 57603 |

The 200k-to-1M decision ratio for this cube is:

```
3.984x
```

## 1M cross-surface update

F327 updates the F323 comparison:

| Surface | Cube | Decisions | Wall s | Status |
|---|---|---:|---:|---|
| shell, new 200k winner | `w1r58b01v0__w1r58b19v1` | 5273226 | 39.364 | UNKNOWN |
| shell, old 50k winner | `w1r58b01v1__w1r58b29v0` | 5188785 | 41.053 | UNKNOWN |
| core, dW59 | `dwr59b29v1__dwr59b03v0` | 4642809 | 31.632 | UNKNOWN |

## Interpretation

The beam/rerank policy helped: the new 200k shell winner is also the stronger
1M shell cube by decisions. But the broader conclusion is unchanged:

- both shell 1M cubes remain UNKNOWN;
- the best shell cube is still heavier than the best dW59 core cube;
- W1_58 shell status is not a shortcut to an easy split.

For sr60 bit10, the immediate cube frontier is not producing SAT/UNSAT
separation. The next useful direction is either a deeper diversified beam
across more surfaces or a different feature source than raw shallow
CaDiCaL-heavy cubes.
