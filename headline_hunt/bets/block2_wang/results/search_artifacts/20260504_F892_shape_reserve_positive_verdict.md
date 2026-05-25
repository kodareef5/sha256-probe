# F892 Shape-Reserve Positive-Control Verdict

## Inputs

- F889 positive control:
  - `20260504_F889_bit24_f788_hw86_shape_reserve_beam.json`
  - `20260504_F890_f889_shape_reserve_mixed_candidates.{jsonl,md}`
- Reserve comparison:
  - `20260504_F891_shape_reserve_positive_control_comparison.{json,md}`
- Prior controls:
  - `20260504_F883_bit24_f799_hw87_shape_reserve_beam.json`
  - `20260504_F884_bit24_f796_hw87_shape_reserve_beam.json`

## Result

The shape-reserve beam is calibrated on the known-good F788 branch.

| branch | reserve best | final low-net/removal best | interpretation |
| --- | ---: | ---: | --- |
| F788/F889 | HW78 add8/remove4/net+4 | HW78 | positive control passes |
| F799/F883 | HW86 add10/remove0/net+10 | HW91 | pure-add overfill remains |
| F796/F884 | HW87 init | HW94 | closed |

F889 reaches the same HW78 endpoint as the plain F875 run. It does drop the
plain run's intermediate HW85 pure-add state, but that is acceptable: the
operator preserves the final mixed repair path, which is the thing we wanted to
protect.

## Calibration

The reserve settings are safe enough to use as an active diagnostic operator:

- beam width: 1024
- global primary slots: 512
- low-net reserve: 384 slots with net <= 4 and removed >= 1
- removal reserve: 128 slots with removed >= 2

The positive branch reaches HW78 despite the reserves. The two weak branches do
not become false wins:

- F799 gets a temporary HW87 mixed plateau at depth 4, but still repairs only
  by pure add-add to HW86.
- F796 never improves.

## Updated Selector

Use final-depth low-net/removal crossover as the repair-coverability signal.

Pass:

- final low-net/removal bucket beats the starting HW;
- final best shape has removals and bounded net additions;
- pure-add states are not the only improvement.

Fail or suspect:

- low-net/removal bucket appears only as an intermediate plateau;
- final improvement is pure add-add overfill;
- final low-net/removal best remains above the starting HW.

This is stronger than the earlier "mixed bucket exists" test and survives the
F799 false positive.

## Next Use

Apply the reserve beam to new raw detours as a triage step. Promote only
branches whose final low-net/removal frontier crosses below the parent HW; do
not promote branches that merely touch the parent HW mid-run.
