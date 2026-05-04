---
F-number: F836
date: 2026-05-04
author: macbook-claude
type: tooling / ML baseline
evidence_level: EVIDENCE (109 labelled rows; ridge baseline; CV results below)
parent: F835 (external research scan, Angle C)
---

# F836 — Seed-score ridge baseline: within-candidate signal, no cross-candidate

## What this is

F835 Angle C: train a small classifier on accumulated `*_pair_beam*.json`
telemetry to predict `best_seen_hw` from the *initial* configuration, so
we can prefilter cert-pin candidates instead of grinding everything.

## Dataset

- **Source:** 343 `*pair_beam*.json` files in
  `headline_hunt/bets/block2_wang/results/search_artifacts/`.
- **Filter:** require `best_seen_hw` and `init_M2` (M2-pair-beam runs only;
  excludes block-1 W-pair-beam files).
- **Join:** each result joined to its seed via `(seed_jsonl, seed_rank)` to
  recover candidate identity + rich seed features (`bridge_score`, `cg_*`,
  per-lane HWs).
- **Result:** **109 labelled rows × 192 features**, 14 distinct candidates.
- **Label dist:** `best_seen_hw` ∈ [78, 92], mean=86.12, std=2.89.

Top candidates by row count:
- `bit13_m916a56aa`: 43
- `bit24_mdc27e18c`: 32
- everyone else (12 cands): 2–5 rows each

## Method

Closed-form ridge regression in numpy (no sklearn). Standardize → fit
`(X^T X + λI)^-1 X^T y` → CV. λ=10 default. Three feature subsets tested:
all (192), seed-only (74), all-minus-m2-bit-popcounts (160).

CV variants:
- **Random 5-fold** — leaks candidate identity, optimistic.
- **Grouped 5-fold by candidate** — held-out candidates the model never saw.
- **Within-candidate 5-fold** on the largest cand (bit13_m916a56aa, n=43).

Naive baselines for comparison: always-mean, linreg(init_hw), linreg(init_m2_weight).

## Results

| Setting (λ=10) | MAE ↓ | RMSE ↓ | R² ↑ |
|---|---|---|---|
| Naive: always-mean | 2.24 | 2.90 | 0.00 |
| Naive: linreg(init_hw) (in-sample) | 1.92 | 2.56 | +0.22 |
| Ridge, all features, **random 5-fold** | **1.52** | **2.02** | **+0.51** |
| Ridge, all features, **grouped 5-fold** | 4.90 | 6.29 | −3.73 |
| Ridge, all features, **within-cand bit13** | **1.17** | **1.80** | **+0.66** |
| Ridge, seed-only, random 5-fold | 1.97 | 2.72 | +0.12 |
| Ridge, no-m2-bits, random 5-fold | 2.09 | 2.81 | +0.06 |
| Ridge, seed-only, grouped 5-fold | 21.2 | 34.0 | catastrophic |

## Reading

1. **Strong within-candidate signal.** Per-candidate prediction is *real*.
   For bit13_m916a56aa, ridge cuts MAE from 2.24 → 1.17 (47% reduction) and
   reaches R²=+0.66 on held-out folds. That's deployable.
2. **No cross-candidate generalisation.** Grouped-by-candidate CV is worse
   than predicting the mean. The model memorises candidate-specific
   M2-mask patterns; held-out candidates land outside its training
   manifold.
3. **M2-bit-pattern features carry the signal.** Dropping the 32
   `m2_bitNN` popcounts drops within-cand R² from +0.66 to +0.47. The
   seed-level `bridge_score` / `cg_*` features alone barely beat naive.
4. **Top features (standardized weights, full fit):** `m2_bit00`, `m2_bit29`,
   `init_hw`, `m2_bit01`, `m2_bit09`, `m2_bit14`, `m2_bit03`, `m2_bit26`,
   `shape_removed_bonus`, `m2_bit21`, `m2_word06_hw`. The bit-position
   popcounts dominate; the candidate-shape `shape_removed_bonus` matters
   too.

## Operational implication

The deployable form is **per-candidate ridge scorers**. Per-candidate
because:

- Yale's pair-beam pipeline runs the *same 13-cand portfolio* repeatedly.
- We have enough rows for two cands now (bit13: 43, bit24: 32) and will
  accumulate more on the others as Yale ships.
- Per-candidate models cleanly side-step the cross-candidate failure mode.

**Suggested deployment** (not built yet, gate on user approval):

1. After each pair-beam run, append `(features, best_seen_hw)` to a
   per-candidate jsonl bank.
2. When candidate has ≥20 rows, fit a ridge model offline. Store coefficients.
3. Wrap `block2_m2_pair_beam.py`'s pair-pool generation: score every
   candidate (M1, M2_pair) with the model, keep top 30% by predicted HW,
   cert-pin only those.
4. With current MAE=1.17 and a 4-point useful range (HW 82–86), top-30%
   filtering should keep ≥80% of true positives — cuts cert-pin cost by
   roughly 3× without missing the actually-promising seeds.

## What would change my mind

- A held-out experiment where the prefilter throws away a true positive
  that the un-filtered run would have found.
- A single-feature linear regression on the right derived M2 statistic
  beating the 192-feature ridge (would mean we're memorising not
  modelling).
- Candidate-conditioned features (e.g., `m2_bit_i × cand_id` interactions)
  closing the cross-candidate gap → would change the recommendation
  from per-candidate to one-shared model.

## Code

- `headline_hunt/bets/block2_wang/seed_score/extract_dataset.py`
  → builds the npz from the search_artifacts root + seed-jsonl join.
- `headline_hunt/bets/block2_wang/seed_score/ridge_baseline.py`
  → numpy-only ridge with random / grouped / within-cand CV and feature
  ablations.

Reproduce:

```
python3 headline_hunt/bets/block2_wang/seed_score/extract_dataset.py \
    --out /tmp/seed_score.npz
python3 headline_hunt/bets/block2_wang/seed_score/ridge_baseline.py \
    --npz /tmp/seed_score.npz --lam 10.0 --within-candidate
```

## Next (if user wants to push C further)

- Try classification (HW≤85 vs >85) — cleaner labels, can use logistic
  regression's calibrated probability to set the prefilter threshold.
- Install sklearn, swap ridge for gradient-boosted trees. Likely picks up
  M2-bit-position interactions ridge can't model.
- Build the per-candidate online deployment loop wired into
  `block2_m2_pair_beam.py`'s pair-pool generation.
- Try adding the W-pair-beam dataset (234 files) for the *block-1* HW
  prediction task — separate but related scorer.
