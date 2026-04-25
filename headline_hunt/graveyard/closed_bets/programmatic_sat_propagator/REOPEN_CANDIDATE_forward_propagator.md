# Reopen candidate: q5/forward_propagator.cpp
**2026-04-25 evening** — programmatic_sat_propagator graveyard reopen candidate
discovery. (Per GPT-5.5 review: narrow "killed" claims, mark reopen criteria.)

## What the killed bet actually killed

The KILL_MEMO for programmatic_sat_propagator was specific: the **Rule-4 propagator
design** (watching ACTUAL register-value variables via diff-aux, triggering on
partial assignments) doesn't fire deeply. CDCL navigates by deciding XOR-diff
aux variables; actual-register-value rules go silent during deep search.

**It did NOT kill all programmatic SAT for SHA-256.** Per the corrected
TARGETS.md note: "Future propagators must operate on diff-aux variables (which
CDCL DOES decide) or actively shape CDCL decisions via cb_decide()."

## What forward_propagator.cpp does differently

`q5_alternative_attacks/forward_propagator.cpp` (458 LOC, uses CaDiCaL IPASIR-UP
ExternalPropagator API):

- Watches the **256 free-word variables** (W1[57..60] × 32 bits = 128 vars,
  similar for W2). These are directly decided by CDCL.
- Trigger: when all 32 bits of a free word are assigned, run forward SHA
  computation natively in C++ with the assigned word.
- Compute the resulting state register values (a57, e57, etc.) for that path.
- Propagate any collision-register constraints whose values are now determined
  (e.g., if pair-1 a57 = 0x..., and pair-2 a57 = 0x..., emit any
  consequent diff-aux unit clauses).

This is structurally different from the killed Rule-4 propagator:
- Triggers on COMPLETE word assignment (not partial bits).
- Forward-propagates from FREE-WORD literals (which CDCL decides) toward
  diff-aux outcomes.
- No reliance on ACTUAL-register-value triggers.

## Whether it's a reopen

Reopen criterion per kill_criteria.md:
> "A new propagator design that operates on diff-aux variables (CDCL's natural
>  decision basis) and demonstrates ≥2× speedup over Mode B at 500k+ conflicts."

forward_propagator.cpp meets the FIRST half (operates on free-word literals →
diff-aux propagation). The SECOND half (≥2× speedup) requires empirical run
against current Mode B baseline.

**Reopen request would require:**
1. Compile & run forward_propagator.cpp at sr=61 cascade CNF (current bet
   instances).
2. Compare conflict count vs Mode B at matched 500k conflict budget.
3. If ≥2× faster, formally reopen.

## What I'm NOT doing right now

- Not actually compiling/running forward_propagator. That needs a focused
  test bench setup (separate CaDiCaL build with IPASIR-UP).
- Not formally reopening the bet.
- Not committing to porting forward_propagator to current encoder format.

## Concrete handoff for next worker

If a future worker wants to attempt reopen:
1. Read `q5_alternative_attacks/forward_propagator.cpp` (458 LOC).
2. Build instructions in the file header.
3. Need a varmap.json from the current cascade encoder (see
   `bets/cascade_aux_encoding/encoders/cascade_aux_encoder.py`).
4. Wire the propagator's word-watch list to current free-word vars
   (likely already correctly identified in the existing varmap format).
5. Run `forward_propagator <cnf> <varmap> <timeout>` at 500k conflicts.
6. Compare against `kissat --conflicts=500000` baseline.

Estimated effort: 1-2 days focused work.

## Logging to mechanisms.yaml

Add to `programmatic_sat_cascade_propagator.reopen_candidates`:
- `q5_alternative_attacks/forward_propagator.cpp` — diff-aux-friendly design,
  unevaluated against current Mode B baseline.
