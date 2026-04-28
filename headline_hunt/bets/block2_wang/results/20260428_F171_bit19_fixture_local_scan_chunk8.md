# F171: bit19 chunk 8 is negative
**2026-04-28**

## Summary

F171 continues the coordinated bit19 fixture-local size-5 scan at
`--start-index 512`. This slice did not improve the current bit19 floor.

```
Chunk:        8
Start index:  512
Limit:        64
Best mask:    0,2,5,11,15
Best score:   91
Msg diff HW:  80
```

The current bit19 best remains F135/F159's `0,1,3,8,9` at score 87.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 512 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F171_bit19_fullpool_size5_chunk0008_64x3x4k.json
```

Runtime was 118.239 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,2,5,11,15` | 91 | 80 | 53 |
| 2 | `0,2,6,8,9` | 94 | 75 | 53 |
| 3 | `0,2,6,13,14` | 95 | 53 | 53 |
| 4 | `0,2,7,8,14` | 95 | 59 | 53 |
| 5 | `0,2,5,13,15` | 95 | 69 | 53 |
| 6 | `0,2,6,8,13` | 95 | 73 | 53 |
| 7 | `0,2,5,11,13` | 95 | 74 | 53 |
| 8 | `0,2,5,12,14` | 96 | 72 | 53 |
| 9 | `0,2,6,7,8` | 96 | 86 | 53 |
| 10 | `0,2,6,10,14` | 97 | 50 | 53 |
| 11 | `0,2,5,9,13` | 97 | 58 | 53 |
| 12 | `0,2,7,8,10` | 97 | 60 | 53 |

## Interpretation

Chunk 8 is coverage-only. Its winner is another W[0],W[2] mask, and the
chunk does not produce a score-89 or better near miss like F168.

Best-by-yale-chunk table through chunk 8:

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
| F171 | 512 | 91 | `0,2,5,11,15` |

Next scan slice starts at `--start-index 576`.
