---
date: 2026-04-28
bet: cascade_aux_encoding
status: SR61_HARD_CORE_STABILITY_MATERIALIZED
---

# F336: four-candidate sr61 hard-core stability artifact

## Purpose

F274/F275 reports that the universal hard-core pattern extends to sr61, but the
machine-readable four-candidate stability JSON was not present in this checkout.
F336 materializes that artifact with the existing
`summarize_hard_core_stability.py` tool.

## Inputs

- F274 bit10 sr61 aux-force hard-core JSON
- F274 bit13 sr61 aux-force hard-core JSON
- F274 bit18 sr61 aux-force hard-core JSON
- F311 bit25 sr61 aux-force hard-core JSON

Output:

`headline_hunt/bets/cascade_aux_encoding/results/20260428_F336_sr61_4cand_hard_core_stability.json`

## Result

| Class | Count |
|---|---:|
| Stable core | 129 |
| Stable shell | 8 |
| Variable | 55 |

Per word-round:

| Word round | Stable core | Stable shell | Variable | Mean core fraction |
|---|---:|---:|---:|---:|
| w1[57] | 1 | 3 | 28 | 0.414062 |
| w1[58] | 31 | 0 | 1 | 0.984375 |
| w1[59] | 32 | 0 | 0 | 1.000000 |
| w2[57] | 1 | 5 | 26 | 0.406250 |
| w2[58] | 32 | 0 | 0 | 1.000000 |
| w2[59] | 32 | 0 | 0 | 1.000000 |

## Interpretation

This reproduces the F275 memo numerically. The sr61 universal target is the
last two free schedule rounds: `W1_58`, `W1_59`, `W2_58`, and `W2_59`, with
one candidate-variable bit in `W1_58`.

Together with F332's sr60 six-candidate artifact, this gives downstream
selector code a machine-readable cross-mode basis:

- sr60: universal core is `W*_59 + W*_60` (128 bits)
- sr61: universal core is effectively `W*_58 + W*_59` (127 of 128 bits)

The common rule is "last two free schedule rounds," with first-free-round
behavior left as candidate-specific structure.
