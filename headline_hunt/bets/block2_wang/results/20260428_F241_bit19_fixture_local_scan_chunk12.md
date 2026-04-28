# F241: bit19 chunk 12 is negative
**2026-04-28**

## Summary

F241 continues bit19 fixture-local size-5 candidate discovery at
`--start-index 768`.

```
Chunk:        12
Start index:  768
Limit:        64
Best mask:    0,3,8,10,11
Best score:   93
Msg diff HW:  82
```

The current F135-basin bit19 floor remains `0,1,3,8,9` at score 87. This
chunk is not continuation-worthy under the score-89 follow-up threshold.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 768 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F241_bit19_fullpool_size5_chunk0012_64x3x4k.json
```

Runtime was 112.856 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,3,8,10,11` | 93 | 82 | 53 |
| 2 | `0,3,7,10,14` | 94 | 78 | 53 |
| 3 | `0,3,7,9,11` | 95 | 58 | 52 |
| 4 | `0,3,8,10,13` | 95 | 61 | 53 |
| 5 | `0,3,7,8,10` | 95 | 70 | 53 |
| 6 | `0,3,6,12,13` | 95 | 80 | 52 |
| 7 | `0,3,7,8,12` | 95 | 90 | 52 |
| 8 | `0,3,8,11,13` | 96 | 65 | 52 |
| 9 | `0,3,6,11,12` | 96 | 80 | 52 |
| 10 | `0,3,7,11,13` | 96 | 80 | 52 |
| 11 | `0,3,7,11,12` | 97 | 42 | 52 |
| 12 | `0,3,7,12,13` | 97 | 73 | 52 |

## Interpretation

Chunk 12 adds coverage only. The chunk's best mask includes the `3,8`
substructure but does not approach the F135-basin result. Next unclaimed
Yale-side chunk starts at `--start-index 832`.
