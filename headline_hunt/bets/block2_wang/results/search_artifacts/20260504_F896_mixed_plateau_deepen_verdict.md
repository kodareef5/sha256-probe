# F896 Mixed-Plateau Deepen Verdict

## Inputs

- Source candidate:
  - `20260504_F890_f889_shape_reserve_mixed_candidates.jsonl`
  - HW86 add5/remove1/net+4 at depth 3 of F889
- Deepen run:
  - `20260504_F893_f889_hw86_mixed_plateau_deepen_reserve.json`
  - `20260504_F894_f893_plateau_mixed_candidates.{jsonl,md}`
  - `20260504_F895_mixed_plateau_deepen_comparison.{json,md}`

## Result

Restarting from the early F889 mixed HW86 plateau did not improve.

| run | init | best | final best | final low-net best |
| --- | ---: | ---: | --- | --- |
| F889 original reserve | 86 | 78 | add8/remove4/net+4 | HW78 |
| F893 plateau deepen | 86 | 86 | init | HW90 |

F893 explored six fresh pairs around the HW86 add5/remove1/net+4 plateau. The
best observed frontier states were:

- depth 2: HW87 add4/remove0/net+4
- depth 4: HW88 add7/remove1/net+6
- depth 6: HW88 add10/remove2/net+8
- final low-net/removal best: HW90 add7/remove5/net+2

No state beat the starting HW86.

## Interpretation

The early mixed HW86 plateau is not itself a deeper doorway. The known HW78
success appears to require the original branch's full depth-6 crossover into
add8/remove4/net+4, not just any nearby low-net/mixed HW86 state.

This tightens the selector again:

- useful signal: final-depth low-net/removal crossover;
- weak signal: intermediate mixed state at or near the parent HW;
- rejected signal: restarting from an intermediate mixed plateau and failing to
  improve.

## Consequence

Do not spend broad compute restarting every intermediate mixed plateau. Use
plateau restarts sparingly, only when the plateau also has a target-lane or
carry-chart reason to be special. The better compute path is still to run
shape-reserve triage on fresh raw detours and look for final-depth crossover.
