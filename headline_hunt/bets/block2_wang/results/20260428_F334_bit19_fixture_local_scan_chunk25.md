# F334: bit19 fixture-local scan chunk 25 is negative
**2026-04-28**

## Summary

F334 continues the bit19 fixture-local size-5 active-word scan from the next
unclaimed Yale-side chunk after F333.

```
Chunk:             25
Start index:       1600
Masks scanned:     64
Best mask:         1,2,13,14,15
Best score:        94
Elapsed:           113.781s
```

No score-90-class basin appeared, so I did not run an 8x50k continuation.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 1600 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F334_bit19_fullpool_size5_chunk0025_64x3x4k.json
```

## Result

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `1,2,13,14,15` | 94 | 72 | 53 |
| 2 | `1,2,8,11,13` | 94 | 73 | 53 |
| 3 | `1,3,4,5,6` | 96 | 70 | 53 |
| 4 | `1,3,4,5,14` | 96 | 75 | 53 |
| 5 | `1,2,11,12,13` | 96 | 77 | 53 |
| 6 | `1,2,12,13,15` | 96 | 88 | 53 |
| 7 | `1,3,4,5,9` | 97 | 53 | 53 |
| 8 | `1,2,11,13,14` | 97 | 62 | 53 |
| 9 | `1,2,12,13,14` | 97 | 66 | 53 |
| 10 | `1,2,9,11,15` | 97 | 75 | 53 |
| 11 | `1,3,4,5,15` | 97 | 81 | 53 |
| 12 | `1,2,9,10,13` | 98 | 52 | 53 |

## Interpretation

Chunk 25 is weaker than F333 and does not add a new narrow basin. Its best
score 94 is inside the robust random-init floor range, not a continuation
candidate.

The bit19 verified narrow-basin floor remains:

- F135: `0,1,3,8,9` at score 87
- F248: `0,7,9,12,14` at score 90
- F301: `1,2,3,4,15` at score 90

The next unclaimed chunk starts at `--start-index 1664`.
