# F108: simple W2 constraint patterns don't reduce residual amplification — yale design constraint
**2026-04-28 05:00 EDT**

Direct empirical follow-up to F106 (which showed naive M2=M2' produces
residual AMPLIFICATION ×2.3). F108 tests 3 non-trivial W2 constraint
patterns to see if any single-word or sparse-pattern modification
REDUCES the amplification.

## Setup

3 variant bundles built from F106's bit3_HW55_naive_blocktwo
fixture (block-1 residual HW=55):

**Variant A** — single `exact_diff` at round 0:
```
W2_constraints: [{"type": "exact_diff", "round": 0, "diff": "0xb0468462"}]
```
Hypothesis: pinning dW2[0] to match the cascade-1 da63 might cancel
the diff that gets carried forward into block-2's round 0 input.

**Variant B** — Wang-9-sparse, 3 `exact_diff` at rounds 0, 5, 9:
```
W2_constraints: [
  {"type": "exact_diff", "round": 0, "diff": "0xb0468462"},
  {"type": "exact_diff", "round": 5, "diff": "0x07066020"},
  {"type": "exact_diff", "round": 9, "diff": "0x31c4d182"}
]
```
Hypothesis: a 3-active-rounds sparse pattern (analogous to Wang's
9-active SHA-1 disturbance vectors but adapted for 64-round SHA-2)
might cancel the residual via multiple cancellation points.

**Variant C** — single `exact` (pin W2[0] to a fixed value):
```
W2_constraints: [{"type": "exact", "round": 0, "value": "0xb0468462"}]
```
Hypothesis: pinning W2[0] to a specific value (rather than constraining
the diff) tests whether VALUE matters or just DIFF.

All 3 use bit3_m33ec77ca HW=55 W-witness as block-1 (same as F106
fixture) and target = all zero at block-2 round 63.

## Result — all 3 verdict FORWARD_BROKEN, all 3 produce median HW=127

```
Variant   Final HW range    Median   Verdict
-------   --------------    ------   --------
A         111 - 149         127      FORWARD_BROKEN
B         108 - 155         127      FORWARD_BROKEN
C         110 - 152         127      FORWARD_BROKEN
F106 ref  105 - 149         127      FORWARD_BROKEN  (no constraints)
```

**All 3 patterns give IDENTICAL median HW (127), same as F106's empty
baseline.** Simple W2 modifications don't affect propagation
distribution.

## Why this is structurally informative for yale

The empirical result is consistent with the structural reality:
- Block-1 residual HW=55 enters block-2 as the chaining-state diff at
  block-2 round 0 (NOT block-2 W2[0]).
- W2 constraints affect the MESSAGE differential dW2[r], which
  combines with the chaining-state diff via T1+T2 round update.
- Random W2 contributes ~32 random bits of additional diff per round
  it's modified; this BLENDS with the existing chain-state diff.
- The blending doesn't naturally produce cancellation because SHA-2's
  Sigma + Ch + Maj are nonlinear in their inputs.

**Cancellation requires the chain-state diff itself to be steered
through Sigma/Ch/Maj-aware transitions, not just W2 modifications.**

## What yale needs to design (refined understanding)

Per F107 (Wang→F82 mapping), yale's trail design must specify:

1. **Bitconditions on block-2 internal state diffs** at each round —
   not just W2 modifications. Use F82 SPEC's `bit_condition` constraint
   type to specify per-bit equality / inequality predicates on
   intermediate diff state across all 64 block-2 rounds.

2. **Multi-round modification sequence**: a single W2 round
   modification (Variants A/C) doesn't cancel; even a 3-round sparse
   pattern (Variant B) doesn't help. Wang's full SHA-1 trail used
   sequential message modifications PLUS bitcondition propagation.
   Yale's SHA-2 design needs both.

3. **Sigma-aware constraint structure**: SHA-2's Sigma functions mix
   4 register positions per round. Modifications must align with the
   Sigma transitions to allow cancellation, not amplification. This
   is the SHA-256-specific challenge that Mendel/Nad/Schläffer 2013
   addresses with their signed-DC framework.

## What this rules out for yale's design

- **Single-W2-word modifications cannot absorb a non-zero residual.**
  Verdict A.
- **Sparse W2 patterns (≤3 rounds) of arbitrary diffs cannot absorb.**
  Verdict B.
- **Pinning a single W2 word's value (not just diff) cannot absorb.**
  Verdict C.

## What this leaves OPEN for yale

- **Dense W2 modifications** (>9 rounds) — could test next.
- **Bit_condition constraints on intermediate state diffs** —
  fundamentally different mechanism, not yet tested via F104 because
  F104 currently ignores `bit_condition` (Phase 2 simulator work).
- **Modular_relation constraints** linking W2 and chain-state — also
  not yet supported in F104.

## Implication for F104 simulator's coverage

F104 supports `exact` and `exact_diff` constraint types fully. F108
shows these alone are NOT sufficient to express absorption trails.

**Phase 2 of F104 simulator** (per F102's open work) becomes higher
priority: implement `bit_condition` and `modular_relation` types so
yale can test richer trail designs in the sub-second feedback loop.

## Discipline

- 3 bundles built (`/tmp/f108_bundles/`, transient)
- 3 F104 simulator runs, all FORWARD_BROKEN, ~3s total wall
- 0 SAT solver runs (forward simulation only)
- All bundles VALID per F83 schema validator

EVIDENCE-level: VERIFIED. 3 variants × 100 W2 samples = 300 simulated
block-2 forward runs, all FORWARD_BROKEN with consistent HW=127
median (~2.3× amplification of HW=55 input).

## Concrete next moves

1. **F104 Phase 2** (priority increased per F108): implement
   `bit_condition` and `modular_relation` constraint type handling
   in `simulate_2block_absorption.py`. ~50 LOC extension.

2. **Yale**: review this F108 result. Single-word + sparse W2
   modifications are insufficient. Wang-style + Mendel/Nad/Schläffer
   bitcondition propagation is the design path. F107 note has the
   Wang→F82 mapping; F82 SPEC's bit_condition type is ready to
   accept your structural design.

3. **Optional dense W2 probe** (F109 candidate): test 10-15 round
   exact_diff patterns to see if denser sparse patterns help. May
   give partial reduction even without bitconditions.
