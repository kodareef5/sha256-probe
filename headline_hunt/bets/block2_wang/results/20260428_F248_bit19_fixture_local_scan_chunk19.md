# F248: bit19 chunk 19 finds score 90, continuation holds at 90
**2026-04-28**

## Summary

F248 continues bit19 fixture-local size-5 candidate discovery at
`--start-index 1216`. This chunk produced the first score-90 candidate since
chunk 8-13, so I ran an immediate 8x50k continuation.

```
Chunk:             19
Start index:       1216
Best mask:         0,7,9,12,14
3x4000 score:      90
8x50k continuation:90
```

The current F135-basin bit19 floor remains `0,1,3,8,9` at score 87. The
chunk-19 near miss is real enough to reproduce under basin-init, but it does
not descend.

## Chunk Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 1216 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F248_bit19_fullpool_size5_chunk0019_64x3x4k.json
```

Chunk runtime was 118.389 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,7,9,12,14` | 90 | 87 | 52 |
| 2 | `0,7,10,11,13` | 93 | 56 | 53 |
| 3 | `0,6,9,13,14` | 94 | 61 | 51 |
| 4 | `0,6,13,14,15` | 94 | 62 | 53 |
| 5 | `0,6,10,11,15` | 95 | 47 | 53 |
| 6 | `0,6,12,13,15` | 95 | 90 | 53 |
| 7 | `0,7,8,10,15` | 96 | 63 | 53 |
| 8 | `0,7,9,10,11` | 96 | 78 | 53 |
| 9 | `0,7,9,10,14` | 96 | 81 | 53 |
| 10 | `0,7,8,11,15` | 97 | 51 | 53 |
| 11 | `0,7,9,10,15` | 97 | 68 | 53 |
| 12 | `0,6,10,11,14` | 97 | 70 | 53 |

## Continuation

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --active-words 0,7,9,12,14 \
  --restarts 8 --iterations 50000 --seed 8201 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F248_bit19_fullpool_size5_chunk0019_64x3x4k.json \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F248_bit19_0791214_continue_8x50k.json
```

Continuation summed wall time was 59.763 seconds.

| Restart | Score | Msg diff HW |
|---:|---:|---:|
| 0 | 90 | 87 |
| 1 | 92 | 75 |
| 4 | 93 | 69 |
| 2 | 96 | 47 |
| 6 | 97 | 69 |
| 3 | 98 | 80 |
| 7 | 98 | 93 |
| 5 | 99 | 85 |

## Interpretation

The score-90 mask is a valid near miss but not a hidden sub-90 basin. The
8x50k basin-init continuation preserves the score-90 result and finds no
descent. This supports the F205/F206 protocol distinction: chunk discovery can
surface candidates, but continuation is needed before treating them as basin
floors.

Next unclaimed Yale-side chunk starts at `--start-index 1280`.
