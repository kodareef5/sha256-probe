# F243: bit19 chunk 14 is negative
**2026-04-28**

## Summary

F243 continues bit19 fixture-local size-5 candidate discovery at
`--start-index 896`.

```
Chunk:        14
Start index:  896
Limit:        64
Best masks:   0,4,5,9,13 and 0,4,6,12,13
Best score:   94
```

The current F135-basin bit19 floor remains `0,1,3,8,9` at score 87. This
chunk is not continuation-worthy.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 896 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F243_bit19_fullpool_size5_chunk0014_64x3x4k.json
```

Runtime was 115.664 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,4,5,9,13` | 94 | 56 | 52 |
| 2 | `0,4,6,12,13` | 94 | 85 | 52 |
| 3 | `0,4,6,11,12` | 95 | 61 | 52 |
| 4 | `0,4,5,12,13` | 95 | 64 | 52 |
| 5 | `0,4,6,9,13` | 96 | 56 | 52 |
| 6 | `0,4,7,8,12` | 96 | 70 | 52 |
| 7 | `0,4,6,8,13` | 96 | 73 | 52 |
| 8 | `0,4,5,10,12` | 96 | 75 | 53 |
| 9 | `0,4,5,10,11` | 97 | 55 | 53 |
| 10 | `0,4,6,8,11` | 97 | 66 | 52 |
| 11 | `0,4,6,9,15` | 97 | 75 | 53 |
| 12 | `0,4,6,10,13` | 97 | 76 | 53 |

## Interpretation

Chunk 14 is one of the weaker Yale-side slices so far. It adds coverage only.
Next unclaimed Yale-side chunk starts at `--start-index 960`.
