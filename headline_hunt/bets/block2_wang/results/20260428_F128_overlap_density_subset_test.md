# F128: overlap-density subset prediction misses the current absorber floor
**2026-04-28**

## Summary

F150 predicted that the top size-5 message-word subsets by SHA-256 message
expansion overlap density might outperform the empirical `0,1,2,8,9`
absorber lane. F128 tested that prediction directly on the bit3 fixture with
strict active-word scans.

The result is a useful negative control:

```
Best F150-predicted subset score: 96
Best empirical 0,1,2,8,9 score:   86
```

None of the top ten high-overlap-density subsets beat or approached the
existing score-86 lane at this budget. Pure expansion-overlap density is not
enough to explain the current best absorber.

## Method

Each F150 top-10 subset was scanned as a single strict size-5 active mask:

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --pool SUBSET --sizes 5 \
  --restarts 3 --iterations 4000 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F128_overlap_SUBSET_3x4k.json
```

The scan used seeds 2001 through 2010 in F150 rank order. The
`--require-all-used` flag matters here: it prevents an inherited smaller mask
from being credited to a five-word subset.

## Results

| F150 rank | Active words | Best score | Msg diff HW | Schedule words | Artifact |
|---:|---|---:|---:|---:|---|
| 1 | `1,5,13,14,15` | 96 | 97 | 53 | `20260428_F128_overlap_1_5_13_14_15_3x4k.json` |
| 2 | `1,6,13,14,15` | 100 | 84 | 53 | `20260428_F128_overlap_1_6_13_14_15_3x4k.json` |
| 3 | `1,6,9,14,15` | 100 | 68 | 53 | `20260428_F128_overlap_1_6_9_14_15_3x4k.json` |
| 4 | `1,6,10,14,15` | 97 | 84 | 53 | `20260428_F128_overlap_1_6_10_14_15_3x4k.json` |
| 5 | `1,9,10,14,15` | 99 | 85 | 53 | `20260428_F128_overlap_1_9_10_14_15_3x4k.json` |
| 6 | `0,1,6,14,15` | 99 | 53 | 53 | `20260428_F128_overlap_0_1_6_14_15_3x4k.json` |
| 7 | `1,2,6,14,15` | 102 | 79 | 53 | `20260428_F128_overlap_1_2_6_14_15_3x4k.json` |
| 8 | `1,2,9,10,11` | 96 | 81 | 53 | `20260428_F128_overlap_1_2_9_10_11_3x4k.json` |
| 9 | `1,5,6,14,15` | 102 | 53 | 53 | `20260428_F128_overlap_1_5_6_14_15_3x4k.json` |
| 10 | `1,6,7,14,15` | 98 | 82 | 53 | `20260428_F128_overlap_1_6_7_14_15_3x4k.json` |

Aggregate analyzer output:

```
Loaded 10 unique runs from 10 file(s).
Best score: 96 at active 1,2,9,10,11 with msgHW 81.
Pareto frontier:
  score 96, msgHW 81, active 1,2,9,10,11
  score 99, msgHW 53, active 0,1,6,14,15
```

## Interpretation

This does not falsify message-expansion structure as a useful signal. It does
falsify the simple version of the hypothesis: "more extra downstream feeds is
better."

The current `0,1,2,8,9` lane has lower total overlap density than the F150
top-10, but it has a more concentrated overlap pattern around early expansion
rounds. That concentration appears more relevant than raw extra-feed count for
the bit3 block-2 absorber search.

The only useful byproduct here is the low message-diff point
`0,1,6,14,15`:

```
score 99, msgHW 53, schedule words 53
```

It is not competitive on target distance, but it gives another sparse
negative-control lane for later absorber-neighborhood probes.

## Next

The next structural ranking should combine at least three features:

1. Total expansion overlap density.
2. Concentration, especially max feeders into the same early schedule word.
3. Channel pattern, separating direct, `sigma0`, `sigma1`, and `i-7` feeds.

The practical search direction remains the empirical score-86
`0,1,2,8,9` lane unless a new fixture changes the active-word physics.
