# F900 HW82 Shape-Reserve Verdict

## Inputs

- Top-shelf seed:
  - `20260503_F541_hw82_seed.jsonl`
- Reserve run:
  - `20260504_F897_bit13_hw82_shape_reserve_beam.json`
  - `20260504_F898_f897_hw82_mixed_candidates.{jsonl,md}`
  - `20260504_F899_hw82_vs_success_reserve_comparison.{json,md}`

## Result

The calibrated shape-reserve beam did not improve the bit13 HW82 witness.

| run | init | best | best depth | final low-net/removal best |
| --- | ---: | ---: | ---: | ---: |
| F897 bit13 HW82 reserve | 82 | 82 | 0 | HW90 |
| F889 F788 positive reserve | 86 | 78 | 6 | HW78 |

F897's best frontier states were:

- depth 2: HW88 add3/remove1/net+2
- depth 3: HW86 add5/remove1/net+4
- depth 4: HW89 add7/remove1/net+6
- depth 5: HW88 add9/remove1/net+8
- depth 6: HW90 add7/remove3/net+4

No state crossed below the starting HW82.

## Interpretation

The reserve operator is calibrated, but it does not break the bit13 HW82
basin. This is a useful negative because F897 uses the same reserve criterion
that preserves the known F788->HW78 success path.

The contrast is sharp:

- F889: final low-net/removal bucket becomes the global best and reaches HW78.
- F897: low-net/removal states exist but remain far above the start.

So the HW82 witness is not merely missing a protected mixed frontier under the
plain beam. It needs a different upstream move or a different coordinate
system, not more local pair-beam volume.

## Consequence

Use shape-reserve beams for triage on new detours, but do not keep spending
local reserve-beam compute on this bit13 HW82 seed unless a new target-lane,
carry-chart, or algebraic reason changes the starting point.
