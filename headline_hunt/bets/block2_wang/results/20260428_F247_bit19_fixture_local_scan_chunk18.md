# F247: bit19 chunk 18 is weak coverage
**2026-04-28**

## Summary

F247 continues bit19 fixture-local size-5 candidate discovery at
`--start-index 1152`.

```
Chunk:        18
Start index:  1152
Limit:        64
Best score:   95
Best masks:   several tied at 95
```

The current F135-basin bit19 floor remains `0,1,3,8,9` at score 87. This
chunk is not continuation-worthy.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 1152 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F247_bit19_fullpool_size5_chunk0018_64x3x4k.json
```

Runtime was 112.232 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,6,7,9,11` | 95 | 42 | 51 |
| 2 | `0,6,7,8,10` | 95 | 46 | 53 |
| 3 | `0,6,8,10,14` | 95 | 63 | 53 |
| 4 | `0,6,7,8,15` | 95 | 70 | 53 |
| 5 | `0,6,8,10,15` | 95 | 92 | 53 |
| 6 | `0,6,7,8,13` | 96 | 65 | 51 |
| 7 | `0,6,8,13,14` | 96 | 65 | 51 |
| 8 | `0,6,7,12,13` | 96 | 67 | 52 |
| 9 | `0,6,7,12,15` | 96 | 67 | 53 |
| 10 | `0,6,7,9,14` | 96 | 69 | 51 |
| 11 | `0,6,7,8,12` | 96 | 75 | 52 |
| 12 | `0,6,9,10,15` | 96 | 80 | 53 |

## Interpretation

Chunk 18 is one of the weakest covered slices so far. It contributes negative
coverage only. Next unclaimed Yale-side chunk starts at `--start-index 1216`.
