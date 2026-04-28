# F169: bit19 chunk 7 is coverage-only
**2026-04-28**

## Summary

F169 continues the coordinated bit19 fixture-local size-5 scan at
`--start-index 448`. This slice did not improve the current bit19 floor.

```
Chunk:        7
Start index:  448
Limit:        64
Best mask:    0,2,4,8,14
Best score:   92
Msg diff HW:  79
```

The current bit19 best remains F135/F159's `0,1,3,8,9` at score 87.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 448 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F169_bit19_fullpool_size5_chunk0007_64x3x4k.json
```

Runtime was 116.324 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,2,4,8,14` | 92 | 79 | 53 |
| 2 | `0,2,4,8,12` | 94 | 60 | 53 |
| 3 | `0,2,5,7,11` | 95 | 58 | 53 |
| 4 | `0,2,4,7,12` | 95 | 62 | 53 |
| 5 | `0,2,4,9,11` | 95 | 72 | 53 |
| 6 | `0,2,4,9,15` | 95 | 72 | 53 |
| 7 | `0,2,5,8,10` | 95 | 78 | 53 |
| 8 | `0,2,4,8,10` | 95 | 83 | 53 |
| 9 | `0,2,5,6,13` | 96 | 52 | 53 |
| 10 | `0,2,4,7,15` | 96 | 71 | 53 |
| 11 | `0,2,5,7,12` | 96 | 77 | 53 |
| 12 | `0,2,4,8,15` | 97 | 61 | 53 |

## Interpretation

Chunk 7 is coverage-only. Its best mask includes W[0], W[2], W[4] and the
late pair W[8],W[14], but it does not reproduce the `3,8,9` motif seen in
F135/F159 and F168.

Best-by-yale-chunk table through chunk 7:

| Chunk | Start index | Best score | Best active words |
|---:|---:|---:|---|
| F134 | 0 | 90 | `0,1,2,7,15` |
| F135/F159 | 64 | 87 | `0,1,3,8,9` |
| F136 | 128 | 91 | `0,1,3,12,15` |
| F137 | 192 | 91 | `0,1,5,10,12` |
| F138 | 256 | 93 | `0,1,6,8,14` |
| F167 | 320 | 93 | `0,1,9,10,14` |
| F168 | 384 | 89 | `0,2,3,8,9` |
| F169 | 448 | 92 | `0,2,4,8,14` |

Next scan slice starts at `--start-index 512`.
