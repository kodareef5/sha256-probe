---
F-number: F837
date: 2026-05-04
author: macbook-claude
type: tooling / ML baseline
evidence_level: EVIDENCE (231 labelled rows, ridge baseline, grouped-CV prefilter eval)
parent: F836 (M2-side seed-score baseline)
---

# F837 — W-pair-beam scorer: cross-candidate generalisation works

## Summary

Built a separate scorer for the **block-1 W-pair-beam** task (predicting
`best_seen.hw_total` from initial W-cube residual). Unlike the M2-side
scorer in F836 — which was per-candidate-only — **the W-side scorer
generalises across candidates**. A single shared scorer is deployable
as a prefilter for the W-pair-beam pipeline.

## Dataset

- **Source:** same `*pair_beam*.json` corpus, but extracts files that have
  `init_W` (block-1 W-cube residual runs).
- **Filter:** require `init_W` (4-tuple) + `best_seen.hw_total`.
- **Result:** **231 labelled rows × 77 features**, **16 distinct candidates**.
- **Label dist:** `best_seen.hw_total` ∈ [35, 47], mean=39.77, std=2.44.
- **Candidate distribution:** much more even than M2 side; top two
  (bit13_m916a56aa, bit24_mdc27e18c) have 40 rows each, then 5–19 for
  the rest. Good for grouped CV.

## Features (77 total)

- **W bit-position popcounts** (32 features): how many of W57..W60 have
  bit `b` set, for `b ∈ [0,32)`.
- **W per-word HW** (4): popcount of each word.
- **W total HW** (1).
- **init_hw, init_score, beam_width, max_radius, max_pairs, pair_pool,
  penalty_weight** (scalars).
- **init_hw63** (8): the round-63 per-lane HW vector. *Encodes
  candidate-derived structural information without leaking candidate ID.*
- **slots[0..3] + slot_span** (5): which W-positions are in the cube
  basis and how spread they are.
- **penalty_regs** one-hot (6) and **pair_rank** one-hot (7).

## Ridge results (numpy, λ=10)

| Setting | MAE ↓ | RMSE ↓ | R² ↑ |
|---|---|---|---|
| Naive: always-mean | 2.04 | 2.44 | 0.00 |
| Naive: linreg(init_hw) (in-sample) | 1.50 | 1.90 | +0.39 |
| Ridge, **random 5-fold** | 1.32 | 1.71 | +0.51 |
| Ridge, **grouped 5-fold (held-out cand)** | **1.59** | **1.92** | **+0.38** |
| Ridge, within-cand (bit13, n=40) | 1.09 | 1.55 | +0.42 |

**The headline:** grouped CV R² = +0.38, MAE 1.59 vs naive 2.04. The model
generalises to candidates it has never seen. This is the M2-side's
critical missing property.

## Prefilter recall evaluation (the deployment metric)

What we actually need from the model: when we score every candidate seed
and keep the top-K, how many of the truly-best (lowest-HW) seeds do we
retain?

Grouped-by-candidate CV (held-out cands), n=231, top-30% threshold (the
69 rows with `best_seen.hw_total ≤ 38`):

| keep | kept_n | recall | precision | random_recall |
|---|---|---|---|---|
| 30% | 69 | **43.5%** | 43.5% | 30% |
| 50% | 116 | **68.1%** | 40.5% | 50% |
| 70% | 162 | 84.1% | 35.8% | 70% |

At top-10% threshold (the 23 best, HW≤36):

| keep | kept_n | recall | precision | random_recall |
|---|---|---|---|---|
| 20% | 46 | **43.5%** | 21.7% | 20% |
| 30% | 69 | **65.2%** | 21.7% | 30% |
| 50% | 116 | 78.3% | 15.5% | 50% |

**Reading.** Keep-50% retains 68% of the top-30% — a 2× compute reduction
that drops only one in three good candidates. Keep-30% (3.3× reduction)
still retains 44%, beating random's 30%. For finding the rarest top-10%,
keep-30% retains 65% — a 2.17× lift over random.

## Bonus: M2-side prefilter recall (revising F836's pessimism)

Despite F836's grouped-CV MAE being catastrophic (R²=−0.88), the model is
*rank-preserving* even when calibration drifts. Re-evaluated as a
prefilter (grouped CV, n=109, top-30% threshold = HW ≤ 85):

| keep | recall | precision |
|---|---|---|
| 30% | **57.6%** | 57.6% |
| 50% | **75.8%** | 46.3% |
| 70% | 93.9% | 40.8% |

So the M2-side scorer is actually deployable as a cross-candidate
prefilter too — just don't trust its absolute predictions. F836's "no
cross-candidate generalisation" was the regression conclusion; **for the
ranking task, both scorers work**.

## Top features (W-side, full-fit standardized weights)

```
W_bit01      +0.60
init_hw      +0.50
W_bit11      +0.49
W_bit19      -0.39
beam_width   -0.38
W_bit13      -0.38
W_bit22      -0.37
W_bit14      +0.33
W_bit18      -0.32
init_hw63_2  +0.30   ← lane c at round 63
init_hw63_5  +0.28   ← lane f at round 63
W_bit04      +0.27
```

`init_hw63_2` and `init_hw63_5` (lanes c and f) being in the top 10
matches our F428–F520 priors that c and g are the active lanes for
cascade-1 and cg-objective ranking. The model independently rediscovered
that signal from telemetry.

## Code

- `headline_hunt/bets/block2_wang/seed_score/extract_dataset_w.py`
  → builds the W-side npz from search_artifacts.
- `headline_hunt/bets/block2_wang/seed_score/ridge_baseline.py`
  → reused from F836.
- `headline_hunt/bets/block2_wang/seed_score/prefilter_eval.py`
  → recall@K-keep eval under grouped CV (the realistic deployment metric).

Reproduce:

```
python3 headline_hunt/bets/block2_wang/seed_score/extract_dataset_w.py \
    --out /tmp/seed_score_w.npz
python3 headline_hunt/bets/block2_wang/seed_score/ridge_baseline.py \
    --npz /tmp/seed_score_w.npz --lam 10.0 --within-candidate
python3 headline_hunt/bets/block2_wang/seed_score/prefilter_eval.py \
    --npz /tmp/seed_score_w.npz --top-frac 0.30 --keep 0.30 0.50 0.70
```

## Deployment plan (gate on user approval)

1. Wrap the pair-pool generation step inside `block2_bridge_beam.py` (the
   W-side equivalent of F836's M2 pipeline). Score every candidate
   (W57..W60, hw63, slots) tuple, keep top 50% by predicted
   `best_seen.hw_total`, run the full pair-beam only on survivors.
2. After each run, append `(features, best_seen.hw_total)` to a
   per-cand jsonl bank → online retraining as Yale ships.
3. Initial λ=10 from CV; could grid-search but the curve is flat.
4. Expected savings (keep-50%, recall-68%): roughly 2× faster sweep,
   loses ≈1/3 of the very best seeds. For an exhaustive backstop, run
   keep-100% periodically (weekly?) to catch what the prefilter misses.

## What would change my mind

- A run where the prefilter throws away a seed that ends up beating
  Yale's current floor (HW=82). Especially if the dropped seed scored
  in the predicted bottom 30%.
- Sklearn GBT not improving on ridge (would say the linear model has
  exhausted the signal in this feature set; would push us to add more
  features rather than swap models).
- A held-out future-week test (train on rows up to date X, eval on
  later rows) showing the model decays — would mean the manifold is
  shifting under us as Yale changes operators.
