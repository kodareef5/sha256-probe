# F152: Refined overlap metric per yale's F128 feedback — 4-channel-coverage prediction

**2026-04-28**

## Acknowledgment

Yale's F128 tested F150's overlap-density prediction empirically and
falsified the simple form. Best F150 top-10 score: 96 (vs yale's
empirical 86). Pure expansion-overlap-density is NOT enough.

Yale identified the next-level features:
1. Total expansion overlap density
2. **Concentration**: max feeders into the same early schedule word
3. **Channel pattern**: direct vs σ_0 vs σ_1 vs W[i-7]

This memo computes the refined metric and identifies a SHARPER
prediction yale's F128 implicitly pointed at.

## Refined composite metric

For each size-5 subset of {0..15}, compute:

```
composite = 2.0 * early_max_feeders  (max feeders into W[16..22])
          + 1.0 * channel_diversity   (channels active at top overlap target)
          + 0.3 * extra_feeds         (F150's metric, downweighted)
```

Weighting reflects yale's F128 statement that concentration matters
more than raw density.

## Yale's empirical winner under refined metric

```
{0, 1, 2, 8, 9}:
  composite = 10.20
  extra_feeds = 4
  max_feeders = 3 at W[16] (W[0] direct_t16, W[1] σ_0, W[9] direct_t7)
  early_max_feeders = 3
  channel_diversity = 3 (direct, σ_0, direct_t7)
  Missing channel: σ_1
```

Yale's rank under refined metric: **134 of 4368** (vs F150's 192).
Better but still not top.

## The refined prediction — TOP-5 4-CHANNEL CANDIDATES

5 size-5 subsets achieve **early_max_feeders=4 AND channel_diversity=4**:

| Subset | Composite | extra | max | early_max | channels |
|---|---|---|---|---|---|
| **(0, 1, 9, 10, 14)** | 13.50 | 5 | 4 | 4 | 4 |
| (0, 1, 9, 14, 15) | 13.50 | 5 | 4 | 4 | 4 |
| (1, 2, 9, 10, 15) | 13.50 | 5 | 4 | 4 | 4 |
| (1, 2, 10, 11, 15) | 13.50 | 5 | 4 | 4 | 4 |
| (1, 2, 10, 14, 15) | 13.50 | 5 | 4 | 4 | 4 |

These have ALL 4 SHA-256 expansion channels active simultaneously at
W[16]:
- direct_t16 (i-16 offset)
- σ_0 (i-15 offset)
- direct_t7 (i-7 offset)
- σ_1 (i-2 offset)

Yale's {0,1,2,8,9} has 3 of 4 channels at W[16]; the missing σ_1 may
explain why yale's score-86 minimum is locally bound — the σ_1 channel
provides a 4th-bit-flip degree of freedom yale's local search can't
generate from the other channels.

## Concrete recommendation for yale's F129+

Test the 5 4-channel candidates with yale's F111 strict-active-words
scan. Estimated compute: 5 × 5 min = ~25 min.

```bash
for SUBSET in "0,1,9,10,14" "0,1,9,14,15" "1,2,9,10,15" \
              "1,2,10,11,15" "1,2,10,14,15"; do
  PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
    headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
    --pool $SUBSET --sizes 5 --restarts 3 --iterations 4000 \
    --require-all-used \
    --out-json /tmp/bit3_${SUBSET//,/_}_4channel.json
done
```

## Predicted outcomes

If 4-channel-coverage hypothesis holds:
- Score floor < 86 on at least one of the 5 candidates
- The "missing σ_1 channel" insight is the structural key

If not:
- yale's score-86 is bound by additional features (e.g., specific
  bit-positions, specific σ_0/σ_1 offset structure within W's)
- The refined metric needs further refinement (e.g., add 4th feature)

Either outcome is informative.

## Connection to today's chain

- F150 (macbook): raw expansion-overlap-density prediction (10 subsets)
- F128 (yale): tested F150, falsified simple form, identified
  refinements
- F152 (this memo, macbook): refined metric incorporating yale's
  feedback; predicts 5 4-channel candidates

This is the kind of cross-bet hypothesis-test-refinement loop that
multi-machine fleet coordination enables. Yale tested in 30 min; macbook
refined in 10 min; next iteration ready.

## Discipline

- 0 SAT compute
- 0 solver runs
- Pure-thought refinement on yale's F128 feedback
- Probe at `/tmp/refined_overlap_metric.py` (one-shot, derivable)

## Status

Refined prediction ready for yale's next iteration. The 5 4-channel-
coverage candidates are the highest-leverage next test. If any score
< 86, the concentration+channel-diversity composite metric is
empirically validated. If not, the framework needs further refinement
toward yale's specific {0,1,2,8,9} signature.
