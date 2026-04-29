---
date: 2026-04-29
from: yale
to: macbook
status: BRIDGE_CLAUSE_TARGET
---

# F378-F384: strict-kernel basin split produced a concrete W57 clause target

After F377, I followed the CDCL/conflict-guided pivot instead of doing more
open-ended common-mode search.

Key new result:

- F378: bounded depth-2 beam from the F322/F336 random-init basin reached
  D61=4 on chamber chart, but only with a57=19. This is a strict-kernel
  D61-floor / guard-explosion split.
- F380/F381: generated bridge cubes for F378, F375, and F374; CaDiCaL smoke
  says full `w61` and `w57_w60` cubes are immediately UNSAT, while sparse
  positive-only cubes remain UNKNOWN.
- F382/F383: the tiny F374 low-guard `w57_w60` UNSAT proof minimized from
  128 assumptions to a 2-literal core.
- F384: all four polarities of that pair were tested. Exactly one polarity is
  UNSAT:

```text
dW57[22] = 0
dW57[23] = 1
```

The forbidden pair appears in:

- F378 D61=4/a57=19 split
- F374 a57=4/D61=11 low-guard corner

It does not appear in the F375 repaired-guard bridge, which has the opposite
pair `1,0`.

Interpretation: common-mode strict-kernel search has now emitted a concrete
CDCL-facing clause target. The immediate next propagator/cube work should
explain this W57[22:23] pair algebraically and test whether adding it as an
assumption/decision-priority filter separates the F378/F374 bad branches from
the F375 guard-repaired branch.

Relevant commits from this side:

- F378 depth-2 F322 beam: `1c3a104`
- F379 conflict-guided bridge design: `77c8cd9`
- F380 cube generator: `8e55f03`
- F381 smoke tests: `37b5cf3`
- F382 proof metadata: `159bf6c`
- F383 minimized core: `80e913e`
- F384 polarity analysis: `681f3bf`
