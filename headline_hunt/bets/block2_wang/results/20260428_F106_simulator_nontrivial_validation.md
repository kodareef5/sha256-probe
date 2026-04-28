# F106: F104 simulator validated on non-trivial bundle — FORWARD_BROKEN detection works
**2026-04-28 04:25 EDT**

Direct follow-up to F104. F104 was validated end-to-end on the
m17149975 trivial-collision bundle (block-1 residual HW=0 →
collision). F106 validates F104's FORWARD_BROKEN detection on a
deliberately-non-trivial test fixture.

## Setup

Constructed `bit3_HW55_naive_blocktwo.json` from F94's bit3_m33ec77ca
HW=55 W-witness:

```
block1.W1_57_60: [0x3d7df981, 0xae13c3a4, 0x49c834bd, 0x7619ac16]
block1.W2_57_60: [0x36ed80fa, 0x8a9db1fa, 0x5c63c09d, 0x0a66d006]
block1.residual_state_diff: { da63=0xb0468462, db63=0x81c0000e,
    dc63=0x07066020, dd63=0x00000000, de63=0x31c4d182,
    df63=0x8801404b, dg63=0x0d1e2020, dh63=0x00000000 }
block1.residual_hw: 55  (per F94 verified UNSAT)

block2.W2_constraints: []  (no W2 modifications — M2 = M2', zero diff)
block2.target_diff_at_round_N: all zero (collision target)
```

This is structurally a "naive" block-2: the cascade-1 block-1 produces
a non-zero residual (HW=55), and block-2 with NO constraints means
M2=M2' so the diff just propagates through block-2 unmodified by any
absorption scheme.

## Result — FORWARD_BROKEN, as expected

```
Block-1 residual HW: 55 (matches bundle ✓)
Block-2 forward simulation:
  Samples:                        100 (random W2 messages, M2=M2')
  Block-2 round-63 final HW range: 105 - 149 (median 127)
  Target HW:                      0
  Collisions (HW=0):              0
  Near-residuals (HW≤4):          0

Verdict: FORWARD_BROKEN
```

F104 simulator correctly detects:
1. Bundle's claimed block-1 residual matches actual forward sim
2. Block-2 cannot achieve the all-zero target without constraints
3. Verdict FORWARD_BROKEN, suggesting yale review block-2 design

## Important structural finding: residual AMPLIFICATION

A naive guess might be that "block-2 with M2=M2' propagates the
residual unchanged" — output HW = input HW = 55. **This is wrong.**

The actual behavior: SHA-256's nonlinear round operations
(Sigma0/Sigma1/Ch/Maj + carries) AMPLIFY a non-zero chaining-state
diff through 64 rounds. Block-1 residual HW=55 → block-2 final
HW=105-149 (median 127, ~2.3× amplification).

This is the deep structural reason Wang's MD5 differential trick
works: cancellation requires *specific* W2 modifications applied at
*specific* rounds to cancel the residual diff cleanly. Random W2
amplifies, doesn't cancel.

For yale's block-2 design: the absorption pattern needs to be
**structural**, not statistical. A random sample of W2 messages will
amplify the residual (per F106's 100/100 amplification). Yale's trail
must specify the exact modification structure that achieves
cancellation.

## What this validates about F104

F104 simulator's verdict logic now empirically validated across both
verdict branches:
- **COLLISIONS_FOUND** (F104 m17149975 test): trivial round-trip
  produces 100/100 HW=0 → collision
- **FORWARD_BROKEN** (F106 bit3 test): non-trivial residual + naive
  block-2 produces 100/100 amplification → forward broken

The middle verdict (NEAR_RESIDUALS_FOUND) would arise from a
*partial* Wang trail design where some constraints reduce the
residual but don't fully cancel it. Yale's trail iterations would
naturally produce this verdict before reaching COLLISIONS_FOUND.

## Implication for yale's trail iteration

Yale's design loop:
1. Draft block-2 W2 constraints (initial guess)
2. `validate_trail_bundle.py` — schema check (F83)
3. `simulate_2block_absorption.py` — forward consistency (F104 + F106
   validates this works on non-trivial cases)
4. If FORWARD_BROKEN → revise constraints; if NEAR_RESIDUALS → tighten;
   if COLLISIONS → submit to SAT verifier (F84)

The simulator is a sub-second feedback loop. Yale gets actionable
"yes/no/maybe" verdicts before paying SAT compute.

## Discipline

- 1 sample bundle written (`bit3_HW55_naive_blocktwo.json`)
- 1 simulator run, 100 W2 samples, ~0.3s wall
- No solver runs (forward simulation only)
- Validates F104's empirical correctness on the non-trivial branch

EVIDENCE-level: VERIFIED. F104 simulator handles both trivial-collision
and non-trivial-broken cases correctly.

## Reproduce

```bash
python3 validate_trail_bundle.py bit3_HW55_naive_blocktwo.json
# → VALID

python3 simulate_2block_absorption.py bit3_HW55_naive_blocktwo.json
# → Verdict: FORWARD_BROKEN, block-2 final HW range 105-149
```

## Concrete next moves

1. **Phase 2 of F104 simulator**: handle `modular_relation` and
   `bit_condition` W2 constraint types (currently ignored). Extends
   to richer trail designs.
2. **Yale's first non-trivial trail attempt**: yale ships a partial
   block-2 design; F104 reports NEAR_RESIDUALS or FORWARD_BROKEN.
   Iterate until COLLISIONS.
3. **2-block SAT encoder extension** (F84 gap): only needed once
   yale's trail reaches COLLISIONS-found via F104. Pre-yale work
   not required.
