---
date: 2026-04-28
bet: cascade_aux_encoding
status: SIX_CAND_HARD_CORE_STABILITY_MATERIALIZED
---

# F332: six-candidate sr60 hard-core stability artifact

## Purpose

Macbook's F272/F273 comms note reports the six-candidate sr60 hard-core
stability result, but the machine-readable six-candidate stability artifact was
not present in this checkout. F332 materializes that summary using the existing
`summarize_hard_core_stability.py` tool.

## Inputs

- F269 bit10 aux-force hard-core JSON
- F269 bit11 aux-force hard-core JSON
- F270 bit13 aux-force hard-core JSON
- F272 bit0 aux-force hard-core JSON
- F272 bit17 aux-force hard-core JSON
- F272 bit18 aux-force hard-core JSON

Output:

`headline_hunt/bets/cascade_aux_encoding/results/20260428_F332_sr60_6cand_hard_core_stability.json`

## Result

| Class | Count |
|---|---:|
| Stable core | 139 |
| Stable shell | 38 |
| Variable | 79 |

Per word-round:

| Word round | Stable core | Stable shell | Variable | Mean core fraction |
|---|---:|---:|---:|---:|
| w1[57] | 1 | 1 | 30 | 0.401042 |
| w1[58] | 0 | 32 | 0 | 0.000000 |
| w1[59] | 32 | 0 | 0 | 1.000000 |
| w1[60] | 32 | 0 | 0 | 1.000000 |
| w2[57] | 2 | 4 | 26 | 0.447917 |
| w2[58] | 8 | 1 | 23 | 0.750000 |
| w2[59] | 32 | 0 | 0 | 1.000000 |
| w2[60] | 32 | 0 | 0 | 1.000000 |

## Interpretation

The six-candidate expansion confirms the 128-bit universal hard core:
`W1_59`, `W1_60`, `W2_59`, and `W2_60` are fully stable core across all six
sr60 candidates.

It also confirms the W1_58 shell result: all 32 bits of `W1_58` are stable
shell across the six-candidate set. The expanded sample mostly converts earlier
near-stable W57/W58 bits into candidate-dependent variables rather than moving
the W59/W60 universal target.

This supports keeping cube-selection effort on the universal 128-bit
W59/W60 surface, while treating W57/W58 as candidate-specific or BP-feature
surface rather than universal cube backbone.
