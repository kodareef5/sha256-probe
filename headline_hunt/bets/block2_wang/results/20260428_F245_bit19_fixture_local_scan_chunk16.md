# F245: bit19 chunk 16 is negative
**2026-04-28**

## Summary

F245 continues bit19 fixture-local size-5 candidate discovery at
`--start-index 1024`.

```
Chunk:        16
Start index:  1024
Limit:        64
Best mask:    0,5,6,10,15
Best score:   93
Msg diff HW:  82
```

The current F135-basin bit19 floor remains `0,1,3,8,9` at score 87. This
chunk is not continuation-worthy.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 1024 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F245_bit19_fullpool_size5_chunk0016_64x3x4k.json
```

Runtime was 115.481 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,5,6,10,15` | 93 | 82 | 53 |
| 2 | `0,5,6,8,10` | 94 | 56 | 53 |
| 3 | `0,5,6,10,14` | 94 | 78 | 53 |
| 4 | `0,5,7,9,10` | 95 | 59 | 53 |
| 5 | `0,5,7,8,10` | 95 | 75 | 53 |
| 6 | `0,5,6,7,11` | 96 | 75 | 51 |
| 7 | `0,5,7,8,11` | 96 | 79 | 51 |
| 8 | `0,4,11,14,15` | 96 | 85 | 53 |
| 9 | `0,5,6,10,11` | 97 | 60 | 53 |
| 10 | `0,5,6,7,14` | 97 | 73 | 51 |
| 11 | `0,5,6,7,10` | 97 | 77 | 53 |
| 12 | `0,5,7,8,12` | 97 | 85 | 52 |

## Interpretation

Chunk 16 is coverage only. It does not produce a score-89 or better candidate
for continuation. Next unclaimed Yale-side chunk starts at `--start-index 1088`.
