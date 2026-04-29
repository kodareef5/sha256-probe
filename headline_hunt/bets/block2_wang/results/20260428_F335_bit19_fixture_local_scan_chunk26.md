# F335: bit19 chunk 26 finds a score-88 narrow basin
**2026-04-28**

## Summary

F335 continues bit19 fixture-local size-5 candidate discovery at
`--start-index 1664`. This chunk produced a score-88 candidate, so I ran the
standard 8x50k init continuation and a fresh-seed 8x50k check.

```
Chunk:               26
Start index:         1664
Best mask:           1,3,5,6,11
3x4000 score:        88
8x50k continuation:  88
8x50k seed-9001:     95
```

The score-88 point is stronger than F248/F301's score-90 narrow basins, but the
fresh-seed check did not reproduce it. The current F135-basin bit19 floor
remains `0,1,3,8,9` at score 87.

## Chunk Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 1664 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F335_bit19_fullpool_size5_chunk0026_64x3x4k.json
```

Chunk runtime was 114.161 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `1,3,5,6,11` | 88 | 54 | 53 |
| 2 | `1,3,5,8,10` | 94 | 86 | 53 |
| 3 | `1,3,5,8,11` | 95 | 48 | 53 |
| 4 | `1,3,4,6,11` | 95 | 69 | 53 |
| 5 | `1,3,4,7,14` | 95 | 71 | 53 |
| 6 | `1,3,5,7,8` | 95 | 77 | 53 |
| 7 | `1,3,5,6,15` | 95 | 88 | 53 |
| 8 | `1,3,5,7,9` | 96 | 60 | 53 |
| 9 | `1,3,4,12,14` | 96 | 62 | 53 |
| 10 | `1,3,5,8,12` | 96 | 77 | 53 |
| 11 | `1,3,4,6,15` | 97 | 56 | 53 |
| 12 | `1,3,5,7,10` | 97 | 58 | 53 |

## Continuation

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --active-words 1,3,5,6,11 \
  --restarts 8 --iterations 50000 --seed 8401 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F335_bit19_fullpool_size5_chunk0026_64x3x4k.json \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F335_bit19_135611_continue_8x50k.json
```

Continuation summed wall time was 58.768 seconds.

| Restart | Score | Msg diff HW |
|---:|---:|---:|
| 0 | 88 | 54 |
| 1 | 92 | 81 |
| 6 | 92 | 81 |
| 3 | 94 | 80 |
| 4 | 94 | 93 |
| 5 | 95 | 76 |
| 7 | 96 | 92 |
| 2 | 97 | 79 |

## Fresh-seed check

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --active-words 1,3,5,6,11 \
  --restarts 8 --iterations 50000 --seed 9001 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F335_bit19_135611_seed9001_8x50k.json
```

Fresh-seed summed wall time was 59.918 seconds.

| Restart | Score | Msg diff HW |
|---:|---:|---:|
| 2 | 95 | 75 |
| 3 | 95 | 74 |
| 4 | 95 | 82 |
| 7 | 95 | 90 |
| 1 | 97 | 82 |
| 5 | 97 | 87 |
| 0 | 98 | 87 |
| 6 | 98 | 80 |

## Interpretation

The score-88 candidate is real under the chunk artifact/init continuation, but
the fresh-seed run only reached 95. This matches the F248/F301 pattern: narrow
seed-7101/init basins can be preserved, but they are not robust random-init
floors.

Bit19 narrow basins now include:

- F135: `0,1,3,8,9` at score 87
- F335: `1,3,5,6,11` at score 88
- F248: `0,7,9,12,14` at score 90
- F301: `1,2,3,4,15` at score 90

The next unclaimed Yale-side chunk starts at `--start-index 1728`.
