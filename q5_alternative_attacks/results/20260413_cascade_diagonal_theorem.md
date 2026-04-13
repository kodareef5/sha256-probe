# The Cascade Diagonal Structure Theorem

Date: 2026-04-13 07:00 UTC

## The Complete State-Diff Picture

After cascade round r (state diffs, CONST = candidate-specific constant):

```
       | da | db | dc | dd | de | df | dg | dh |
  r=57 |  0 |  0 | C1 | C2 | C3 | C4 | C5 | C6 |
  r=58 |  0 |  0 |  0 | C1 |*V* | C3 | C4 | C5 |
  r=59 |  0 |  0 |  0 |  0 | C1 |*V* | C3 | C4 |
  r=60 |  0 |  0 |  0 |  0 |  0 | C1 |*V* | C3 |
  r=61 |  0 |  0 |  0 |  0 |  0 |  0 | C1 |*V* |
  r=62 |  0 |  0 |  0 |  0 |  0 |  0 |  0 | C1 |
  r=63 |  0 |  0 |  0 |  0 |  0 |  0 |  0 |  0 | ← COLLISION
```

Where:
- **0**: Forced zero (cascade construction + shift register)
- **C1,C2,...**: Constants determined by state56 only (candidate property)
- ***V***: The ONE variable position per round (takes 2^hw(C1) values)
- C1 = db56 (the b-register diff at state56, propagated everywhere)

## Two Diagonal Waves

1. **a-path wave** (upper-left): da=0 at r57, then db=0, dc=0, dd=0
   by r59. This is the shift register propagation of da=0.

2. **e-path wave** (lower-right): de=0 at r60, then df=0, dg=0, dh=0
   by r63. This wave starts 3 rounds later because de=0 requires
   dd=0 first (which arrives at r59) PLUS W60 cascade zeroing.

3. **Variable diagonal** (*V*): Exactly one register per round carries
   the Maj-function freedom. It moves from de (r58) through df (r59),
   dg (r60), dh (r61). Each variable takes |2^hw(db56)| distinct values.

## For Collision: The Variable Must Also Reach Zero

At r62: dh = C1 (constant = db56). At r63: dh = *V* (variable).
The collision requires dh63 = 0, which constrains *V* at r63.

This means: the collision system has hw(db56) binary degrees of freedom
at each of 4 rounds (58-61), minus the constraint that dh63 = 0.

Total effective freedom: ~4 × hw(db56) - constraints from W61-W63
(schedule-determined).

## Implication

The cascade collision is a THIN DIAGONAL PATH through state-diff space.
The "width" of this path is determined by a single parameter: hw(db56).

For the paper: this gives the complete structural characterization of
the sr=60 cascade mechanism. The collision problem reduces to finding
message words that navigate this thin diagonal path to the origin.
