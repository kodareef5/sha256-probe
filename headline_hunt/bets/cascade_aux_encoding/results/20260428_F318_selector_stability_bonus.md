---
date: 2026-04-28
bet: cascade_aux_encoding
status: SELECTOR_STABILITY_BONUS_ADDED
---

# F318: stability bonus for hard-core cube selector

## Purpose

F317 separated stable hard-core bits from candidate-dependent boundary bits.
F318 wires that signal into `hard_core_cube_seeds.py` so future selector runs
can use same-`sr` cohort stability as an optional score component.

## Tool Change

`hard_core_cube_seeds.py` now supports:

- `--stability-json`: output from `summarize_hard_core_stability.py`;
- `--stability-weight`: score weight for the stability component;
- `--stability-mode core|shell`: choose core-frequency or shell-frequency.

For W1/W2 targets, the stability key is the direct semantic schedule bit. For
`dw` targets, the component is the average of the W1 and W2 bit stability.

Score is now:

```
core_weight * structural_score
+ observed_component
+ stability_weight * stability_component
```

With no `--stability-json`, behavior is unchanged.

## Smoke Test

Rank sr60 bit10 `W2_58` with the two-candidate sr60 stability summary:

```bash
python3 headline_hunt/bets/cascade_aux_encoding/encoders/hard_core_cube_seeds.py \
  --hard-core-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F269_aux_force_sr60_n32_bit10_m3304caa0_fill80000000_hard_core.json \
  --target w2 --round 58 --metric decisions \
  --stability-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F317_sr60_bit10_bit11_hard_core_stability.json \
  --stability-weight 1.0 \
  --top 12 \
  --out-json headline_hunt/bets/cascade_aux_encoding/results/20260428_F318_sr60_bit10_w2r58_stability_rank.json
```

Top-ranked bits all have:

```
core_class=core
stability_component=1.0
score=3.0
```

The selected stable-core W2_58 bits are:

```
28, 27, 26, 25, 24, 23, 21, 16, 14, 9, 8, 5
```

## Interpretation

This is a selector-policy improvement, not a solver result. It lets future
cube manifests prefer bits that are both hard-core for the local candidate and
stable across a same-`sr` cohort. That is useful for W57/W58, where F316/F317
showed candidate-specific movement.
