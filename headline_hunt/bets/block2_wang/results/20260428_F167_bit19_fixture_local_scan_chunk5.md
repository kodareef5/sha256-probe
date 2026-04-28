# F167: sixth bit19 scan slice is negative
**2026-04-28**

## Summary

F167 continues the bit19 fixture-local size-5 scan at `--start-index 320`.
This slice did not improve the current bit19 floor.

```
Chunk:        5
Start index:  320
Limit:        64
Best mask:    0,1,9,10,14
Best score:   93
Msg diff HW:  75
```

The current bit19 best remains F135/F159's `0,1,3,8,9` at score 87.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 320 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F167_bit19_fullpool_size5_chunk0005_64x3x4k.json
```

Runtime was 121.308 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,1,9,10,14` | 93 | 75 | 53 |
| 2 | `0,1,12,13,14` | 94 | 56 | 53 |
| 3 | `0,1,8,12,15` | 94 | 81 | 53 |
| 4 | `0,1,9,11,13` | 96 | 58 | 53 |
| 5 | `0,2,3,4,15` | 96 | 67 | 53 |
| 6 | `0,1,10,13,15` | 96 | 77 | 53 |
| 7 | `0,1,9,11,14` | 97 | 46 | 53 |
| 8 | `0,2,3,5,14` | 97 | 49 | 53 |
| 9 | `0,1,10,12,15` | 97 | 65 | 53 |
| 10 | `0,2,3,4,11` | 97 | 73 | 53 |
| 11 | `0,1,9,14,15` | 97 | 78 | 53 |
| 12 | `0,1,10,11,15` | 97 | 82 | 53 |

## Interpretation

This slice is coverage only. The best-by-yale-chunk table through chunk 5 is:

| Chunk | Start index | Best score | Best active words |
|---:|---:|---:|---|
| F134 | 0 | 90 | `0,1,2,7,15` |
| F135/F159 | 64 | 87 | `0,1,3,8,9` |
| F136 | 128 | 91 | `0,1,3,12,15` |
| F137 | 192 | 91 | `0,1,5,10,12` |
| F138 | 256 | 93 | `0,1,6,8,14` |
| F167 | 320 | 93 | `0,1,9,10,14` |

The chunk-5 best still uses the early pair `0,1`, but lacks the chunk-1
`0,1,3` pattern that produced the bit19 floor. Next scan slice starts at
`--start-index 384`.
