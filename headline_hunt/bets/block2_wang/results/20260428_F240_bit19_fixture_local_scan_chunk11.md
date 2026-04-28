# F240: bit19 chunk 11 is negative
**2026-04-28**

## Summary

F240 continues bit19 fixture-local size-5 candidate discovery at
`--start-index 704`.

```
Chunk:        11
Start index:  704
Limit:        64
Best mask:    0,3,6,7,14
Best score:   93
Msg diff HW:  65
```

The current F135-basin bit19 floor remains F135/F159/F173/F174's
`0,1,3,8,9` at score 87. Per F180/F206, that is not the robust random-init
floor; it is a narrow seeded-basin benchmark. This chunk is not
continuation-worthy under the current score-89 follow-up threshold.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 704 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F240_bit19_fullpool_size5_chunk0011_64x3x4k.json
```

Runtime was 113.124 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,3,6,7,14` | 93 | 65 | 52 |
| 2 | `0,3,5,6,12` | 94 | 74 | 52 |
| 3 | `0,3,5,8,15` | 95 | 80 | 53 |
| 4 | `0,3,6,8,15` | 96 | 70 | 53 |
| 5 | `0,3,5,10,11` | 96 | 79 | 53 |
| 6 | `0,3,5,7,14` | 97 | 41 | 52 |
| 7 | `0,3,5,7,13` | 97 | 61 | 52 |
| 8 | `0,3,5,13,15` | 97 | 61 | 53 |
| 9 | `0,3,5,7,10` | 97 | 70 | 53 |
| 10 | `0,3,5,9,15` | 97 | 71 | 53 |
| 11 | `0,3,5,6,10` | 97 | 75 | 53 |
| 12 | `0,3,6,7,11` | 97 | 80 | 52 |

## Interpretation

Chunk 11 is coverage only. It is weaker than chunks 9 and 10 and does not
add a new basin candidate. Next unclaimed Yale-side chunk starts at
`--start-index 768`.
