---
date: 2026-04-28
bet: cascade_aux_encoding
status: SHELL_BEAM_PROMOTION
---

# F326: W1_58 shell top-four promoted to 200k

## Purpose

F325 recommended beam-style promotion instead of trusting a single shallow
winner. F326 applies that to the W1_58 shell surface by promoting the top four
50k shell cubes from F322 to a 200k CaDiCaL cap, then comparing them against
the already-promoted dW59 core top-four.

## Command

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/run_schedule_cubes.py \
  --manifest headline_hunt/bets/cascade_aux_encoding/results/20260428_F322_sr60_bit10_w1r58_shell_matched_depth2_manifest.jsonl \
  --out-jsonl headline_hunt/bets/cascade_aux_encoding/results/20260428_F326_sr60_bit10_w1r58_shell_top4_cadical_200k_stats.jsonl \
  --solver cadical --conflicts 200000 --stats \
  --cube-id w1r58b01v1__w1r58b29v0 \
  --cube-id w1r58b01v0__w1r58b19v1 \
  --cube-id w1r58b01v0__w1r58b03v1 \
  --cube-id w1r58b01v0__w1r58b29v1
```

All four shell cubes remained `UNKNOWN`.

## Shell 200k result

| Rank | Cube | Decisions | Wall s | Status |
|---:|---|---:|---:|---|
| 1 | `w1r58b01v0__w1r58b19v1` | 1323542 | 7.097 | UNKNOWN |
| 2 | `w1r58b01v0__w1r58b03v1` | 1233270 | 5.906 | UNKNOWN |
| 3 | `w1r58b01v1__w1r58b29v0` | 1231046 | 7.196 | UNKNOWN |
| 4 | `w1r58b01v0__w1r58b29v1` | 1191423 | 5.883 | UNKNOWN |

50k-to-200k shell decision transfer:

```
Spearman rank correlation: 0.4
```

| 200k rank | Cube | 50k rank | 50k decisions | 200k decisions | Ratio |
|---:|---|---:|---:|---:|---:|
| 1 | `w1r58b01v0__w1r58b19v1` | 2 | 438094 | 1323542 | 3.021 |
| 2 | `w1r58b01v0__w1r58b03v1` | 3 | 405842 | 1233270 | 3.039 |
| 3 | `w1r58b01v1__w1r58b29v0` | 1 | 440612 | 1231046 | 2.794 |
| 4 | `w1r58b01v0__w1r58b29v1` | 4 | 393152 | 1191423 | 3.030 |

## Core-vs-shell at 200k

Using `rank_cube_surfaces.py` on F322 core top-four and F326 shell top-four:

| Surface | Rows | Mean wall s | Mean decisions | Max decisions |
|---|---:|---:|---:|---:|
| `core_dw59_200k` | 4 | 5.720 | 1146026 | 1196790 |
| `shell_w1r58_200k` | 4 | 6.520 | 1244820 | 1323542 |

Top cross-surface 200k cubes:

| Rank | Surface | Cube | Decisions |
|---:|---|---|---:|
| 1 | shell | `w1r58b01v0__w1r58b19v1` | 1323542 |
| 2 | shell | `w1r58b01v0__w1r58b03v1` | 1233270 |
| 3 | shell | `w1r58b01v1__w1r58b29v0` | 1231046 |
| 4 | core | `dwr59b29v1__dwr59b03v0` | 1196790 |
| 5 | shell | `w1r58b01v0__w1r58b29v1` | 1191423 |
| 6 | core | `dwr59b29v1__dwr59b01v0` | 1183162 |

## Interpretation

F326 adds two useful corrections:

- Shell is not solver-easy here. At 200k, the shell top-four is heavier on
  average than the core top-four.
- Shallow shell ranking transfers better than the core sample from F325, but
  still not cleanly enough to trust a single 50k winner.

The beam policy is the right shape: promote several candidates per surface,
then rerank after a larger cap. The next useful run is a 1M cap on the new
200k shell winner `w1r58b01v0__w1r58b19v1`, because F323 only ran the old 50k
winner `w1r58b01v1__w1r58b29v0`.
