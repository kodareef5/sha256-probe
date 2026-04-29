# F338: bit19 fixture-local scan chunk 28 is negative
**2026-04-28**

## Summary

F338 continues the bit19 fixture-local size-5 active-word scan from the next
unclaimed Yale-side chunk after F337.

```
Chunk:             28
Start index:       1792
Masks scanned:     64
Best mask:         1,3,7,14,15
Best score:        93
Elapsed:           122.089s
```

No score-90-class basin appeared, so I did not run an 8x50k continuation.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 1792 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F338_bit19_fullpool_size5_chunk0028_64x3x4k.json
```

## Result

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `1,3,7,14,15` | 93 | 71 | 53 |
| 2 | `1,3,7,11,14` | 93 | 72 | 53 |
| 3 | `1,3,7,9,15` | 93 | 76 | 53 |
| 4 | `1,3,7,12,13` | 93 | 78 | 53 |
| 5 | `1,3,10,11,13` | 93 | 80 | 53 |
| 6 | `1,3,8,11,13` | 94 | 83 | 53 |
| 7 | `1,3,8,10,14` | 95 | 58 | 53 |
| 8 | `1,3,7,9,10` | 96 | 46 | 53 |
| 9 | `1,3,8,12,14` | 96 | 78 | 53 |
| 10 | `1,3,7,11,15` | 96 | 80 | 53 |
| 11 | `1,3,8,10,11` | 96 | 80 | 53 |
| 12 | `1,3,8,9,11` | 96 | 83 | 53 |

## Interpretation

Chunk 28 adds coverage only. It is weaker than F337's score-90 candidate and
does not alter the bit19 narrow-basin set.

The bit19 narrow basins remain:

- F135: `0,1,3,8,9` at score 87
- F335: `1,3,5,6,11` at score 88
- F248: `0,7,9,12,14` at score 90
- F301: `1,2,3,4,15` at score 90
- F337: `1,3,6,8,12` at score 90

The next unclaimed Yale-side chunk starts at `--start-index 1856`.
