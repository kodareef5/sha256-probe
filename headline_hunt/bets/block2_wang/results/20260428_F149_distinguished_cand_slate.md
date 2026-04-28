# F149: structurally-distinguished cand fixture slate (3 more, complementing F148 bit28)

**2026-04-28**

## Summary

F148 shipped the bit28_HW59 fixture so yale could test the
structural-distinction hypothesis (F143). F149 expands the slate with
3 more fixtures from the structurally distinguished cand list, each
with available F101 corpora.

Now yale has a 4-cand slate of structurally distinguished testbeds:

| Cand | Fixture | de58_size | hardlock | residual_HW |
|---|---|---|---|---|
| bit28_md1acca79_fillff | F148 | 2048 | 15 | 59 |
| bit4_m39a03c2d_fillff | F149 | 2048 | 12 | 63 |
| bit25_m09990bd2_fill80 | F149 | 4096 | 13 | 62 |
| msb_m9cfea9ce_fill00 | F149 | 4096 | 10 | 62 |

Plus the existing bit3_HW55 baseline (de58 generic, ~50K).

## Files shipped (F149)

- `bets/block2_wang/trails/sample_trail_bundles/bit4_HW63_39a03c2d_naive_blocktwo.json`
- `bets/block2_wang/trails/sample_trail_bundles/bit25_HW62_09990bd2_naive_blocktwo.json`
- `bets/block2_wang/trails/sample_trail_bundles/msb_HW62_9cfea9ce_naive_blocktwo.json`

All three validated via `simulate_2block_absorption.py`:
- bit4 HW63: median chain-diff 128 (FORWARD_BROKEN baseline)
- bit25 HW62: similar
- msb HW62: similar

Comparable in structure to bit3_HW55 (median 119) and bit28_HW59
(median 130). Naive block-2 with no W2 constraints.

## Drop-in commands for yale

For each fixture, the F110/F111/F123 commands are identical to bit28's
in F148, just with the fixture path swapped:

```bash
# bit4 example (replicate for bit25, msb)
PYTHONPATH=. python3 headline_hunt/bets/block2_wang/encoders/active_subset_scan.py \
  headline_hunt/bets/block2_wang/trails/sample_trail_bundles/bit4_HW63_39a03c2d_naive_blocktwo.json \
  --pool 0,1,5,7,8,9,10,11,12,13,14 --sizes 3-5 \
  --restarts 3 --iterations 4000 --limit 80 \
  --out-json /tmp/bit4_subset_scan.json
```

## Predicted experiment

Running yale's F110/F111 on all 4 distinguished fixtures + comparing
score floors against bit3's 86:

| Cand | hardlock_bits | Predicted absorber score floor (per F143 hypothesis) |
|---|---|---|
| bit3 (baseline) | unknown (generic) | 86 (yale's empirical) |
| bit28 | 15 (highest) | 70-80 (predicted lowest) |
| bit4 | 12 | 75-85 |
| bit25 | 13 | 73-83 |
| msb_m9cfea9ce | 10 | 78-88 |

If observed: monotonic correlation between hardlock_bits and absorber
score floor across the distinguished cands → F143 hypothesis
empirically supported, suggests yale's heuristic should be re-targeted
at high-hardlock cands as a class.

If not observed: hypothesis refined or refuted; structural distinction
doesn't transfer monotonically to absorber yield.

## Why this is concrete and ship-able

- 4 cands × ~5 minutes per F111 active subset scan = ~20 minutes
  yale-side compute
- All fixtures pre-validated via simulator
- No new tooling needed — yale's existing scripts work directly
- Predicted outcomes are TESTABLE (rank-order of score floors)

The cross-bet experiment is a clean structural test of F143's
hypothesis using yale's existing search infrastructure.

## Connection to today's chain

- F143 (macbook): structurally distinguished cands target list
- F146 (macbook): coordination message proposing bit28 swap
- F148 (macbook): bit28 fixture shipped
- F149 (this memo): 3 more fixtures, 4-cand slate complete

If yale picks this up, it's the highest-leverage cross-bet experiment
the project has set up. Either outcome is informative.

## Discipline

- 0 SAT compute (~30 forward-sim samples each for fixture validation)
- 0 solver runs to log
- All fixtures schema-valid (2blockcertpin/v1)
- validate_registry: 0 errors, 0 warnings

## Status

Slate ready for yale's next iteration. The structural-distinction
hypothesis from F143 now has 4 test points instead of 1.
