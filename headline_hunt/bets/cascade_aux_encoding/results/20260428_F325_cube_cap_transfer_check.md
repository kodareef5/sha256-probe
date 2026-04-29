---
date: 2026-04-28
bet: cascade_aux_encoding
status: CUBE_CAP_TRANSFER_CHECK
---

# F325: 50k-to-200k cube-rank transfer is noisy

## Purpose

F324 made cross-surface ranking easier. F325 adds a narrower transfer check:
for cube IDs observed at two solver caps, compare whether the lower-cap rank
predicts the higher-cap rank.

New tool:

```
headline_hunt/bets/cascade_aux_encoding/encoders/compare_cube_caps.py
```

It joins two `run_schedule_cubes.py` JSONL files by `cube_id` and reports:

- baseline/followup metric values
- metric ratio
- baseline/followup rank
- rank delta
- Spearman rank correlation on the shared cube set

## Commands

Decision transfer:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/compare_cube_caps.py \
  --baseline headline_hunt/bets/cascade_aux_encoding/results/20260428_F321_sr60_bit10_dw59_universal_core_depth2_cadical_50k_stats.jsonl \
  --followup headline_hunt/bets/cascade_aux_encoding/results/20260428_F322_sr60_bit10_dw59_universal_core_top4_cadical_200k_stats.jsonl \
  --baseline-label c50k --followup-label c200k \
  --metric decisions \
  --out-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F325_sr60_bit10_core_50k_to_200k_decision_transfer.json
```

Propagation transfer:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/compare_cube_caps.py \
  --baseline headline_hunt/bets/cascade_aux_encoding/results/20260428_F321_sr60_bit10_dw59_universal_core_depth2_cadical_50k_stats.jsonl \
  --followup headline_hunt/bets/cascade_aux_encoding/results/20260428_F322_sr60_bit10_dw59_universal_core_top4_cadical_200k_stats.jsonl \
  --baseline-label c50k --followup-label c200k \
  --metric propagations \
  --out-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F325_sr60_bit10_core_50k_to_200k_propagation_transfer.json
```

## Result

For the four dW59 core cubes followed from 50k to 200k, both metrics transfer
poorly.

Decision-rank Spearman correlation:

```
-0.2
```

| 200k rank | Cube | 50k rank | 50k decisions | 200k decisions | Ratio |
|---:|---|---:|---:|---:|---:|
| 1 | `dwr59b29v1__dwr59b03v0` | 2 | 424815 | 1196790 | 2.817 |
| 2 | `dwr59b29v1__dwr59b01v0` | 3 | 423965 | 1183162 | 2.791 |
| 3 | `dwr59b29v0__dwr59b03v0` | 4 | 408203 | 1131783 | 2.773 |
| 4 | `dwr59b01v1__dwr59b03v0` | 1 | 424826 | 1072370 | 2.524 |

Propagation-rank Spearman correlation:

```
-0.4
```

| 200k rank | Cube | 50k rank | 50k propagations | 200k propagations | Ratio |
|---:|---|---:|---:|---:|---:|
| 1 | `dwr59b29v1__dwr59b01v0` | 3 | 6616644 | 26121969 | 3.948 |
| 2 | `dwr59b29v1__dwr59b03v0` | 2 | 6750116 | 25761532 | 3.816 |
| 3 | `dwr59b29v0__dwr59b03v0` | 4 | 6581459 | 25434662 | 3.865 |
| 4 | `dwr59b01v1__dwr59b03v0` | 1 | 6870387 | 22310246 | 3.247 |

## Interpretation

The four-cube sample is small, but the warning is direct: a 50k cap is useful
for screening surfaces, not for freezing a cube frontier. The F321 50k winner
became the weakest of the four at 200k under both decisions and propagations.

Selector implication:

```
use shallow stats as noisy features, not as hard ordering
```

The next selector should diversify across the top shallow candidates rather
than commit to a single best shallow cube. A practical policy is beam-style
promotion: carry the top N from each surface to the next cap, then rerank after
200k or 1M evidence.
