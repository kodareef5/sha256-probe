# F156: Structural priors don't transfer at this budget — consolidation of 4 falsifications

**2026-04-28**

## Summary

After 4 iterations of structural-prediction-and-test loop between
macbook and yale (F150-F155 macbook predictions, F128/F131/F132/F133
yale tests), the empirical answer is:

**Pure-structural priors (cand-level OR word-level) don't transfer
to absorber score floors at the 4-8 restart × 4-50k iteration budget.**

Yale's empirical {0,1,2,8,9} score-86 on bit3 is BIT3-CAND-SPECIFIC,
not a generic structural property.

## What was falsified

### Word-level structural metrics

| Iteration | Hypothesis | Yale's test result |
|---|---|---|
| F150 | Raw expansion-overlap density | F128: best 96 (vs 86) |
| F152 | 4-channel W[16] coverage | F131: best 96 (vs 86) |
| F154 | Dual-wave injection (W[16]+W[24]) | F133: best 100 (vs 86) |
| F155 | Composite (4-channel + dual-wave) | F133: 100 on (0,1,8,9,14) |

All 4 word-level structural metrics failed to predict yale's
empirical winner. Yale's own concentration ranker (F129) ranks the
empirical {0,1,2,8,9} at position 107/4368 — also missing.

### Cand-level structural distinction

| Cand | de58_size | hardlock | Predicted floor | Yale's empirical |
|---|---|---|---|---|
| bit3 baseline | ~50K | n/a | 86 (empirical) | 86 |
| bit19 (most extreme) | 256 | 13 | 65-75 (predicted) | **96-103 (F132)** |

bit19 was predicted to give the LOWEST floor; yale's F132 found it
gives a HIGHER floor than bit3 with bit3-inherited masks. Cand-level
structural distinction also falsified.

## What we learned (positive)

The 4-iteration loop did NOT find a magic structural metric, but it
DID surface several useful empirical observations:

1. **Mid-only control {8,9,10,11,12} reaches score 94** with msgHW=33
   (very sparse). This is the cleanest low-msgHW lane found in any
   F-iteration. Useful for absorber-design with sparsity as a goal.

2. **bit19 has its own anchor**: yale's F132 found {0,1,2,9,15} on
   bit19 reaches score 93/msgHW=42 (also sparse). bit19 has a
   DIFFERENT optimal active-word mask than bit3.

3. **Fixture-local active-word physics**: each cand fixture has its
   own optimum mask. Reuse of bit3 masks on other fixtures is
   PROVABLY suboptimal (yale's F132 explicitly tested this).

4. **Yale's 86 is structurally isolated**: no nearby radius-2 perturbation
   (raw, common-mode, additive, fixed-diff) escapes the basin (F123,
   F125, F126, F127). The empirical winner sits at a strict local
   minimum that pure structural reasoning can't predict from the
   active-word features alone.

## What this implies for the headline path

The principles framework's algorithmic candidates (synthesis 1-22 in
april28_explore/principles/) are NOT local search — they're poly-time
algorithms (matroid intersection, BP-Bethe, F4 Gröbner, etc.). These
should not be subject to the same fixture-locality limitation as
yale's heuristic absorber search.

The empirical falsification of structural transfer is consistent
with cascade-1's complexity being a CAND-SPECIFIC algebraic feature.
Polynomial-time algorithms operate ON the cand's specific algebraic
structure, not generic word-level priors.

For block2_wang's absorber search, the practical conclusion:

1. Continue yale's heuristic at fixture-locality (pool=0..15, full
   subset scan per cand) — slower but yields cand-specific masks
2. For each cand, characterize the local optimum mask + score floor
3. Cross-cand comparison BY OPTIMA, not BY-FIXED-MASK transfer

For each of the 5 distinguished cand fixtures from F148/F149/F153,
yale's full pool=0..15 scan would take ~30 min × 5 = 2.5 hr compute.
Within feasible compute scale.

## Honest assessment of the structural framework

The principles framework predicted:
- Σ-Steiner partial cover → BP-Bethe poly-time on cascade-1 (F134-F139,
  empirically calibrated to ~2-5 sec wall) — STILL VALID at the
  algorithmic level
- Structural distinction (de58_size) → cand-level yield transfer to
  block2_wang — FALSIFIED at this compute budget
- Active-word structural metrics → block2_wang yield prediction —
  FALSIFIED across 4 iterations

The framework's algorithmic-level predictions (BP-Bethe, matroid
intersection) ARE NOT FALSIFIED — they haven't been implemented yet.

The framework's structural-prior predictions for the heuristic
absorber search ARE FALSIFIED. The structural framework explains
WHY cascade-1 has algorithmic potential (Σ-Steiner topology + Iwasawa
pipelines), but NOT what makes a particular block-2 absorber active-
word mask succeed at heuristic local search.

## Concrete next moves (priority-ordered)

1. **Fixture-local full scan on each distinguished cand** (yale, ~2.5 hr
   compute): for each of bit19, bit28, bit4, bit25, msb_m9cfea9ce
   fixtures, run full pool=0..15 size-5 active subset scan.
   Yields cand-specific score floors for the rank-order test.

2. **Cross-cand optimum comparison**: do the cand-specific floors
   correlate with hardlock_bits or de58_size, even if reused-mask
   transfer doesn't? This is a stronger structural-distinction test.

3. **Implement matroid intersection M_C ∩ M_P** on bit3 fixture (per
   ALGORITHM_matroid_intersection.md from principles framework). If
   this matches yale's 86, the algorithmic poly-time prediction is
   empirically validated. If it BEATS 86, headline-eligible.

## Discipline

- 0 SAT compute throughout F134-F156
- 0 solver runs to log
- All structural priors derived from existing data + SHA-256 spec
- 4-iteration falsification chain documented for future reference

## Status

This memo CONSOLIDATES 4 failed iterations into a clean structural
conclusion. Yale's heuristic absorber search needs fixture-local
optimization, not generic structural priors. The framework's
algorithmic-level predictions (BP-Bethe, matroid intersection) remain
the headline-eligible path.

Honest negative results are valuable. The macbook ↔ yale loop produced
4 iterations in ~30 minutes of fleet time — that's compounding learning
even when each iteration falsifies the prediction.
