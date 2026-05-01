---
date: 2026-04-30
bet: programmatic_sat_propagator
status: BIT2_PRIORITY_RESCUE_NEGATIVE
parents: F402, F407, F408, F409, F410
---

# F411: F286 decision-priority does not rescue bit2

## Setup

F402 identified `bit2_ma896ee41` as the singleton F343 outlier and proposed
testing whether decision-priority nudging rescues it.

This is now testable locally:

- F408 mined bit2's sr60/force hard core.
- F409 mapped bit2 onto the F286/F332 priority recipes.
- F410 ran bit2 under the same 50k-conflict C++ propagator matrix with
  `--priority-max-suggestions=132`.

## Bit2 Priority-Spec Finding

Bit2's conservative F286 priority set is complete:

| Set | Present | Missing |
|---|---:|---:|
| F286 conservative | 132 / 132 | 0 |
| F332 stable6 | 137 / 139 | 2 |

The two missing F332 keys are:

- `w2[57].b1`
- `w2[58].b1`

So bit2 is not fully compatible with the broader F332 stable-core recipe, even
though the conservative 132-bit F286 recipe maps cleanly.

## F410 Result

At 50k conflicts:

| Arm | Wall | Decisions | Backtracks | cb_decide |
|---|---:|---:|---:|---:|
| existing propagator | 3.814s | 353889 | 58131 | 0 |
| F286 max132 | 4.196s | 396334 | 58673 | 132 |

Delta for F286 max132 vs existing:

- Wall: +10.0%
- Decisions: +12.0%
- Backtracks: +0.9%

The F332 arm correctly fails fast because the F409 spec records missing keys.

## Verdict

F286-style decision priority does **not** rescue bit2 in this C++ path. This is
consistent with F402/F393's picture: bit2 is not merely failing because CaDiCaL
never sees the right early priority variables. The bounded priority nudge makes
the run worse.

Bit2 remains a real singleton outlier. The next bit2-specific intervention
should not be more generic F286 priority. Better candidates:

1. Mine bit2-specific conflict traces for the first branches where F343 clauses
   become active but non-pruning.
2. Compare bit2 against bit4/bit24/bit28 on the two missing low-bit F332 keys.
3. Wire F343 clause injection into the C++ matrix path and test interaction with
   bit2, but expect priority alone to be insufficient.
