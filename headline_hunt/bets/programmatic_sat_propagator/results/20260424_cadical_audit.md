# CaDiCaL audit for IPASIR-UP support

**Local install**: CaDiCaL 3.0.0 at `/opt/homebrew/bin/cadical`.

CLI inspection:
- `--externallrat` — external LRAT proof emitter (proof verification, not propagation)
- `--exteagerrecalc` — internal heuristic about external tools recalculating levels
- No `--external-propagator` or similar CLI flag.

**Conclusion**: IPASIR-UP is **not** a CLI feature. It's a library API exposed through `libcadical`'s C++ bindings (and the IPASIR-UP wrapper interface). To use it for `programmatic_sat_cascade_propagator`, the work is:

1. Write C++ that links against `libcadical` (or use the IPASIR-UP C wrapper).
2. Implement the propagator interface: `notify_assignment`, `notify_new_decision_level`, `notify_backtrack`, `cb_check_found_model`, `cb_decide`, `cb_propagate`, `cb_add_reason_clause`, `cb_has_external_clause`, `cb_add_external_clause_lit`.
3. Encode the cascade-aware reasoning rules in `cb_propagate`: when a state is partially assigned, check if cascade constraints (Theorems 1-4) are violated; if so, return a forced literal.
4. Build & link & test.

This is **multi-day C++ work**, not a 30-min audit ship. Below is a sketch of what the propagation rules would look like:

## Sketch: cascade-aware propagation rules

State the propagator tracks:
- Current variable assignments (provided by CaDiCaL).
- Whether enough W[57..60] bits are decided to compute round-r state for some r.

When enough assignments are present:
- Compute T1, T2 incrementally via the standard SHA-256 round.
- Check the cascade invariants:
  - At round 57: da_57 = 0? If forcing variables conflict, fail fast.
  - At round 58/59: db_58 = 0? dc_59 = 0? (shift register propagation)
  - At round 60: de_60 = 0? (cascade-2)
  - At round 61: dA_61 = dE_61? (Theorem 4)
  - At round 63: full collision?
- For each violation, emit a forced literal that flips the offending bit, with a reason clause linking it to the W variables at fault.

The propagator's win is **early termination**: instead of CDCL discovering cascade-incompatible assignments via thousands of conflicts, the propagator detects the violation as soon as enough W bits are set.

## Recommended next steps for the bet

1. **Reference**: Alamgir/Nejati/Bright SAT/CAS for SHA-256 (literature.yaml id=alamgir_nejati_bright_sat_cas_sha256, confidence=needs_verification). Their work is the closest analog. Verify the citation, find the GitHub repo if any, and read their propagator design before writing our own.
2. **Prototype scope**: Don't tackle full SHA-256 at first. Build the propagator for the cascade chain rounds 57-60 only; let CaDiCaL handle the rest. This is testable at N=8 first.
3. **Toolchain check**: confirm CaDiCaL 3.0.0 exposes IPASIR-UP. If not, install Kissat-mab-master or upgrade CaDiCaL — the API has matured rapidly post-2024.

## Status update

Bet stays `open`. owner stays `unassigned` — the multi-day C++ build is a real commitment, not a side project. The literature scan is the right first step for any worker who does pick this up.
