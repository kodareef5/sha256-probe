# F244: bit19 chunk 15 is coverage-only
**2026-04-28**

## Summary

F244 continues bit19 fixture-local size-5 candidate discovery at
`--start-index 960`.

```
Chunk:        15
Start index:  960
Limit:        64
Best mask:    0,4,9,10,14
Best score:   92
Msg diff HW:  66
```

The current F135-basin bit19 floor remains `0,1,3,8,9` at score 87. This
chunk does not meet the score-89 threshold for immediate 8x50k continuation.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 960 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F244_bit19_fullpool_size5_chunk0015_64x3x4k.json
```

Runtime was 121.956 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Message words | Schedule words |
|---:|---|---:|---:|---:|---:|
| 1 | `0,4,9,10,14` | 92 | 66 | 5 | 53 |
| 2 | `0,4,8,9,10` | 94 | 79 | 5 | 53 |
| 3 | `0,4,8,11,12` | 95 | 78 | 5 | 52 |
| 4 | `0,4,10,13,14` | 95 | 88 | 5 | 53 |
| 5 | `0,4,9,12,14` | 96 | 81 | 5 | 52 |
| 6 | `0,4,8,10,15` | 96 | 88 | 5 | 53 |
| 7 | `0,4,8,11,13` | 96 | 91 | 5 | 52 |
| 8 | `0,4,9,12,13` | 97 | 33 | 4 | 51 |
| 9 | `0,4,7,11,15` | 97 | 53 | 5 | 53 |
| 10 | `0,4,7,10,11` | 97 | 63 | 5 | 53 |
| 11 | `0,4,8,12,13` | 97 | 66 | 5 | 52 |
| 12 | `0,4,10,11,12` | 97 | 71 | 5 | 53 |

## Interpretation

Chunk 15 adds coverage only. It has one score-92 mask and no score-89 or
better candidate. Next unclaimed Yale-side chunk starts at `--start-index 1024`.
