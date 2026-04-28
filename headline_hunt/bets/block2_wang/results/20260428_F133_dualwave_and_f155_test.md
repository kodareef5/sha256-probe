# F133: dual-wave and F155 combined prediction miss; mid-only control is sparse
**2026-04-28**

## Summary

F154 proposed a dual-wave explanation for the empirical score-86
`0,1,2,8,9` lane. F155 sharpened that into a single highest-priority
candidate:

```
0,1,8,9,14
```

This mask preserves the W24 `8,9` second wave and adds W14 as the missing
sigma1 channel into W16.

F133 tested that candidate plus the F154 dual-wave candidates and single-wave
controls on the bit3 fixture. The prediction missed:

```
F155 0,1,8,9,14 score: 100
Best dual-wave score:  98
Best control score:    94
Current best score:    86
```

The surprising byproduct is that the mid-only control `8,9,10,11,12` reached
score 94 with very low message HW, and continuation kept score 94 while
finding a msgHW 33 point.

## Screen

Each mask was scanned as a strict single active subset:

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --pool SUBSET --sizes 5 \
  --restarts 3 --iterations 4000 \
  --require-all-used \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F133_SUBSET_3x4k.json
```

| Class | Active words | Best score | Msg diff HW | Schedule words |
|---|---|---:|---:|---:|
| F155 combined | `0,1,8,9,14` | 100 | 69 | 53 |
| Dual-wave | `0,1,7,8,15` | 100 | 62 | 53 |
| Dual-wave | `1,2,3,9,10` | 98 | 85 | 53 |
| Dual-wave | `2,3,8,9,15` | 98 | 71 | 53 |
| Single-wave control | `0,1,2,3,4` | 99 | 64 | 53 |
| Single-wave control | `8,9,10,11,12` | 94 | 43 | 53 |

The dual-wave candidates did not beat the controls. The mid-only control was
the best point in the batch.

## Continuation

The mid-only control was continued because its score-94/msgHW-43 point was
the only potentially useful result:

```bash
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/search_block2_absorption.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit3_HW55_naive_blocktwo.json \
  --restarts 8 --iterations 50000 --seed 6201 \
  --active-words 8,9,10,11,12 \
  --init-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F133_singlewave_8_9_10_11_12_3x4k.json \
  --out-json headline_hunt/bets/block2_wang/results/search_artifacts/20260428_F133_bit3_active_89101112_continue_8x50k.json
```

Result:

```
Best target distance: 94
Best msg diff HW at score 94: 33
Nonzero W diffs: 53
Final chain diff: 0x48b29632 0xe3ec1528 0x3c40c801 0xd1a24c12 0x1c223101 0xa1048814 0x7e3e97b2 0x0016e220
```

The continuation did not lower the target distance, but it produced the
cleanest low-HW score-94 lane seen in this sequence.

## Interpretation

F155's combined rule was too broad: adding W14 to the `0,1,8,9` dual-wave
core disrupted rather than improved the absorber. F154's dual-wave framing
also fails in this simple form because the single mid-wave control beat every
dual-wave test in this batch.

The score-86 `0,1,2,8,9` winner is therefore not explained by:

1. Raw overlap density.
2. Four-channel W16 coverage.
3. Dual-wave structure alone.
4. Four-channel plus dual-wave structure.

The next feature to test should be more specific: keep the exact
`0,1,2,8,9` W16/W17/W24 phase, then vary one word at a time with matched
continuation budgets. Broad structural substitutions have repeatedly failed.
