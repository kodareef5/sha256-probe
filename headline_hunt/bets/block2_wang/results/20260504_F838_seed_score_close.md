---
F-number: F838
date: 2026-05-04
author: macbook-claude
type: tooling / ML closure
evidence_level: EVIDENCE (GBT + time-split + ridge across both prediction tasks)
parent: F837 (W-pair-beam scorer), F836 (M2 scorer)
---

# F838 — Seed-score closure: GBT + time-split, both scorers deploy-ready

## What changed since F837

Two follow-up checks the F837 memo flagged as open:

1. **Time-split eval** — train on the oldest 80% of rows, eval on the
   newest 20%. Detects manifold drift (the deployment-killer for static
   models).
2. **GBT (sklearn HistGradientBoosting) instead of ridge** — sees if the
   linear model has been leaving signal on the table.

## Time-split eval (ridge)

| | W-side | M2-side |
|---|---|---|
| Train n / val n | 185 / 46 | 87 / 22 |
| Naive MAE (always-train-mean) | 1.96 | 1.59 |
| Ridge MAE | **1.11** | 2.31 |
| Ridge R² | **+0.64** | **−0.89** |

W-side ridge **holds up under time-split** — actually improves over
grouped CV (1.59 → 1.11) because the most-recent rows are well-represented
in the training mix.

M2-side ridge **decays catastrophically** — worse than naive. Concluded:
M2 search operator is shifting fast (Yale's been adding new objectives
F520→F834 over 4 days), and ridge doesn't capture the regime change.

## GBT rescues both

`HistGradientBoostingRegressor(max_depth=4, lr=0.05, l2=1.0)`. Same CV
splits as ridge.

### W-side

| Setting | Ridge MAE | GBT MAE | Ridge R² | GBT R² |
|---|---|---|---|---|
| Random 5-fold | 1.32 | **1.18** | +0.51 | +0.53 |
| **Grouped (held-out cand)** | 1.59 | **1.52** | +0.38 | +0.39 |
| Within-cand bit13 | **1.09** | 1.25 | +0.42 | +0.31 |
| **Time-split** | 1.11 | **0.91** | +0.64 | **+0.74** |

GBT lifts grouped CV slightly and time-split substantially. Within-cand
it loses to ridge (40 rows is too few for trees).

### M2-side (the big rescue)

| Setting | Ridge MAE | GBT MAE | Ridge R² | GBT R² |
|---|---|---|---|---|
| Random 5-fold | 1.52 | 1.49 | +0.51 | +0.47 |
| **Grouped** | 4.90 | **1.65** | −3.73 | **+0.38** |
| Within-cand bit13 | **1.17** | 1.30 | +0.66 | +0.65 |
| **Time-split** | 2.31 | **1.53** | **−0.89** | **+0.16** |

GBT **fixes the M2 cross-candidate catastrophe** (R² −3.73 → +0.38) and
**fixes the time-split decay** (−0.89 → +0.16). F837's "M2 needs online
retraining" is no longer the right read — with a nonlinear model, the M2
prefilter is also static-deployable, just with a thinner safety margin
than W-side.

## Prefilter recall (the deployment metric)

| | Keep | Ridge recall@top-30% | GBT recall@top-30% |
|---|---|---|---|
| W-side grouped | 50% | 68% | **81%** |
| W-side grouped | 70% | 84% | **97%** |
| W-side time-split | 50% | 79% | **86%** |
| M2 grouped | 50% | 76% | **88%** |
| M2 time-split | 50% | 43% (worse than random) | **71%** |

**Operational picture.** Keep-50% (2× compute reduction) retains:
- W-side: 81–86% of true top-30%
- M2-side: 71–88% of true top-30%

That's the deployable threshold. Lift over random uniformly positive
across both scorers and both eval regimes.

## Top features (GBT permutation importance)

**W-side:** `init_hw` (0.33), `init_hw63_2` (0.07, **lane c**), `W_bit31`
(0.06), `W_bit14` (0.06), `init_score`, `W_bit11`, `W_bit01`, `W_bit27`,
`W_bit23`, `init_hw63_5` (**lane f**).

**M2-side:** `init_hw` (0.46), `m2_word10_hw` (0.18), `m2_lane0_hw`
(0.07), `cg_weight` (0.07), `init_m2_weight`, `m2_bit03`, `m2_bit30`.

Both pictures rediscover the cascade-1 priors. The W-side scorer
independently surfaces `init_hw63_2` and `init_hw63_5` (lanes c and f) —
the lanes our hand-engineered cg-objective targets. Validation that the
telemetry encodes real structure.

## Where this leaves Angle C

Three deployable artifacts now exist; both prediction tasks have a
working scorer; both pass time-split. The rest is wiring.

| Artifact | Status |
|---|---|
| W-pair-beam scorer (block-1) | Static-deploy ready (GBT, time-split R²=+0.74) |
| M2-pair-beam scorer (block-2) | Static-deploy ready (GBT, time-split R²=+0.16, recall@50%=71%) |
| Prefilter eval harness | Reusable for future scorer iterations |

**Open** (still gated on user direction):
- Wire either scorer *into* `block2_bridge_beam.py` / `block2_m2_pair_beam.py`
  pair-pool generation. Yale is mid-run; this is the coordination-risk
  step that needs explicit user OK.
- Add features for the M2 side targeting the new objectives Yale's been
  adding (objective-cross-feature interactions, lane-weighted bit
  popcounts). Could close the gap between M2 and W-side.
- Build the same pair (extractor + scorer) for the *overlap detour*
  pipeline (Yale F788/F789) — different prediction task, similar shape.

## Code (F836–F838)

```
headline_hunt/bets/block2_wang/seed_score/
  extract_dataset.py       — M2 side
  extract_dataset_w.py     — W side
  ridge_baseline.py        — numpy ridge, all CV variants
  gbt_baseline.py          — sklearn GBT
  prefilter_eval.py        — recall@K under grouped CV
  time_split_eval.py       — drift detection (ridge)
```

Reproduce W-side end-to-end:

```
python3 headline_hunt/bets/block2_wang/seed_score/extract_dataset_w.py --out /tmp/w.npz
python3 headline_hunt/bets/block2_wang/seed_score/gbt_baseline.py --npz /tmp/w.npz
```

## What would change my mind (final)

- A held-out future-week test (rows from after 2026-05-08, say) showing
  the GBT scorers also decay → M2-side time-split's R²=+0.16 is a soft
  warning sign and might still need online retrain in production.
- A run where the prefilter (keep-50%) discards a true headline-tier
  seed → would have to add safety net of periodic full sweeps.
- M2-side feature engineering closing the time-split R² gap (+0.16 →
  +0.50) without trees → would mean we're still under-featuring.
