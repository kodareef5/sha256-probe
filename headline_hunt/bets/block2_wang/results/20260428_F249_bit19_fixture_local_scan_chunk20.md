# F249: bit19 chunk 20 is coverage-only
**2026-04-28**

## Summary

F249 continues bit19 fixture-local size-5 candidate discovery at
`--start-index 1280`.

```
Chunk:        20
Start index:  1280
Limit:        64
Best mask:    0,8,10,12,15
Best score:   92
Msg diff HW:  69
```

The current F135-basin bit19 floor remains `0,1,3,8,9` at score 87. This
chunk does not meet the score-89 threshold for immediate 8x50k continuation.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 1280 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F249_bit19_fullpool_size5_chunk0020_64x3x4k.json
```

Runtime was 120.533 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,8,10,12,15` | 92 | 69 | 53 |
| 2 | `0,7,10,12,14` | 93 | 82 | 53 |
| 3 | `0,9,10,11,13` | 95 | 41 | 53 |
| 4 | `0,9,10,13,15` | 95 | 55 | 53 |
| 5 | `0,8,11,12,14` | 95 | 72 | 52 |
| 6 | `0,8,9,10,12` | 95 | 81 | 53 |
| 7 | `0,7,11,12,13` | 96 | 44 | 52 |
| 8 | `0,7,10,13,15` | 96 | 53 | 53 |
| 9 | `0,7,10,13,14` | 96 | 56 | 53 |
| 10 | `0,8,10,14,15` | 96 | 60 | 53 |
| 11 | `0,8,9,10,14` | 96 | 79 | 53 |
| 12 | `0,9,10,12,14` | 96 | 88 | 53 |

## Interpretation

Chunk 20 is coverage only. It does not produce a candidate close enough for
continuation. Next unclaimed Yale-side chunk starts at `--start-index 1344`.
