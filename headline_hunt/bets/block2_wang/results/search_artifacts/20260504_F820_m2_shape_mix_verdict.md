# F820 M2 Shape-Mix Verdict

## Inputs

- F817 one-pair repair forecast:
  - `20260504_F817_m2_repair_forecast.json`
  - `20260504_F817_m2_repair_forecast.md`
- F818 transition pair-cover analysis:
  - `20260504_F818_m2_transition_pair_cover.json`
  - `20260504_F818_m2_transition_pair_cover.md`
- F819 shaped F799 repair beam:
  - `20260504_F819_bit24_f799_hw87_pair_beam_shape_mix.json`

## Findings

All checked witnesses are one-pair closed. F788 HW86, F789 HW78, F796 HW87,
F799 HW87, F800 HW86, and F802 HW85 each had zero improving 2-bit M2 moves
across 130,816 local pairs.

The successful F788->F789 transition is not locally obvious. Its 12 transition
bits have exactly one perfect pairing where every pair is inside the original
top-1024 pair pool. That cover mixes one remove-remove pair, two swap pairs,
and three add-add pairs.

The F799->F800 side-branch repair also has exactly one top-pool cover, but its
cover is five pure add-add pairs. It moves M2 weight 40->50 and explains why
the branch then falls into the overfilled F800/F802 basin.

F800->F802 is a smaller version of the same drift: three add-add pairs and one
swap, M2 weight 50->56, with three additions in word 15.

The F819 shaped beam tested whether penalizing net additions and rewarding
removals would uncover a mixed repair from F799. It closed at the starting
HW87. Its best shaped-objective state was balanced, M2 weight 42 with
added6/removed4/net+2, but still HW87.

## Verdict

F799 is probably the wrong detour, not merely the right detour with the wrong
repair objective. The next operator should move upstream: select or generate
detours whose top-pool transition covers resemble F788->F789's mixed cover,
and reject candidates whose accessible covers are pure add-add overfill.

## Next Target

Build a detour selector that scores combo candidates by balanced coverability:

- one-pair closed is acceptable and expected;
- prefer pair-pool covers with removals/swaps plus bounded net additions;
- penalize pure add-add covers, high word-15 concentration, and M2 weight jumps;
- then repair only the top balanced-cover candidates.
