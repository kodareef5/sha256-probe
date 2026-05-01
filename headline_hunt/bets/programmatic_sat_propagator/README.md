# bet: programmatic_sat_propagator — SAT solver with SHA-256/cascade propagator

**Priority TBD.** Newly surfaced by GPT-5.5 in the 2nd-wind consultation.

## The bet

Plain CNF + Kissat is a black box; chunk-mode DP requires designing a complete
quotient state. **In between**: a programmatic SAT solver (IPASIR-UP / CaDiCaL
external propagator) that exposes:
- modular-add carry modes,
- cascade offsets,
- schedule-derived W[60] reasoning,
- impossible-residue early termination,
- failed-residual-interface caching.

This is the practical form of the quotient-state idea without writing a full
KC compiler.

## Hypothesis

Custom propagation rules that exploit known cascade structure can:
1. Detect impossible carry/syndrome states earlier than CDCL discovers them on its own.
2. Cache failed residual interfaces across restarts.
3. Reduce conflicts on N=8 by >10x vs. vanilla Kissat.

If it works at N=8 and N=12, scale to N=32 and combine with `cascade_aux_encoding`.

## Headline if it works

Two possible headlines:
- **Sub-brute-force on a nontrivial reduced-SHA target** — algorithmic class change.
- **First sr=61 SAT** via custom propagation that vanilla CDCL couldn't find.

## What's built / TODO

- [x] **API survey.** `propagators/IPASIR_UP_API.md` covers the CaDiCaL 3.0.0
  hook surface and keeps the reopen recipe current.
- [x] **Propagation rule set.** `propagators/cascade_propagator.cc` implements
  the Phase 2B/2C rule substrate.
- [x] **Preflight clause mining.** `propagators/preflight_clause_miner.py`
  ships the F343 two-clause baseline used in F347-F395.
- [x] **Decision-priority specs.** `propagators/build_decision_priority_specs.py`
  emits F397 cb_decide priority lists for the F286 132-bit core and F332
  139-bit stable-core comparison arm.
- [x] **Decision-priority hook wiring.** `cascade_propagator.cc` accepts F397
  priority specs and feeds them into `cb_decide` (F398). Repo-local setup is in
  `propagators/setup_local_deps.sh`; capped/strided priority controls landed in
  F407.
- [x] **Decision-priority matrix runner.** `run_decision_priority_matrix.py`
  emits the exact four-arm F399 command matrix and runs it when headers are
  available.
- [x] **Decision-priority run matrix.** F403/F405 ran the 6-candidate matrix.
  Uncapped priority is harmful; cap-132 is candidate-specific and useful on
  bit10.
- [x] **Bit2 rescue check.** F408-F411 generated bit2's priority spec and found
  F286 cap-132 does not rescue the F343 singleton outlier.
- [x] **F343 mechanism probes.** F413-F416 added targeted first-touch tracing,
  direct F343 injection, clause-placement checks, and `--phase-lit` polarity
  hints. Bit2 is not explained by late F343 assignment, clause placement, or
  wrong default phase; forbidden-pair phase hints make the trace worse.
- [ ] **Next decision gate.** Reopen broad propagator work only if a
  candidate-gated priority/F343 interaction beats F343 on bit2 or another known
  outlier.

## Related

- Adjacent to `chunk_mode_dp_with_modes` — different implementation route, similar
  underlying state-quotient idea.
- AlphaMapleSAT (literature.yaml) is methodologically related (structured cube
  selection); read before designing branching.
- If successful, enables a new run-class in `sr61_n32`.
