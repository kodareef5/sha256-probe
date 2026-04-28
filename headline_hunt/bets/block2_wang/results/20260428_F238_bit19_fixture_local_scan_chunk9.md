# F238: bit19 chunk 9 is coverage-only
**2026-04-28**

## Summary

F238 resumes the coordinated bit19 fixture-local size-5 scan at
`--start-index 576`. This is candidate discovery only under the corrected
F205/F206 protocol: 3x4000 chunk results are hints, not verified floors.

```
Chunk:        9
Start index:  576
Limit:        64
Best mask:    0,2,9,11,15
Best score:   91
Msg diff HW:  81
```

The current verified bit19 floor remains F135/F159/F173/F174's `0,1,3,8,9`
at score 87.

## Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 576 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F238_bit19_fullpool_size5_chunk0009_64x3x4k.json
```

Runtime was 117.083 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,2,9,11,15` | 91 | 81 | 53 |
| 2 | `0,2,7,12,13` | 93 | 89 | 53 |
| 3 | `0,2,7,11,15` | 94 | 73 | 53 |
| 4 | `0,2,9,13,14` | 94 | 73 | 53 |
| 5 | `0,2,8,10,13` | 95 | 56 | 53 |
| 6 | `0,2,7,11,12` | 95 | 61 | 53 |
| 7 | `0,2,9,12,14` | 96 | 33 | 53 |
| 8 | `0,2,8,10,11` | 96 | 57 | 53 |
| 9 | `0,2,8,11,13` | 96 | 64 | 53 |
| 10 | `0,2,10,12,15` | 96 | 80 | 53 |
| 11 | `0,2,8,12,15` | 96 | 91 | 53 |
| 12 | `0,2,8,9,13` | 97 | 69 | 53 |

## Interpretation

Chunk 9 does not produce a continuation-worthy candidate. Under the revised
protocol, I am using score 89 or better as the threshold for immediate 8x50k
follow-up. The best mask here is score 91, so this result is coverage only.

The chunk does add another negative slice in the Yale-side gap between chunks
8 and 34. Next unclaimed Yale-side chunk starts at `--start-index 640`.
