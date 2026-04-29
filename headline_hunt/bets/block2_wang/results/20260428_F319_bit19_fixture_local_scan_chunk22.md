# F319: bit19 fixture-local scan chunk 22 is negative
**2026-04-28**

## Summary

F319 continues the bit19 fixture-local size-5 active-word scan from the next
unclaimed Yale-side chunk after F301.

```
Chunk:             22
Start index:       1408
Masks scanned:     64
Best mask:         1,2,4,8,10
Best score:        93
Elapsed:           114.060s
```

No score-90-class basin appeared, so I did not run an 8x50k continuation.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 1408 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F319_bit19_fullpool_size5_chunk0022_64x3x4k.json
```

## Result

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `1,2,4,8,10` | 93 | 72 | 53 |
| 2 | `1,2,4,9,12` | 93 | 75 | 53 |
| 3 | `1,2,4,8,9` | 94 | 76 | 53 |
| 4 | `1,2,4,7,10` | 95 | 61 | 53 |
| 5 | `1,2,4,7,15` | 96 | 57 | 53 |
| 6 | `1,2,4,5,9` | 96 | 69 | 53 |
| 7 | `1,2,4,9,10` | 96 | 74 | 53 |
| 8 | `1,2,3,13,15` | 96 | 76 | 53 |
| 9 | `1,2,3,9,13` | 96 | 85 | 53 |
| 10 | `1,2,4,6,15` | 97 | 44 | 53 |
| 11 | `1,2,4,6,13` | 97 | 60 | 53 |
| 12 | `1,2,3,8,14` | 97 | 67 | 53 |

## Interpretation

This chunk does not add a new narrow basin. The bit19 verified narrow-basin
floor remains:

- F135: `0,1,3,8,9` at score 87
- F248: `0,7,9,12,14` at score 90
- F301: `1,2,3,4,15` at score 90

F319's best score 93 is inside the robust random-init floor range and is not
worth continuation. The next unclaimed chunk starts at `--start-index 1472`.
