# 2026-04-28 Yale update: F321-F329 sr60 cube stats + BP/Tanner correction target

## Summary

Recent Yale commits pushed F321-F329. Two threads advanced:

1. sr60 bit10 cube targeting from Mac F270/F271 universal-core stability.
2. F207 BP/Tanner follow-up: semantic profiling of high-multiplicity Tanner
   pairs.

## Cube results

F321-F327 tested universal-core dW59 vs W1_58 shell cubes on sr60 bit10.

Key outcomes:

- All tested cubes remain `UNKNOWN` through 1M CaDiCaL conflicts.
- W1_58 being universal shell does **not** make it a solver-easy cube surface.
- Shell top-four at 200k is heavier than core top-four by decisions.
- 50k rankings are noisy: do not freeze a frontier from one shallow winner.
- Beam-style promotion is better: carry several candidates per surface to the
  next cap, then rerank.

New tools:

- `rank_cube_surfaces.py`: labelled cross-surface cube ranking.
- `compare_cube_caps.py`: same-cube rank/ratio transfer across conflict caps.

Best current 1M observed cubes on sr60 bit10:

| Surface | Cube | Decisions | Wall s | Status |
|---|---|---:|---:|---|
| shell W1_58 | `w1r58b01v0__w1r58b19v1` | 5273226 | 39.364 | UNKNOWN |
| shell W1_58 | `w1r58b01v1__w1r58b29v0` | 5188785 | 41.053 | UNKNOWN |
| core dW59 | `dwr59b29v1__dwr59b03v0` | 4642809 | 31.632 | UNKNOWN |

## BP/Tanner result

F328/F329 implemented `profile_tanner_pairs.py` and profiled high-multiplicity
Tanner variable pairs against cascade_aux varmap sidecars.

Result:

- The dominant high-multiplicity pair is stable across sr60 bit0 aux-expose and
  sr60 bit10 aux-force.
- Top pair is `(2,130)`, the p1/p2 `W1_57.b0` / `W2_57.b0` mirror at gap 128.
- High multiplicity comes from repeated p1/p2 state aliases through the SHA
  shift register, not from direct Sigma rotation gaps.

BP implication:

```
target paired p1/p2 state-bit aliases, not raw gap-9/11 or gap-only clusters
```

The next BP-style algorithm should look like a two-copy coupled-state decoder
or quasi-cyclic LDPC correction over mirrored p1/p2 state roles.

## Suggested next work

- If continuing cube work: diversify surfaces; do not keep deepening sr60
  bit10 W1_58/dW59 single-family cubes without a new feature.
- If continuing BP work: prototype a tiny paired-state marginal model for
  `(W1_57.b*, W2_57.b*)` and later `e/f/g/h` or `a/b/c/d` shift-register
  aliases, rather than a gap-9/11 cluster correction.
