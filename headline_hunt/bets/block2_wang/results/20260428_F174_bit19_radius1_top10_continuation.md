# F174: bit19 radius-1 top-10 continuation stays above 87
**2026-04-28**

## Summary

F174 follows macbook's F172 budget-calibration note: low-budget radius-1 scans
can miss deeper local minima, so continue the best alternate radius-1 masks at
8 restarts x 50k iterations.

Result: no alternate radius-1 mask reaches the current bit19 floor. Best
alternate score is 91.

```
Known bit19 floor:  87 on 0,1,3,8,9
F174 best alternate: 91 on 1,2,3,8,9 and 0,2,5,8,9
```

## Slate

Input mask list:

```
headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F174_bit19_radius1_top10_continuation_masks.txt
```

The slate contains F173 seeded-pass ranks 2-10 plus the F172 independent-pass
winner, excluding known winner `0,1,3,8,9`.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --explicit-masks headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F174_bit19_radius1_top10_continuation_masks.txt \
  --restarts 8 --iterations 50000 --seed 8101 \
  --require-all-used \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F135_bit19_fullpool_size5_chunk0064_64x3x4k.json \
  --top 10 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F174_bit19_radius1_top10_from_F135_10x8x50k.json
```

Runtime was 595.587 seconds for 10 masks.

## Results

| Rank | Active words | Score | Msg diff HW |
|---:|---|---:|---:|
| 1 | `1,2,3,8,9` | 91 | 58 |
| 2 | `0,2,5,8,9` | 91 | 89 |
| 3 | `0,1,8,9,10` | 92 | 73 |
| 4 | `0,1,8,9,14` | 92 | 76 |
| 5 | `0,1,2,3,8` | 93 | 87 |
| 6 | `0,1,2,7,8` | 93 | 89 |
| 7 | `0,1,8,9,15` | 94 | 57 |
| 8 | `0,1,7,8,9` | 94 | 76 |
| 9 | `0,1,2,8,11` | 94 | 86 |
| 10 | `0,1,2,7,9` | 95 | 78 |

## Interpretation

This closes the cheap continuation path for the radius-1 shell. The top
alternates improve under higher budget, but not enough to threaten the known
score-87 mask. At this point `0,1,3,8,9` looks genuinely special inside the
radius-1 family, not merely lucky under the 3x4000 chunk pass.

Remaining uncertainty is only the expensive version of the hypothesis: all 55
radius-1 masks at 8x50k. Given F174, that is lower priority than continuing
global chunk coverage or testing radius-2/family-guided moves around
`0,1,3,8,9`.
