# F239: bit19 chunk 10 is coverage-only
**2026-04-28**

## Summary

F239 continues bit19 fixture-local size-5 candidate discovery at
`--start-index 640`.

```
Chunk:        10
Start index:  640
Limit:        64
Best masks:   0,3,4,10,13 and 0,3,4,10,15
Best score:   91
```

The current verified bit19 floor remains F135/F159/F173/F174's `0,1,3,8,9`
at score 87. This chunk does not meet the score-89 threshold for immediate
8x50k continuation.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 640 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F239_bit19_fullpool_size5_chunk0010_64x3x4k.json
```

Runtime was 124.962 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,3,4,10,13` | 91 | 62 | 53 |
| 2 | `0,3,4,10,15` | 91 | 80 | 53 |
| 3 | `0,3,4,9,10` | 92 | 55 | 53 |
| 4 | `0,2,11,14,15` | 94 | 70 | 53 |
| 5 | `0,3,4,6,13` | 95 | 61 | 52 |
| 6 | `0,3,4,9,13` | 95 | 63 | 52 |
| 7 | `0,3,4,7,11` | 95 | 64 | 52 |
| 8 | `0,3,4,5,11` | 95 | 82 | 52 |
| 9 | `0,3,4,6,9` | 96 | 65 | 52 |
| 10 | `0,3,4,7,12` | 96 | 72 | 52 |
| 11 | `0,3,4,5,12` | 96 | 79 | 52 |
| 12 | `0,3,4,11,12` | 96 | 83 | 52 |

## Interpretation

Chunk 10 is coverage-only. The best masks share the `0,3,4,10,*` family,
but neither approaches the verified bit19 floor. Next unclaimed Yale-side
chunk starts at `--start-index 704`.
