# F246: bit19 chunk 17 is coverage-only
**2026-04-28**

## Summary

F246 continues bit19 fixture-local size-5 candidate discovery at
`--start-index 1088`.

```
Chunk:        17
Start index:  1088
Limit:        64
Best mask:    0,5,8,11,13
Best score:   92
Msg diff HW:  79
```

The current F135-basin bit19 floor remains `0,1,3,8,9` at score 87. This
chunk does not meet the score-89 threshold for immediate 8x50k continuation.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 1088 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F246_bit19_fullpool_size5_chunk0017_64x3x4k.json
```

Runtime was 113.356 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,5,8,11,13` | 92 | 79 | 51 |
| 2 | `0,5,9,10,14` | 94 | 62 | 53 |
| 3 | `0,5,8,11,15` | 94 | 68 | 53 |
| 4 | `0,5,9,10,15` | 95 | 73 | 53 |
| 5 | `0,5,11,13,14` | 95 | 74 | 51 |
| 6 | `0,5,8,10,12` | 96 | 52 | 53 |
| 7 | `0,5,11,13,15` | 96 | 59 | 53 |
| 8 | `0,5,7,14,15` | 96 | 71 | 53 |
| 9 | `0,5,8,10,11` | 96 | 76 | 53 |
| 10 | `0,5,10,11,13` | 96 | 78 | 53 |
| 11 | `0,5,10,12,15` | 96 | 84 | 53 |
| 12 | `0,5,11,12,15` | 97 | 44 | 53 |

## Interpretation

Chunk 17 is coverage only. It adds no candidate close enough for continuation.
Next unclaimed Yale-side chunk starts at `--start-index 1152`.
