# F301: bit19 chunk 21 finds another score-90 basin
**2026-04-28**

## Summary

F301 continues bit19 fixture-local size-5 candidate discovery at
`--start-index 1344`. This chunk produced another score-90 candidate, so I
ran an 8x50k continuation and a fresh-seed 8x50k check.

```
Chunk:             21
Start index:       1344
Best mask:         1,2,3,4,15
3x4000 score:      90
8x50k continuation:90
8x50k seed-9001:   93
```

The current F135-basin bit19 floor remains `0,1,3,8,9` at score 87. F301
adds another score-90-class basin on bit19, after F248's `0,7,9,12,14`, but
the fresh-seed check suggests the score-90 point is seed/init-narrow.

## Chunk Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 1344 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F301_bit19_fullpool_size5_chunk0021_64x3x4k.json
```

Chunk runtime was 116.375 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `1,2,3,4,15` | 90 | 75 | 53 |
| 2 | `1,2,3,7,12` | 91 | 76 | 53 |
| 3 | `1,2,3,7,13` | 93 | 81 | 53 |
| 4 | `0,10,11,12,15` | 95 | 64 | 53 |
| 5 | `1,2,3,4,5` | 96 | 60 | 53 |
| 6 | `0,11,12,13,14` | 96 | 80 | 52 |
| 7 | `1,2,3,7,14` | 96 | 83 | 53 |
| 8 | `0,10,12,14,15` | 96 | 84 | 53 |
| 9 | `1,2,3,5,8` | 97 | 56 | 53 |
| 10 | `0,10,11,13,14` | 97 | 64 | 53 |
| 11 | `0,11,12,14,15` | 97 | 70 | 53 |
| 12 | `1,2,3,7,9` | 97 | 75 | 53 |

## Continuation

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --active-words 1,2,3,4,15 \
  --restarts 8 --iterations 50000 --seed 8301 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F301_bit19_fullpool_size5_chunk0021_64x3x4k.json \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F301_bit19_123415_continue_8x50k.json
```

Continuation summed wall time was 57.776 seconds.

| Restart | Score | Msg diff HW |
|---:|---:|---:|
| 0 | 90 | 75 |
| 2 | 97 | 74 |
| 3 | 97 | 77 |
| 6 | 97 | 80 |
| 1 | 98 | 80 |
| 4 | 98 | 77 |
| 5 | 99 | 85 |
| 7 | 99 | 86 |

## Fresh-seed check

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --active-words 1,2,3,4,15 \
  --restarts 8 --iterations 50000 --seed 9001 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F301_bit19_123415_seed9001_8x50k.json
```

The seed-9001 run used random init, without the chunk artifact as an init
source. Summed wall time was 62.398 seconds.

| Restart | Score | Msg diff HW |
|---:|---:|---:|
| 0 | 93 | 69 |
| 1 | 95 | 91 |
| 5 | 96 | 75 |
| 2 | 98 | 79 |
| 3 | 98 | 90 |
| 4 | 98 | 77 |
| 6 | 99 | 77 |
| 7 | 99 | 86 |

## Interpretation

The score-90 result is real in the sense that the chunk artifact can be
preserved by an 8x50k continuation, but the fresh-seed 8x50k run only reached
93. That matches the F248 pattern: a narrow seed-7101/init basin rather than a
robust random-init floor. The mask family is structurally different from both
known bit19 basins:

- F135: `0,1,3,8,9` at score 87
- F248: `0,7,9,12,14` at score 90
- F301: `1,2,3,4,15` at score 90

Bit19 now has multiple verified narrow basins, but none below 87. Next
unclaimed Yale-side chunk starts at `--start-index 1408`.
