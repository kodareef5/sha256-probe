# F136: third bit19 scan slice is negative
**2026-04-28**

## Summary

F136 continues the fixture-local bit19 size-5 scan at `--start-index 128`.
Unlike F134 and F135, this slice did not improve the bit19 floor.

```
Chunk:        start 128, limit 64
Best mask:    0,1,3,12,15
Best score:   91
Msg diff HW:  76
```

The current bit19 best remains F135's `0,1,3,8,9` at score 87.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 128 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used --top 16 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F136_bit19_fullpool_size5_chunk0128_64x3x4k.json
```

Runtime was 122.619 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,1,3,12,15` | 91 | 76 | 53 |
| 2 | `0,1,4,7,9` | 94 | 81 | 53 |
| 3 | `0,1,4,5,11` | 95 | 61 | 53 |
| 4 | `0,1,4,8,13` | 95 | 75 | 53 |
| 5 | `0,1,4,7,12` | 95 | 80 | 53 |
| 6 | `0,1,4,5,9` | 96 | 64 | 53 |
| 7 | `0,1,3,12,13` | 96 | 71 | 53 |
| 8 | `0,1,4,6,15` | 96 | 80 | 53 |
| 9 | `0,1,4,6,13` | 97 | 65 | 53 |
| 10 | `0,1,4,9,10` | 97 | 66 | 53 |

Pareto frontier:

```
score 91, msgHW 76, active 0,1,3,12,15
score 95, msgHW 61, active 0,1,4,5,11
score 98, msgHW 58, active 0,1,4,6,9
score 99, msgHW 47, active 0,1,3,9,15
score 101, msgHW 16, actual active 0,3,14
```

## Interpretation

This slice is useful mostly as coverage. It shows the bit19 scan can have
ordinary weak regions, and it does not change the current best result:

```
F135 bit19 best: 0,1,3,8,9 at score 87
```

Next scan slice starts at `--start-index 192`.
