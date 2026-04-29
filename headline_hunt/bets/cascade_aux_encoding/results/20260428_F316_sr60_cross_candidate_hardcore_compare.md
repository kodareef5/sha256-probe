---
date: 2026-04-28
bet: cascade_aux_encoding
status: SR60_CROSS_CAND_HARDCORE_COMPARED
---

# F316: sr60 cross-candidate hard-core comparison

## Purpose

Mac F269 added hard-core JSONs for two more sr60 candidates. F316 runs the new
semantic comparator on those JSONs to check which hard-core schedule structure
is stable across candidates and which part is candidate-specific.

Compared JSONs:

- `20260428_F269_aux_force_sr60_n32_bit10_m3304caa0_fill80000000_hard_core.json`
- `20260428_F269_aux_force_sr60_n32_bit11_m45b0a5f6_fill00000000_hard_core.json`

## Command

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/compare_hard_core_jsons.py \
  headline_hunt/bets/cascade_aux_encoding/results/20260428_F269_aux_force_sr60_n32_bit10_m3304caa0_fill80000000_hard_core.json \
  headline_hunt/bets/cascade_aux_encoding/results/20260428_F269_aux_force_sr60_n32_bit11_m45b0a5f6_fill00000000_hard_core.json \
  --left-name sr60_bit10 --right-name sr60_bit11 \
  --out-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F316_sr60_bit10_bit11_hard_core_compare.json
```

## Result

Aggregate:

| Metric | sr60 bit10 | sr60 bit11 |
|---|---:|---:|
| Vars | 12540 | 12592 |
| Clauses | 52454 | 52657 |
| Shell vars | 8704 | 8755 |
| Core vars | 3836 | 3837 |
| Schedule core vars | 176 | 179 |
| Schedule shell vars | 80 | 77 |
| Aux core vars | 3659 | 3657 |

Schedule core by word/round:

| Word | bit10 core | bit11 core |
|---|---:|---:|
| `w1[57]` | 16 | 10 |
| `w1[58]` | 0 | 0 |
| `w1[59]` | 32 | 32 |
| `w1[60]` | 32 | 32 |
| `w2[57]` | 14 | 16 |
| `w2[58]` | 18 | 25 |
| `w2[59]` | 32 | 32 |
| `w2[60]` | 32 | 32 |

Set overlap:

| Set | Intersection | Union | Jaccard |
|---|---:|---:|---:|
| Schedule core | 159 | 196 | 0.811224 |
| Schedule shell | 60 | 97 | 0.618557 |

## Interpretation

The stable structure is late-round:

- `W1_59`, `W2_59`, `W1_60`, and `W2_60` are fully hard-core for both sr60
  candidates.
- `W1_58` is fully shell for both.

The candidate-specific structure lives in `W1_57`, `W2_57`, and `W2_58`.
This means selector results should transfer confidently for late-round dW
targets, but early/mid free-word choices need per-candidate hard-core JSON.

For future cube pilots, the selector should not assume a universal bit list
inside W57/W58. It should rank from the candidate's own JSON, then optionally
use cross-candidate overlap as a stability bonus.
