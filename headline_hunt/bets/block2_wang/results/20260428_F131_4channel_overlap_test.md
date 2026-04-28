# F131: four-channel W16 overlap prediction does not beat the score-86 lane
**2026-04-28**

## Summary

F152 refined the failed F150/F128 overlap-density hypothesis into a sharper
prediction: size-5 masks with all four SHA-256 expansion channels active at
the same early target should beat the current absorber floor.

F131 tested the exact five F152 four-channel candidates on the bit3 fixture
using the same strict 3 x 4k active-subset screen.

Result:

```
Best F152 four-channel score: 96
Current empirical best score: 86
```

The four-channel W16 coverage hypothesis did not validate at this budget.

## Method

Each F152 candidate was scanned as a single strict active mask:

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --pool SUBSET --sizes 5 \
  --restarts 3 --iterations 4000 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F131_4channel_SUBSET_3x4k.json
```

## Results

| F152 candidate | Best score | Msg diff HW | Schedule words | Artifact |
|---|---:|---:|---:|---|
| `0,1,9,10,14` | 102 | 72 | 53 | `20260428_F131_4channel_0_1_9_10_14_3x4k.json` |
| `0,1,9,14,15` | 100 | 67 | 53 | `20260428_F131_4channel_0_1_9_14_15_3x4k.json` |
| `1,2,9,10,15` | 100 | 60 | 53 | `20260428_F131_4channel_1_2_9_10_15_3x4k.json` |
| `1,2,10,11,15` | 96 | 67 | 53 | `20260428_F131_4channel_1_2_10_11_15_3x4k.json` |
| `1,2,10,14,15` | 100 | 77 | 53 | `20260428_F131_4channel_1_2_10_14_15_3x4k.json` |

Pareto frontier:

```
score 96, msgHW 67, active 1,2,10,11,15
score 100, msgHW 60, active 1,2,9,10,15
```

## Interpretation

All four one-hop expansion channels meeting at W16 is not sufficient for a
good block-2 absorber on this bit3 trail. This reinforces the F129/F130
reading: the old `0,1,2,8,9` winner is probably not explained by generic
overlap geometry alone.

The specific missing feature remains the word-8 to W24 phase. The best new
neighbor so far is still F130's `0,1,2,9,15` continuation at score 91, which
shares `0,1,2,9` with the winner but lacks word 8.

Next useful search should bias toward masks that preserve the W16/W17
structure of `0,1,2,8,9` while varying only the W24 contributor, instead of
chasing more W16 channel diversity.
