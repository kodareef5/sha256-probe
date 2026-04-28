# F132: bit19 fixture does not beat bit3 under known anchor masks
**2026-04-28**

## Summary

F153 shipped the `bit19_HW56_51ca0b34_naive_blocktwo.json` fixture and
predicted that its extreme structural distinction could lower the absorber
floor to roughly 65-75.

F132 ran a first controlled screen on bit19 using the masks that are already
live on bit3:

1. The score-86 bit3 winner `0,1,2,8,9`.
2. The F130 neighbor `0,1,2,9,15`.
3. Earlier compact lanes such as `0,1,8,14` and `0,1,11`.
4. The best F131 four-channel mask `1,2,10,11,15`.

The bit19 result did not validate the easy-floor prediction:

```
Best 3 x 4k anchor score: 96
Best 8 x 50k continuation: 93
Current bit3 best: 86
```

This is not a full six-fixture slate result, but it is a negative first read
on the strongest F153 claim.

## Anchor Screen

Each mask was scanned as a strict single active subset:

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --pool SUBSET --sizes SIZE \
  --restarts 3 --iterations 4000 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F132_bit19_anchor_SUBSET_3x4k.json
```

| Active words | Size | Best score | Msg diff HW | Schedule words |
|---|---:|---:|---:|---:|
| `0,1,2,9,15` | 5 | 96 | 75 | 53 |
| `0,1,8,14` | 4 | 99 | 65 | 52 |
| `1,2,10,11,15` | 5 | 99 | 64 | 53 |
| `0,1,11` | 3 | 100 | 42 | 51 |
| `0,1,5,6,14` | 5 | 101 | 71 | 53 |
| `0,1,2,8,9` | 5 | 103 | 73 | 53 |

The bit3 winner mask `0,1,2,8,9` was specifically bad on bit19 at this
budget. The best bit19 anchor was the newer `0,1,2,9,15` neighbor.

## Continuation

The best anchor was continued:

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --restarts 8 --iterations 50000 --seed 5201 \
  --active-words 0,1,2,9,15 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F132_bit19_anchor_0_1_2_9_15_3x4k.json \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F132_bit19_active_012915_continue_8x50k.json
```

Result:

```
Best target distance: 93
Best msg diff HW:    83
Nonzero W diffs:     53
Final chain diff:    0x2186cb65 0x19119212 0x3da08030 0x33228c05 0xc1a4d529 0x28cf17d4 0x3eb09044 0x20416010
```

The continuation also found a sparse Pareto point:

```
score 94, msgHW 42, actual active words 1,2,9,15
```

That is useful for sparsity analysis, but it is still not competitive with
the bit3 score-86 lane.

## Additive Neighborhood

The score-93 bit19 point was probed with additive common-mode radius 2:

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/probe_absorption_neighborhood.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit19_HW56_51ca0b34_naive_blocktwo.json \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F132_bit19_active_012915_continue_8x50k.json \
  --active-words 0,1,2,9,15 --mode add_common --radius 2 \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F132_bit19_active_012915_addcommon_radius2_probe.json
```

Result:

```
Base score:          93
Candidates:          51200
Skipped no-op moves: 160
Improving moves:     0
Best move:           score 93, msgHW 82
```

The local additive neighborhood did not polish the bit19 point below 93.

## Interpretation

This first bit19 test weakens the simple structural-distinction transfer
hypothesis. The fixture is structurally extreme at block 1, but the known
block-2 absorber masks did not convert that distinction into a lower final
target distance.

The evidence so far says:

1. Low block-1 residual HW alone is not enough.
2. Extreme de58/hardlock structure alone is not enough under reused bit3 masks.
3. Active-word physics is fixture-specific; bit19 may need its own scan rather
   than inheriting the bit3 best masks.

Next useful bit19 step: run a real fixture-local active subset scan instead of
only transferring known bit3 masks. Until that scan beats 86, bit3 remains the
stronger absorber testbed despite being less structurally distinguished.
