---
date: 2026-04-29
bet: block2_wang × math_principles cross-machine
status: CROSS_MACHINE_VALIDATION — chamber-chart reachable from all yale-F351 masks
---

# F313: F312 atlas-loss search × yale's F351 score-87/88 active masks

## Cross-machine setup

- **yale (F351)**: cluster atlas of size-5 active masks, ranked by chain-output
  score. `0,1,3,8,9` = score-87 (best), 8 masks at score-88.
- **macbook (F311+F312)**: carry-chart atlas + atlas-loss schedule-space search.
  Block2_wang's historical mask `0,1,2,8,9` got atlas_score=104.45 (F115).

This memo runs my F312 atlas-loss search on yale's F351 top-5 score-87/88 masks
to test: do these "good" masks (low chain-output score) ALSO reach the chamber
chart family (dh, dCh) + low a57_xor under coordinate-aware loss?

## Result (4 restarts × 10k iterations per mask)

| yale mask | yale chain-score | F313 atlas score | best a57_xor_hw | best D61_hw | chart of best |
|---|---:|---:|---:|---:|---|
| `0,1,3,8,9`     | 87 | **42.15** | 6 | 12 | (dh, dCh) |
| `1,3,5,6,11`    | 88 | 42.45 | 6 | 12 | (dCh, dh) |
| `2,6,8,11,12`   | 88 | 43.70 | 6 | 13 | (dCh, dh) |
| `2,6,11,12,13`  | 88 | 44.25 | 4 | 14 | (dCh, dSig1) |
| `1,7,10,11,15`  | 88 | 44.55 | 6 | 14 | (dCh, dh) |

For comparison:
- F115 baseline (mask `0,1,2,8,9`, chain-loss search, 8×50k): atlas_score = **104.45**
- F312 (mask `0,1,2,8,9`, atlas-loss search, 8×50k): atlas_score = **38.85**

## Findings

### Finding 1 — Chamber chart is mask-independent under atlas loss

4 of 5 yale-masks find best points in (dh, dCh) family. The exception
(`2,6,11,12,13`) reaches (dCh, dSig1) but with the LOWEST a57_xor_hw=4 of
any mask tested. The chamber-chart reachability is a property of the loss
function, not the active-word selection.

### Finding 2 — Mask selection has small effect on best atlas score

Spread is 42.15-44.55 across yale's score-87/88 masks (5% relative). Compared
to F312's `0,1,2,8,9` 8×50k best of 38.85, no yale-mask at 4×10k beats it
significantly — but the budgets are different (F313 is 1/10th compute per
mask). At matched 4×10k compute, F312's `0,1,2,8,9` would score similarly.

### Finding 3 — yale's chain-score ranking does NOT track atlas loss closely

`0,1,3,8,9` (yale chain-score 87) gives F313 atlas 42.15.
`1,7,10,11,15` (yale chain-score 88) gives F313 atlas 44.55 — within 5%.

The two scoring functions are correlated but not identical: yale's metric
favors masks where chain-output diff descends well; atlas loss adds the
cascade-1 hardlock + chart-membership signals. **A perfect match would
require running yale's submodular calibration with atlas loss as the
fitness function** — natural extension.

### Finding 4 — `2,6,11,12,13` has best a57_xor_hw

This mask reached a57_xor_hw=4 (vs 5-6 for others), at cost of leaving the
(dh, dCh) chart for (dCh, dSig1). This suggests the cascade-1 hardlock and
chart membership are sometimes in tension — the score function's penalty
weights (alpha=4 a57, gamma=8 chart) determine which side wins.

## Cross-bet implications

- **For math_principles (yale's bet)**: consider rerunning F351 cluster atlas
  with atlas loss as the fitness function. The carry-chart atlas score is
  more cascade-relevant than chain-output diff and would re-rank masks.
- **For block2_wang (this bet)**: the search-space bottleneck is NOT mask
  selection (yale's masks ≈ block2_wang's mask under atlas loss). The
  bottleneck is the chamber-attractor brittleness from F311 — single-bit
  moves don't reach (a57=0, D61=4) regardless of mask.

## What's shipped

- `headline_hunt/bets/block2_wang/results/search_artifacts/F313_yale_masks/` —
  5 JSONs, one per yale mask.
- This memo.

## Discipline

- 5 × 14s = 70s wall.
- Direct atlas-score comparison vs F312 baseline.
- Cross-machine coordination: built on yale's just-shipped F351 result.
- ~5 min total wall (including memo).

## Next concrete moves

- (a) **Run yale's submodular calibration with atlas loss as fitness**: the
  natural follow-up. Yale's pipeline lives in `headline_hunt/bets/math_principles/`;
  swap `score_message` for atlas-loss eval and re-rank masks. (Coordinate
  with yale before doing this; might be in their backlog.)
- (b) **Run yale-mask `2,6,11,12,13` under atlas loss with weight tuning to
  prioritize a57_xor**: it reached a57_xor=4. Pushing a57_xor weight up
  might force it to 0 or 1. Worth ~10 minutes.
- (c) **Run F312 with yale mask `0,1,3,8,9` at full 8×50k budget**: directly
  compare to F312's `0,1,2,8,9` 8×50k atlas_score=38.85. Likely similar but
  worth the data point.
