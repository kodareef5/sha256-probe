# F134: first fixture-local bit19 scan slice finds a score-90 mask
**2026-04-28**

## Summary

F156 concluded that generic structural priors do not transfer at the current
absorber-search budget, and that each fixture needs its own active-word scan.
F134 starts that process for the F153 bit19 fixture.

I also made `active_subset_scan.py` resumable by adding `--start-index`, so
the full 4,368-mask size-5 scan can be run in deterministic chunks.

First bit19 chunk:

```
Fixture:      bit19_HW56_51ca0b34_naive_blocktwo.json
Subset range: start 0, limit 64 of 4368 size-5 masks
Budget:       3 restarts x 4000 iterations per mask
Best mask:    0,1,2,7,15
Best score:   90
Msg diff HW:  56
```

This beats the previous bit19 result from F132 (`0,1,2,9,15` at score 93)
and supports F156's practical point: bit19 needs fixture-local masks, not
bit3 mask transfer.

## Scanner Update

New option:

```bash
--start-index N
```

The scanner enumerates or shuffles the full subset list, skips `N` entries,
then applies `--limit`. JSON outputs now record:

```
total_available
start_index
```

This makes long fixture-local scans resumable and shardable without changing
the scoring behavior.

## Chunk Command

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool 0-15 --sizes 5 \
  --start-index 0 --limit 64 \
  --restarts 3 --iterations 4000 --seed 7101 \
  --require-all-used --top 16 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F134_bit19_fullpool_size5_chunk0000_64x3x4k.json
```

Runtime was 120.245 seconds for 64 masks.

Top chunk results:

| Rank | Active words | Score | Msg diff HW | Schedule words |
|---:|---|---:|---:|---:|
| 1 | `0,1,2,7,15` | 90 | 56 | 53 |
| 2 | `0,1,2,7,10` | 93 | 57 | 53 |
| 3 | `0,1,2,3,7` | 94 | 86 | 53 |
| 4 | `0,1,2,8,11` | 95 | 57 | 53 |
| 5 | `0,1,2,4,6` | 95 | 58 | 53 |
| 6 | `0,1,2,5,6` | 95 | 59 | 53 |
| 7 | `0,1,2,8,10` | 95 | 64 | 53 |
| 8 | `0,1,2,4,15` | 95 | 74 | 53 |
| 9 | `0,1,2,4,5` | 95 | 89 | 53 |
| 10 | `0,1,2,5,7` | 96 | 30 | 53 |

The chunk's Pareto frontier is:

```
score 90, msgHW 56, active 0,1,2,7,15
score 96, msgHW 30, active 0,1,2,5,7
```

## Continuation

The chunk winner was continued:

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --restarts 8 --iterations 50000 --seed 7201 \
  --active-words 0,1,2,7,15 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F134_bit19_fullpool_size5_chunk0000_64x3x4k.json \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F134_bit19_active_012715_continue_8x50k.json
```

The continuation did not improve:

```
Best target distance: 90
Best msg diff HW:    56
Nonzero W diffs:     53
Final chain diff:    0x21186f91 0x2768e4b0 0x3041802f 0x84028202 0x005c444b 0x93d35384 0x14730284 0x071e1a22
```

## Additive Neighborhood

Additive common-mode radius 2 around the continued score-90 point:

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/probe_absorption_neighborhood.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F134_bit19_active_012715_continue_8x50k.json \
  --active-words 0,1,2,7,15 --mode add_common --radius 2 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F134_bit19_active_012715_addcommon_radius2_probe.json
```

Result:

```
Base score:          90
Candidates:          51200
Skipped no-op moves: 160
Improving moves:     0
Best real move:      score 93
```

## Interpretation

This is the first positive result after the F156 consolidation. The simple
structural-prior transfer story failed, but chunked fixture-local search
immediately improved bit19 from score 93 to score 90 in only 64 of 4,368
size-5 masks.

That does not yet beat the bit3 score-86 lane, but it changes the bit19
assessment: bit19 was not inherently worse, it was being evaluated mostly
through the wrong active masks.

Next useful step: continue the bit19 full-pool scan at `--start-index 64`.
