# F337: bit19 chunk 27 finds a score-90 narrow basin
**2026-04-28**

## Summary

F337 continues bit19 fixture-local size-5 candidate discovery at
`--start-index 1728`. This chunk produced a score-90 candidate, so I ran the
standard 8x50k init continuation and a fresh-seed 8x50k check.

```
Chunk:               27
Start index:         1728
Best mask:           1,3,6,8,12
3x4000 score:        90
8x50k continuation:  90
8x50k seed-9001:     92
```

The fresh-seed run improved to 92 but did not reproduce the score-90 point.
This looks like another preserved narrow basin, not a new robust random-init
floor.

## Chunk Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 1728 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F337_bit19_fullpool_size5_chunk0027_64x3x4k.json
```

Chunk runtime was 113.271 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `1,3,6,8,12` | 90 | 62 | 53 |
| 2 | `1,3,7,8,13` | 94 | 54 | 53 |
| 3 | `1,3,5,11,13` | 94 | 81 | 53 |
| 4 | `1,3,6,11,15` | 95 | 82 | 53 |
| 5 | `1,3,5,9,10` | 96 | 46 | 53 |
| 6 | `1,3,6,7,13` | 96 | 66 | 53 |
| 7 | `1,3,7,8,10` | 96 | 74 | 53 |
| 8 | `1,3,6,9,10` | 96 | 76 | 53 |
| 9 | `1,3,6,9,12` | 97 | 32 | 53 |
| 10 | `1,3,6,10,15` | 97 | 73 | 53 |
| 11 | `1,3,6,11,12` | 97 | 98 | 53 |
| 12 | `1,3,6,13,15` | 98 | 53 | 53 |

## Continuation

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --active-words 1,3,6,8,12 \
  --restarts 8 --iterations 50000 --seed 8501 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F337_bit19_fullpool_size5_chunk0027_64x3x4k.json \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F337_bit19_136812_continue_8x50k.json
```

Continuation summed wall time was 64.567 seconds.

| Restart | Score | Msg diff HW |
|---:|---:|---:|
| 0 | 90 | 62 |
| 6 | 93 | 76 |
| 1 | 95 | 78 |
| 2 | 95 | 86 |
| 3 | 95 | 80 |
| 5 | 97 | 95 |
| 7 | 97 | 81 |
| 4 | 99 | 78 |

## Fresh-seed check

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --active-words 1,3,6,8,12 \
  --restarts 8 --iterations 50000 --seed 9001 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F337_bit19_136812_seed9001_8x50k.json
```

Fresh-seed summed wall time was 63.583 seconds.

| Restart | Score | Msg diff HW |
|---:|---:|---:|
| 4 | 92 | 84 |
| 5 | 92 | 78 |
| 2 | 94 | 77 |
| 7 | 95 | 76 |
| 0 | 96 | 89 |
| 1 | 96 | 86 |
| 3 | 96 | 84 |
| 6 | 97 | 75 |

## Interpretation

F337 adds another score-90-class narrow basin. It is more robust than F335 in
one limited sense: the fresh-seed check reached 92 rather than 95. It still did
not reproduce the score-90 chunk point, so it should not be treated as a robust
floor.

Bit19 narrow basins now include:

- F135: `0,1,3,8,9` at score 87
- F335: `1,3,5,6,11` at score 88
- F248: `0,7,9,12,14` at score 90
- F301: `1,2,3,4,15` at score 90
- F337: `1,3,6,8,12` at score 90

The next unclaimed Yale-side chunk starts at `--start-index 1792`.
