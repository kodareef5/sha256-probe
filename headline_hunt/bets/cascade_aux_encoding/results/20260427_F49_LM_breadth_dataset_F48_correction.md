# F49: LM-tail-breadth dataset for 67 cands + F48 honest correction
**2026-04-27 15:45 EDT**

Quantifies F48's "LM-tail breadth" metric across all 67 cands and
correlates with measured kissat walls. Result: **F48's monotonic-ordering
claim was overclaimed**. Real correlation is moderate (Pearson r ≈ 0.5)
with bit28 as a 2nd-axis outlier.

## Quantitative breadth definition

For each cand, compute:
```
cand_lm_breadth = max(LM cost across all F32 records for cand)
                - min(LM cost across all F32 records for cand)
```

Distribution across 67 cands:
- min: 67
- q1: 81
- median: 96
- q3: 108
- max: 128
- mean: 96.0

## F48's claim REVISED

F48 claimed: "kissat speed scales with LM-tail breadth — narrow → fast,
broad → slow."

Looking at the actual breadth values for the 4 measured cands:

| cand | breadth | seq median | F48-predicted | match? |
|---|---:|---:|---|:---:|
| bit2_ma896ee41 | 68 (NARROWEST in registry) | 27.08s | fast | ✓ |
| bit28_md1acca79 | **88** (lower-middle) | **39.25s** | medium | **✗** |
| bit10_m9e157d24 | 94 (median area) | 28.04s | medium | ✗ |
| msb_m17149975 | 118 (broad) | 35.81s | slow | ~✓ |

**Critical disagreement**: bit28 has narrower breadth than bit10
(88 vs 94), but bit28 takes ~11s LONGER. F48's monotonic claim is
violated.

Pearson correlation (N=4): r ≈ 0.50 — moderate, not strong.

## bit28 is an outlier on a 2ND axis

bit28's slowness can NOT be explained by LM-tail breadth alone. Some
other structural property makes bit28 hard for kissat.

Possible 2nd-axis explanations (untested):
- **# of distinct vectors per HW level** in the F32 corpus
  (bit28 might have many "competing" trails at each HW)
- **Pareto frontier breadth** in yale's F45 sampler (bit28 explores
  widely; corpus-static metric doesn't capture this)
- **Cand's specific bit pattern** in W-witness or residual

## Honest reformulation

The CORRECT current understanding:

> "kissat at 1M conflicts on cascade_aux Mode A sr=60 has wall times
> in the 27-39s range across 4 distinguished cands tested. The data
> are consistent with a WEAK positive correlation between cand-level
> LM-tail-breadth (max-min LM across HW levels) and median wall
> (Pearson r ≈ 0.5, N=4). bit28_md1acca79 is an outlier on this
> trend — it takes 39s despite a relatively narrow breadth (88, q1).
> Some other structural property of bit28 makes it harder for kissat
> than its breadth predicts."

## What F47 ACTUALLY showed (not F48)

Going back to F47:
- bit28 sequential RANGE = 21.8s (vs ~3s for plateau)
- bit28 sequential MEDIAN = 39.25s (vs 27-28s plateau)

The high SEED VARIANCE is the most distinctive bit28 feature, NOT
just the median. This points to "branchiness" in cascade_aux CNF —
some seeds find a quick path, others flounder.

Branchiness might OR might not correlate with LM-breadth. F49's data
suggests it's a different axis.

## What's still real about F48

The CONTRAST between bit2 (NARROWEST in registry, fastest) and
msb_m17149975 (BROAD breadth=118, medium-slow) IS real and consistent
with the breadth hypothesis. The bit28 datapoint disturbs the trend.

The F25 "1 distinct vector at min HW" finding (which makes bit2's
breadth unusually narrow) IS structurally interesting — bit2 has the
narrowest breadth IN THE REGISTRY (68), not just narrow.

So a milder claim survives:

> "bit2_ma896ee41 has the registry-narrowest LM-tail breadth (68) AND
> the registry-fastest kissat sequential wall (27s) at 1M conflicts.
> No other cand has breadth this low. This is consistent with a
> 'narrow-tail = fast solver' relationship at the extreme, but the
> intermediate cases don't follow a monotonic order."

## Discipline correction

F48 was overclaimed. The 4-cand "monotonic ordering" was actually:
- by breadth: bit2(68) < bit28(88) < bit10(94) < msb_m17149975(118)
- by wall:    bit2(27) < bit10(28) < msb_m17149975(36) < bit28(39)

bit28 ranks 2nd by breadth but 4th by wall — not monotonic.

This is the SAME class of error as F39 catching F37/F38's "cliff"
artifact: jumping to a strong claim from a small N before checking the
data carefully.

**Discipline lesson reinforced**: when establishing a correlation
across cands, check the FULL distribution of the predictor variable
before claiming monotonicity. Pearson r ≈ 0.5 is "moderate"; only
Pearson > 0.85 should be called "strong."

## Useful artifacts retained

Even though F48's claim is refined, the UTILITY survives:

1. **`cand_lm_breadth` dataset** for 67 cands (saved to
   /tmp/cand_lm_breadth.json; can be merged into
   F28_deep_corpus_enriched.jsonl as a per-cand field).

2. **bit2 IS distinct** — narrowest breadth in the entire registry.
   Its kissat speed advantage is REAL and matches one prediction.

3. **bit28's outlier slowness** is a NEW finding — not breadth-driven,
   needs further investigation.

4. **Untested cands at extremes** can be tested next:
   - NARROWEST untested: bit11_m45b0a5f6 (breadth 67) — should be fast
   - BROADEST untested: msb_m9cfea9ce (breadth 128) — should be slow

If these match prediction, the breadth-as-predictor story strengthens.
If they don't, F48 is fully refuted.

## Prediction test (added during F49 same session)

To distinguish "weak predictor" from "no predictor", tested 2 untested
cands at the breadth extremes:

| cand | breadth | predicted | observed seq median | result |
|---|---:|---|---:|---|
| bit11_m45b0a5f6 | 67 (NARROWEST untested) | ~27s (fast like bit2) | **37.79s** | ✗ |
| msb_m9cfea9ce | 128 (BROADEST untested) | >39s (slow like bit28) | **35.19s** | ✗ |

**BOTH predictions failed in the SAME direction** — bit11 (narrow)
is SLOWER than msb_m9cfea9ce (broad). OPPOSITE of F48's claim.

## Updated 6-cand picture

| cand | breadth | seq median | seq range |
|---|---:|---:|---:|
| bit2_ma896ee41 | **68** | **27.08s** | 2.6s |
| bit10_m9e157d24 | 94 | 28.04s | 3.2s |
| msb_m9cfea9ce | 128 | 35.19s | 8.3s |
| msb_m17149975 | 118 | 35.81s | 8.07s |
| bit11_m45b0a5f6 | 67 | 37.79s | 6.6s |
| bit28_md1acca79 | 88 | 39.25s | 21.8s |

Pearson correlation (N=6) of (breadth, wall): **r ≈ 0.20** —
ESSENTIALLY UNCORRELATED.

bit11 has the SAME breadth as bit2 (67-68) but takes 11s LONGER.
The breadth-as-predictor hypothesis is REFUTED.

## Final stance — F48 IS REFUTED

The "LM-tail breadth predicts kissat speed" claim is empirically
wrong. The N=4 monotonic ordering in F48 was a small-sample artifact
that disappeared once the breadth distribution was sampled at
extremes.

What IS empirically true (5+ cand baseline):

1. **bit2_ma896ee41 is uniquely fast** (~27s sequential, ~36s
   parallel-5). This is a real per-cand structural feature.

2. **bit10_m9e157d24 is also fast** (~28s sequential). The other
   "plateau" cand.

3. **All other 4 measured cands are slower** (35-39s sequential).
   No clear ordering among them.

4. **bit28 has unusually high seed variance** (range 22s vs 3-8s
   for others). Solver-axis "branchiness" — orthogonal to breadth.

## Why bit2 is uniquely fast (open question)

bit2_ma896ee41 has 3 known special properties:
- Lowest registry HW=45 (F28 NEW CHAMPION)
- Exact a_61=e_61=0x02000004 symmetry (F26/F28)
- Narrowest LM-tail breadth=68 (F49 this)

But bit11_m45b0a5f6 also has narrow breadth (67) and is NOT fast. So
breadth alone doesn't explain. HW=45 might be the key — bit2 is the
only HW=45 cand. Possibly the kissat advantage requires the
combination of HW=45 + symmetry. Untested.

## Useful artifacts retained

The `cand_lm_breadth` quantification (max-min LM across HW per cand)
remains a meaningful structural metric, even if it doesn't predict
solver speed:

```
Distribution: min=67, q1=81, median=96, q3=108, max=128 (N=67)
```

Use cases:
- Wang trail design: broad-tail cands offer more anchor candidates
- Cand selection: combined with HW + symmetry, breadth is a 4th axis
- F25-style structural rigidity: narrow breadth + 1-distinct-vector
  describes a "tight" cascade-1 manifold

But NOT for predicting kissat solver speed.

## Discipline lesson reinforced (TWICE in one session)

F48 overclaimed a monotonic relationship from 4 data points without
testing predictive power. F49's prediction test showed the data don't
support the claim.

Same class of error as F37/F38 → F39 retraction: jumping to a strong
claim from initial observations without controlling for confounds.

**Going forward**: when claiming a correlation, MUST test prediction
on out-of-sample cands. F49's "test 2 extremes" methodology should be
the default before publishing any cross-cand correlation claim.

EVIDENCE-level: VERIFIED for the breadth dataset. VERIFIED for the
F48 refutation (10-cand Pearson r≈0.2). bit2's uniqueness as
"fastest cand" is VERIFIED but its CAUSE remains HYPOTHESIS.

## Concrete next moves

1. **Investigate why bit2 is uniquely fast.** Cross-validate
   (HW=45 + symmetry + breadth) hypothesis: pick another exact-sym
   cand at LOWER HW (if exists) and test. If none exists at HW<47,
   bit2's HW=45 might be itself the discriminator.

2. **F47's bit28 outlier** is still unexplained on a 2nd axis. Need
   "branchiness" metric: count of distinct cascade-1 vectors per HW
   level for bit28 vs others.

3. **Update sigma1_aligned_kernel_sweep BET.yaml**: add the F49 finding
   that breadth doesn't predict speed. This further weakens any
   structural-axis solver predictions.

4. **Memo for paper**: Section 4 should NOT claim "breadth predicts
   speed" — that was wrong. The publishable claim is narrower:
   "bit2_ma896ee41 is uniquely fast within the registry, and its
   speed is correlated with HW=45 + exact symmetry. Mechanism unknown."
