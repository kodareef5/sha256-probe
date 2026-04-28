# F137: fourth bit19 scan slice is negative
**2026-04-28**

## Summary

F137 continues the bit19 fixture-local size-5 scan at `--start-index 192`.
This slice did not improve the current bit19 floor.

```
Chunk:        start 192, limit 64
Best mask:    0,1,5,10,12
Best score:   91
Msg diff HW:  73
```

The current bit19 best remains F135's `0,1,3,8,9` at score 87.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 192 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used --top 16 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F137_bit19_fullpool_size5_chunk0192_64x3x4k.json
```

Runtime was 114.244 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,1,5,10,12` | 91 | 73 | 53 |
| 2 | `0,1,5,7,12` | 93 | 71 | 53 |
| 3 | `0,1,5,8,9` | 93 | 74 | 53 |
| 4 | `0,1,5,7,15` | 94 | 85 | 53 |
| 5 | `0,1,6,8,11` | 95 | 70 | 53 |
| 6 | `0,1,5,9,12` | 95 | 80 | 53 |
| 7 | `0,1,6,7,9` | 96 | 52 | 53 |
| 8 | `0,1,6,7,8` | 96 | 77 | 53 |
| 9 | `0,1,6,7,12` | 96 | 79 | 53 |
| 10 | `0,1,5,8,11` | 97 | 54 | 53 |

Pareto frontier:

```
score 91, msgHW 73, active 0,1,5,10,12
score 93, msgHW 71, active 0,1,5,7,12
score 95, msgHW 70, active 0,1,6,8,11
score 96, msgHW 52, active 0,1,6,7,9
score 100, msgHW 43, active 0,1,5,7,13
```

## Interpretation

This is coverage only. The bit19 scan has now covered 256 of 4,368 size-5
masks. The best score by chunk is:

| Chunk | Start index | Best score | Best active words |
|---:|---:|---:|---|
| F134 | 0 | 90 | `0,1,2,7,15` |
| F135 | 64 | 87 | `0,1,3,8,9` |
| F136 | 128 | 91 | `0,1,3,12,15` |
| F137 | 192 | 91 | `0,1,5,10,12` |

Next scan slice starts at `--start-index 256`.
