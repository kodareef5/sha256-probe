# F242: bit19 chunk 13 is coverage-only
**2026-04-28**

## Summary

F242 continues bit19 fixture-local size-5 candidate discovery at
`--start-index 832`.

```
Chunk:        13
Start index:  832
Limit:        64
Best masks:   0,3,9,10,13 and 0,4,5,7,11
Best score:   91
```

The current F135-basin bit19 floor remains `0,1,3,8,9` at score 87. This
chunk does not meet the score-89 threshold for immediate 8x50k continuation.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 832 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F242_bit19_fullpool_size5_chunk0013_64x3x4k.json
```

Runtime was 122.189 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,3,9,10,13` | 91 | 74 | 53 |
| 2 | `0,4,5,7,11` | 91 | 78 | 52 |
| 3 | `0,3,11,14,15` | 94 | 42 | 53 |
| 4 | `0,3,9,10,15` | 94 | 83 | 53 |
| 5 | `0,4,5,6,9` | 95 | 42 | 52 |
| 6 | `0,3,9,11,12` | 95 | 47 | 52 |
| 7 | `0,3,13,14,15` | 95 | 80 | 53 |
| 8 | `0,3,8,13,14` | 96 | 50 | 52 |
| 9 | `0,3,12,13,15` | 96 | 62 | 53 |
| 10 | `0,4,5,9,10` | 96 | 67 | 53 |
| 11 | `0,3,9,12,14` | 96 | 78 | 52 |
| 12 | `0,4,5,6,8` | 96 | 81 | 52 |

## Interpretation

Chunk 13 is coverage only. Its two score-91 masks are not close enough to the
F135-basin floor to justify immediate continuation. Next unclaimed Yale-side
chunk starts at `--start-index 896`.
