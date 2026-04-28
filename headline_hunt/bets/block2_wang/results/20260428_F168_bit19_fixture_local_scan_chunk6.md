# F168: bit19 chunk 6 finds a score-89 near miss
**2026-04-28**

## Summary

F168 continues the coordinated bit19 fixture-local size-5 scan at
`--start-index 384`. The slice did not improve the score-87 bit19 floor,
but it found the strongest post-chunk-1 result in this local range so far.

```
Chunk:        6
Start index:  384
Limit:        64
Best mask:    0,2,3,8,9
Best score:   89
Msg diff HW:  73
```

The current bit19 best remains F135/F159's `0,1,3,8,9` at score 87.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 384 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F168_bit19_fullpool_size5_chunk0006_64x3x4k.json
```

Runtime was 115.488 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,2,3,8,9` | 89 | 73 | 53 |
| 2 | `0,2,3,12,14` | 91 | 78 | 53 |
| 3 | `0,2,4,5,15` | 93 | 65 | 53 |
| 4 | `0,2,4,5,8` | 93 | 83 | 53 |
| 5 | `0,2,4,6,10` | 94 | 64 | 53 |
| 6 | `0,2,4,6,8` | 94 | 74 | 53 |
| 7 | `0,2,3,7,11` | 94 | 79 | 53 |
| 8 | `0,2,3,6,10` | 95 | 50 | 53 |
| 9 | `0,2,3,8,12` | 95 | 65 | 53 |
| 10 | `0,2,3,7,9` | 95 | 66 | 53 |
| 11 | `0,2,3,6,15` | 95 | 74 | 53 |
| 12 | `0,2,4,5,14` | 95 | 81 | 53 |

## Interpretation

The best mask `0,2,3,8,9` is one word away from the current bit19 winner
`0,1,3,8,9`: it preserves the `3,8,9` motif but swaps out W[1] for W[2].
That supports the local picture from F159/F160: the bit19 basin is strongly
organized around the `3,8,9` mid-cluster, while W[1] appears important for
crossing from score 89 to score 87.

Best-by-yale-chunk table through chunk 6:

| Chunk | Start index | Best score | Best active words |
|---:|---:|---:|---|
| F134 | 0 | 90 | `0,1,2,7,15` |
| F135/F159 | 64 | 87 | `0,1,3,8,9` |
| F136 | 128 | 91 | `0,1,3,12,15` |
| F137 | 192 | 91 | `0,1,5,10,12` |
| F138 | 256 | 93 | `0,1,6,8,14` |
| F167 | 320 | 93 | `0,1,9,10,14` |
| F168 | 384 | 89 | `0,2,3,8,9` |

Next scan slice starts at `--start-index 448`.
