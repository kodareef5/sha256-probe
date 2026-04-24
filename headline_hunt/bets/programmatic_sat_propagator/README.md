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

- [ ] **API survey.** Read CaDiCaL IPASIR-UP docs / Alamgir et al. SAT/CAS paper
  (literature.yaml#alamgir_nejati_bright_sat_cas_sha256) for closest analog.
- [ ] **Propagation rule set.** Sketch which carry modes, which offsets, which
  W[60] constraints to expose. Document in `propagators/SPEC.md`.
- [ ] **N=8 prototype.** Implement against CaDiCaL external propagator.
- [ ] **Conflict-count comparison** vs. vanilla Kissat / CaDiCaL on same instance.
- [ ] **Decision gate**: 10x conflict reduction at N=8 OR kill.

## Related

- Adjacent to `chunk_mode_dp_with_modes` — different implementation route, similar
  underlying state-quotient idea.
- AlphaMapleSAT (literature.yaml) is methodologically related (structured cube
  selection); read before designing branching.
- If successful, enables a new run-class in `sr61_n32`.
