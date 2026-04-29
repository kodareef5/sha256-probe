---
date: 2026-04-28
bet: cascade_aux_encoding
status: HARDCORE_STABILITY_SUMMARY_ADDED
---

# F317: hard-core stability summary across sr60 candidates

## Purpose

F316 compared two sr60 hard-core JSONs pairwise. F317 adds an N-input stability
summarizer so future selector work can separate stable hard-core bits from
candidate-dependent boundary bits.

New tool:

```
headline_hunt/bets/cascade_aux_encoding/encoders/summarize_hard_core_stability.py
```

It reports, for each semantic schedule bit, how often it is core/shell across
input hard-core JSONs.

## Command

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/summarize_hard_core_stability.py \
  headline_hunt/bets/cascade_aux_encoding/results/20260428_F269_aux_force_sr60_n32_bit10_m3304caa0_fill80000000_hard_core.json \
  headline_hunt/bets/cascade_aux_encoding/results/20260428_F269_aux_force_sr60_n32_bit11_m45b0a5f6_fill00000000_hard_core.json \
  --name sr60_bit10 --name sr60_bit11 \
  --out-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F317_sr60_bit10_bit11_hard_core_stability.json
```

## Result

Across the two sr60 candidates:

| Class | Count |
|---|---:|
| Stable core | 159 |
| Stable shell | 60 |
| Candidate-dependent | 37 |
| Total schedule keys | 256 |

By word/round:

| Word | Stable core | Stable shell | Variable | Mean core fraction |
|---|---:|---:|---:|---:|
| `w1[57]` | 7 | 13 | 12 | 0.406250 |
| `w1[58]` | 0 | 32 | 0 | 0.000000 |
| `w1[59]` | 32 | 0 | 0 | 1.000000 |
| `w1[60]` | 32 | 0 | 0 | 1.000000 |
| `w2[57]` | 10 | 12 | 10 | 0.468750 |
| `w2[58]` | 14 | 3 | 15 | 0.671875 |
| `w2[59]` | 32 | 0 | 0 | 1.000000 |
| `w2[60]` | 32 | 0 | 0 | 1.000000 |

## Interpretation

Late free rounds are stable: W59 and W60 are fully hard-core across both sr60
candidates. W1_58 is stable shell. The uncertain selector surface is W57 and
W2_58.

This gives a clean future policy:

- use candidate-local JSON for W57/W58 choices;
- treat W59/W60 as reliable hard-core target rounds;
- if adding a selector stability bonus, apply it only from same-`sr` cohorts.
