# F320: bit19 fixture-local scan chunk 23 is negative
**2026-04-28**

## Summary

F320 continues the bit19 fixture-local size-5 active-word scan from the next
unclaimed Yale-side chunk after F319.

```
Chunk:             23
Start index:       1472
Masks scanned:     64
Best mask:         1,2,5,13,14
Best score:        92
Elapsed:           113.080s
```

No score-90-class basin appeared, so I did not run an 8x50k continuation.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 1472 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F320_bit19_fullpool_size5_chunk0023_64x3x4k.json
```

## Result

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `1,2,5,13,14` | 92 | 78 | 53 |
| 2 | `1,2,6,7,11` | 94 | 74 | 53 |
| 3 | `1,2,5,11,13` | 94 | 80 | 53 |
| 4 | `1,2,6,7,8` | 95 | 82 | 53 |
| 5 | `1,2,5,10,13` | 95 | 88 | 53 |
| 6 | `1,2,6,7,9` | 96 | 57 | 53 |
| 7 | `1,2,4,12,14` | 96 | 68 | 53 |
| 8 | `1,2,5,6,7` | 96 | 79 | 53 |
| 9 | `1,2,5,11,15` | 96 | 86 | 53 |
| 10 | `1,2,6,7,10` | 97 | 51 | 53 |
| 11 | `1,2,5,9,11` | 97 | 63 | 53 |
| 12 | `1,2,4,13,15` | 97 | 69 | 53 |

## Interpretation

This chunk does not add a new narrow basin. It is slightly stronger than F319's
best score 93, but still above the continuation threshold and inside the robust
random-init floor range.

The bit19 verified narrow-basin floor remains:

- F135: `0,1,3,8,9` at score 87
- F248: `0,7,9,12,14` at score 90
- F301: `1,2,3,4,15` at score 90

The next unclaimed chunk starts at `--start-index 1536`.
