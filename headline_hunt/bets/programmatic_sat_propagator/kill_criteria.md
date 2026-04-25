# Kill criteria — programmatic_sat_propagator

## #1 — Conflict-count reduction below 10×

**Trigger**: Once the propagator is implemented and benchmarked, conflict count
is within an order of magnitude of vanilla cadical/kissat on the same instance.

**Why this kills**: 10× is roughly the threshold below which custom propagation
implementation cost exceeds the gain. Below that, plain CDCL with better
encoding (`cascade_aux_encoding`) is more cost-effective.

**Required evidence**: conflict-count-to-SAT comparison on multiple instances.

**Status (2026-04-25, end of session)**: cannot directly measure conflicts-to-SAT
because both ON/OFF runs hit budget (50k, 500k) without finding SAT. INDIRECT
evidence (kill criterion #3 below) suggests this gate is unlikely to be passed.

## #2 — Implementation cost dominates CPU savings

**Trigger**: Propagator works but adds enough per-decision overhead that wall
time at N=10/N=12 is no better than vanilla even when conflicts are fewer.

**Status (2026-04-25)**: Wall-time slowdown is **~1.9× across both 50k and 500k
budgets** on top firing kernels (bit-19, bit-25, bit-31). Per-conflict overhead
is approximately constant; doesn't amortize at higher budgets.

## #3 — Rule firing is preprocessing-phase only (NEW, 2026-04-25)

**Trigger**: Propagator's main rules fire ONLY in the early-CDCL phase (e.g.,
during preprocessing or first ~50k conflicts) and fall silent during deep
search. This makes the propagator structurally equivalent to Mode B's static
unit clauses (cascade_aux_encoding's force mode) — but at higher implementation
and runtime cost.

**Why this kills**: Mode B already provides preprocessing-phase cascade-zero
constraint injection via STATIC unit clauses, with NO propagator overhead.
If the propagator's dynamic firing is also preprocessing-only, it offers no
value-add over Mode B. The ~750 LOC + IPASIR-UP dependency is unjustified.

**Status (2026-04-25)**: **EMPIRICALLY FIRED for Rule 4@r=62.** Sweep across
top 3 firing kernels (bit-19, bit-25, bit-31) shows Rule 4 fires the EXACT
SAME NUMBER of times at 50k as at 500k:
  bit-19: 209 / 209 (zero new fires across 50k-500k)
  bit-25: 249 / 249
  bit-31: 201 / 201
All firings happen in the first ~50k conflicts; ZERO during deep search.

Reference: `results/phase2c_rule4_500k_2026-04-25/RESULT.md`.

**This kill criterion is FIRED for Rule 4 in isolation.** Bet stays alive
ONLY IF a future rule (Rule 6 at r=63, smarter Rule 4 trigger, or new
mechanism) demonstrates continuous firing during deep search.

## Reopen triggers

- New IPASIR-UP-compatible solver advance with significantly different
  decision strategy (e.g., one that backtracks deeply enough to re-decide
  the cascade-input bits).
- New cascade theory gives propagation rules with formal soundness proofs
  AND empirical evidence of continuous firing during long CDCL search.
- A specific cascade-DP candidate is identified where vanilla cadical
  cannot find SAT in 100M+ conflicts, but the propagator can. (This is
  the only path to a true headline result — and would be earned only by
  finding the candidate, not by improving the propagator alone.)

## Decision (2026-04-25)

**Bet status: HALF-KILLED.** Kill criterion #3 is fired for Rule 4 alone.
The bet is NOT yet fully killed because:
- Rule 6 at r=63 (modular Theorem 4 with two varying inputs) hasn't been
  implemented — could collectively cover different parts of the search space.
- A "smarter trigger" alternative (incremental partial-bit reasoning, fire
  on new bit becoming determinable instead of sample-based) is untested.

**Recommendation: do NOT continue compute-heavy validation of Rule 4 alone.**
The path forward, if any, is through Rule 6 or a smarter-trigger variant.
Both are next-session implementation work. Until then, treat the bet as
"engineering substrate complete, value-add hypothesis empirically refuted
on Rule 4."

The cascade_aux_encoding bet's Mode B is the practical alternative for
preprocessing-phase cascade structure injection. It achieves ~80% of
the propagator's effect with 10% of the complexity.
