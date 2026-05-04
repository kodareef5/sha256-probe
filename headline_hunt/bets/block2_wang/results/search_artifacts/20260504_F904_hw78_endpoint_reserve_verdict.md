# F904 HW78 Endpoint Reserve Verdict

## Inputs

- Endpoint seed:
  - F789 best M2 from `20260504_F791_bit24_f789_hw78_pair_beam_hw.json`
- Reserve run:
  - `20260504_F901_f789_hw78_shape_reserve_beam.json`
  - `20260504_F902_f901_hw78_mixed_candidates.{jsonl,md}`
  - `20260504_F903_hw78_endpoint_reserve_comparison.{json,md}`

## Result

The HW78 endpoint is closed under the calibrated shape-reserve beam.

| run | init | best | final best | final low-net/removal best |
| --- | ---: | ---: | ---: | ---: |
| F901 F789 endpoint reserve | 78 | 78 | HW89 | HW95 |

The best frontier states were:

- depth 2: HW88 add4/remove0/net+4
- depth 4: HW89 add6/remove2/net+4
- depth 6: HW89 add9/remove3/net+6
- final low-net/removal best: HW95 add8/remove4/net+4

No state beat the starting HW78.

## Interpretation

The reserve operator confirms the endpoint is not locally leaky. It preserves
the F788->F789 path when started upstream, but once started at F789 HW78 the
neighborhood pushes back upward immediately.

This reinforces the current model:

- the useful event is a depth-6 transition into the HW78 basin;
- the HW78 basin itself is locally closed under plain, CG, and shape-reserve
  pair beams;
- future compute should search for new upstream detours with final-depth
  low-net/removal crossover, not local repairs from HW78.

## Consequence

Do not spend more pair-beam compute directly on the HW78 endpoint unless the
operator changes materially. The next productive direction is upstream detour
generation or a different representation of carry/lane structure.
