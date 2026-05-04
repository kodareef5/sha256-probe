# F888 Shape-Reserve Calibration

## Inputs

- Plain frontier controls:
  - `20260504_F875_bit24_f788_hw86_pair_beam_frontier_hw.json`
  - `20260504_F876_bit24_f796_hw87_pair_beam_frontier_hw.json`
  - `20260504_F877_bit24_f799_hw87_pair_beam_frontier_hw.json`
- Reserve runs:
  - `20260504_F883_bit24_f799_hw87_shape_reserve_beam.json`
  - `20260504_F884_bit24_f796_hw87_shape_reserve_beam.json`
- Combined table:
  - `20260504_F887_shape_reserve_frontier_comparison.{json,md}`

## Reserve Settings

Both reserve runs used:

- beam width: 1024
- global primary slots: 512
- low-net reserve: 384 slots, net <= 4 and removed >= 1
- removal reserve: 128 slots, removed >= 2

After depth 2, both runs filled all low-net and removal reserve slots. The
operator is therefore actually changing the frontier, not merely reporting the
same plain beam.

## Result

| branch | plain best | reserve best | reserve mixed best | verdict |
| --- | ---: | ---: | ---: | --- |
| F799 | HW86 add10/remove0/net+10 | HW86 add10/remove0/net+10 | HW87 add5/remove3/net+2 | stronger false positive |
| F796 | HW87 init | HW87 init | HW91 add6/remove2/net+4 | closed |

The F799 reserve beam is informative. It improves the mixed frontier from the
plain HW90 add6/remove2/net+4 state to HW87 add5/remove3/net+2 at depth 4. But
the only actual improvement remains the pure-add HW86 state at depth 5, and by
depth 6 the best low-net state is back to HW91.

The F796 reserve beam stays closed. Its best low-net state is still HW91
add6/remove2/net+4 at depth 4, then HW94 by depth 6.

## Interpretation

Shape reserves are useful as a diagnostic, but not sufficient as a repair
operator on these weak branches.

The current best separator is now stricter:

- F788/F875: low-net/removal bucket becomes global best by final depth.
- F799/F883: low-net/removal bucket touches the starting HW but does not cross.
- F796/F884: low-net/removal bucket never gets close enough.

So the next selector should score the *trajectory* of the low-net/removal
bucket, not just its presence. A branch that only creates a temporary HW87
mixed plateau but repairs through pure add-add overfill should remain suspect.

## Next Check

Run the same reserve settings on the known-good F788/F875 branch. If the
reserve beam still reaches HW78, the operator is calibrated. If it loses HW78,
the reserve widths are too aggressive and should become diagnostic-only.
