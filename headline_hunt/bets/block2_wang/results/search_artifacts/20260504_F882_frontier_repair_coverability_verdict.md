# F882 Frontier Repair Coverability Verdict

## Inputs

- `20260504_F875_bit24_f788_hw86_pair_beam_frontier_hw.json`
- `20260504_F876_bit24_f796_hw87_pair_beam_frontier_hw.json`
- `20260504_F877_bit24_f799_hw87_pair_beam_frontier_hw.json`
- `20260504_F881_frontier_success_controls_comparison.md`
- Mixed-frontier candidate exports:
  - `20260504_F878_f875_mixed_frontier_candidates.{jsonl,md}`
  - `20260504_F879_f876_mixed_frontier_candidates.{jsonl,md}`
  - `20260504_F880_f877_mixed_frontier_candidates.{jsonl,md}`

## Result

The F875/F876/F877 frontier reruns separate the known successful F788 repair
from the two weaker branches.

| branch | init | best | best shape | bounded-net mixed candidates with HW <= 91 |
| --- | ---: | ---: | --- | ---: |
| F875/F788 | 86 | 78 | add8/remove4/net+4 | 7 |
| F876/F796 | 87 | 87 | init | 1 |
| F877/F799 | 87 | 86 | add10/remove0/net+10 | 1 |

F875 is the only branch where the low-net/removal bucket becomes the global
best frontier by the final repair depth. At depth 6 its best state is HW78 with
add8/remove4/net+4.

F876 has removal states, but they do not become competitive: its final best
overall frontier is HW89 add10/remove2/net+8, while its best low-net state is
HW94 add8/remove4/net+4.

F877 also has a tempting low-net/removal state at depth 4: HW90
add6/remove2/net+4. But the actual improvement is pure add-add overfill:
HW86 add10/remove0/net+10 at depth 5. By depth 6 the low-net bucket has fallen
back to HW95.

## Interpretation

The selector is not "does a mixed bucket exist?" F877 would pass that weak test.

The stronger selector is:

- keep low-net/removal buckets alive through the full repair depth;
- require the low-net/removal bucket to become competitive with the global best;
- reject branches whose only improvement is pure add-add overfill.

This explains why raw detour shape was misleading. The useful signal appears
inside the repair frontier after the side basin forms.

## Next Operator

Build a shape-stratified M2 repair beam. The current beam ranks one global
frontier by objective and only observes shape afterward. The next version should
reserve slots for low-net/removal buckets at every depth, then compare:

- global HW frontier;
- bounded-net frontier, especially net <= 4;
- removal-bearing frontier, especially removed >= 2;
- pure-add frontier as a negative control.

The operator should report whether the bounded-net/removal reserve crosses the
global frontier by depth 5 or 6. That crossover, not raw add/remove counts, is
the current best repair-coverability signal.
