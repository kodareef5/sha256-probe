# F333: bit19 fixture-local scan chunk 24 is negative
**2026-04-28**

## Summary

F333 continues the bit19 fixture-local size-5 active-word scan from the next
unclaimed Yale-side chunk after F320.

```
Chunk:             24
Start index:       1536
Masks scanned:     64
Best mask:         1,2,7,14,15
Best score:        92
Elapsed:           113.479s
```

No score-90-class basin appeared, so I did not run an 8x50k continuation.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 1536 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F333_bit19_fullpool_size5_chunk0024_64x3x4k.json
```

## Result

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `1,2,7,14,15` | 92 | 61 | 53 |
| 2 | `1,2,6,12,15` | 94 | 65 | 53 |
| 3 | `1,2,7,9,14` | 94 | 72 | 53 |
| 4 | `1,2,8,9,14` | 94 | 72 | 53 |
| 5 | `1,2,7,10,13` | 94 | 77 | 53 |
| 6 | `1,2,7,10,14` | 95 | 76 | 53 |
| 7 | `1,2,6,8,15` | 96 | 62 | 53 |
| 8 | `1,2,6,11,14` | 96 | 62 | 53 |
| 9 | `1,2,7,9,11` | 96 | 72 | 53 |
| 10 | `1,2,6,12,13` | 96 | 76 | 53 |
| 11 | `1,2,6,8,10` | 96 | 82 | 53 |
| 12 | `1,2,7,9,10` | 96 | 86 | 53 |

## Interpretation

This chunk does not add a new narrow basin. The best score 92 matches F320's
best-score level and remains above the continuation threshold.

The bit19 verified narrow-basin floor remains:

- F135: `0,1,3,8,9` at score 87
- F248: `0,7,9,12,14` at score 90
- F301: `1,2,3,4,15` at score 90

The next unclaimed chunk starts at `--start-index 1600`.
