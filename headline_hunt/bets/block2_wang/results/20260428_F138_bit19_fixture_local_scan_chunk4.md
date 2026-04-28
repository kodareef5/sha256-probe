# F138: fifth bit19 scan slice is negative
**2026-04-28**

## Summary

F138 continues the bit19 fixture-local size-5 scan at `--start-index 256`.
This slice did not improve the current bit19 floor.

```
Chunk:        start 256, limit 64
Best mask:    0,1,6,8,14
Best score:   93
Msg diff HW:  68
```

The current bit19 best remains F135's `0,1,3,8,9` at score 87.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 256 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used --top 16 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F138_bit19_fullpool_size5_chunk0256_64x3x4k.json
```

Runtime was 116.101 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,1,6,8,14` | 93 | 68 | 53 |
| 2 | `0,1,7,8,14` | 94 | 64 | 53 |
| 3 | `0,1,6,11,13` | 94 | 74 | 53 |
| 4 | `0,1,7,13,15` | 95 | 77 | 53 |
| 5 | `0,1,8,9,10` | 96 | 50 | 53 |
| 6 | `0,1,6,10,11` | 96 | 56 | 53 |
| 7 | `0,1,8,10,14` | 96 | 74 | 53 |
| 8 | `0,1,6,10,12` | 96 | 77 | 53 |
| 9 | `0,1,7,12,14` | 96 | 79 | 53 |
| 10 | `0,1,7,8,15` | 97 | 63 | 53 |

Pareto frontier:

```
score 93, msgHW 68, active 0,1,6,8,14
score 94, msgHW 64, active 0,1,7,8,14
score 96, msgHW 50, active 0,1,8,9,10
score 98, msgHW 24, active 0,1,8,11,12
```

## Interpretation

This slice is coverage only. The best-by-chunk table through chunk 4 is:

| Chunk | Start index | Best score | Best active words |
|---:|---:|---:|---|
| F134 | 0 | 90 | `0,1,2,7,15` |
| F135 | 64 | 87 | `0,1,3,8,9` |
| F136 | 128 | 91 | `0,1,3,12,15` |
| F137 | 192 | 91 | `0,1,5,10,12` |
| F138 | 256 | 93 | `0,1,6,8,14` |

Next scan slice starts at `--start-index 320`.
