# F150: Expansion-overlap-density prediction for yale's next active-word search

**2026-04-28**

## Summary

Cluster analysis of yale's 26 search artifacts shows score-86 hits
ALL come from active-word config {0,1,2,8,9}. Other configs plateau at
score 90-95. Yale empirically converged to {0,1,2,8,9}.

A pure-thought analysis of SHA-256 message expansion structure ranks
{0,1,2,8,9} at **rank 192 of 4368** size-5 subsets by expansion-overlap
density (top 4.4%). HIGHER-density subsets exist that yale hasn't
tested.

This memo identifies the top-10 size-5 subsets by expansion-overlap
density as candidates for yale's next round of active-word search.

## Method

For each size-5 subset of {0..15} message word positions, count
"extra downstream feeds" — number of W[i] (i ≥ 16) that receive ≥ 2
active-word inputs through the SHA-256 expansion recurrence:

  W[i] = σ_1(W[i-2]) + W[i-7] + σ_0(W[i-15]) + W[i-16]   (i ≥ 16)

A subset with high extra-feed count concentrates active-word influence
on fewer, more-coupled downstream W[i]. Hypothesis: more concentrated
expansion overlap = stronger structural coupling = potentially lower
absorber score floor in yale's local search.

## Results

Yale's {0,1,2,8,9}:
- Extra feeds: 4
- Overlap targets: 3 (W[16], W[17], W[24])
- W[16] has 3 active feeders (W[0] direct, W[1] σ_0, W[9] W[i-7])

**Top-10 size-5 subsets by expansion-overlap density (extra_feeds = 6)**:

| Subset | Overlap targets | Distinct targets |
|---|---|---|
| {1, 5, 13, 14, 15} | 6 | 9 |
| {1, 6, 13, 14, 15} | 6 | 9 |
| {1, 6, 9, 14, 15} | 5 | 9 |
| {1, 6, 10, 14, 15} | 5 | 9 |
| {1, 9, 10, 14, 15} | 4 | 10 |
| {0, 1, 6, 14, 15} | 5 | 7 |
| {1, 2, 6, 14, 15} | 5 | 8 |
| {1, 2, 9, 10, 11} | 5 | 7 |
| {1, 5, 6, 14, 15} | 5 | 8 |
| {1, 6, 7, 14, 15} | 5 | 8 |

All 10 have **6 extra feeds vs yale's 4** — 50% higher overlap density.

Common features:
- W[1] in all 10 (W[1] is heavily downstream-coupled via σ_0(W[i-15]) at
  i=16, direct at i=8 and i=17)
- W[14] and W[15] in 8 of 10 (late-position words that feed W[16-22] and
  later via σ_1 and direct channels)
- W[6] in 7 of 10 (W[6] feeds W[13] via W[i-7] AND W[21] via σ_1(W[i-2])
  at i=8)

## Concrete suggestion for yale

Try the top-10 expansion-overlap-density subsets in F111-style active
subset scan:

```bash
for SUBSET in "1,5,13,14,15" "1,6,13,14,15" "1,6,9,14,15" \
              "1,6,10,14,15" "0,1,6,14,15" "1,2,6,14,15"; do
  PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
    headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
    --pool $SUBSET --sizes 5 --restarts 3 --iterations 4000 --limit 80 \
    --out-json /tmp/bit3_${SUBSET//,/_}_subset_scan.json
done
```

~6 cands × ~5 minutes per scan = ~30 minutes total. Pure local search.

## Predicted outcomes

If the expansion-overlap-density hypothesis is correct, the top-10
subsets should produce score floors LOWER than yale's empirical 86
(perhaps 75-83 range).

If outcomes match: yale's heuristic has a STRUCTURAL UPGRADE — search
should be biased toward high-expansion-overlap subsets.

If outcomes don't match: yale's 4-extra-feeds {0,1,2,8,9} captures
something specific that pure overlap density doesn't (maybe involving
the σ_0 vs σ_1 channel split, or specific Σ-bit-coverage of those
words).

Either outcome is informative.

## What yale's empirical winner has that overlap-density doesn't capture

Yale's {0,1,2,8,9} has overlap CONCENTRATION:
- W[16] has 3 active feeders (extra-extra crowded)
- 3 distinct overlap targets

Top-density subsets like {1,5,13,14,15} have 6 overlap targets (more
spread). Yale's might exploit CONCENTRATED coupling vs DISTRIBUTED
coupling. These are different structural signals.

A complementary metric: max-feeder-count per target (concentration vs
spread). Yale's max=3, others have max=2-3. Could be relevant for
absorption physics.

## Connection to today's chain

- F143/F146/F148/F149: structurally-distinguished CAND slate
  (different cands)
- F150 (this memo): structurally-distinguished WORD-SUBSET slate
  (different active-word configs)

These are independent axes of structural exploitation. Yale could
test BOTH:
- Cand axis: bit28 / bit4 / bit25 / msb_m9cfea9ce fixtures (F148/F149)
- Word-subset axis: top-10 high-overlap-density configs (F150)

Combined search space: 5 cands × 6 subsets = 30 experiments at ~5 min
each = ~2.5 hours yale-side compute.

## Discipline

- 0 SAT compute
- Pure-thought analysis on yale's existing artifacts + SHA-256 spec
- Probe at `april28_explore/principles/items/probe_message_word_expansion_overlap.py`

## Status

Algebraic prediction of high-leverage active-word subsets ready for
yale's next iteration. The principles framework now has a concrete
WORD-LEVEL prediction (this memo) complementary to the BIT-LEVEL
prediction (synthesis 3 KKL × Σ-Steiner).
