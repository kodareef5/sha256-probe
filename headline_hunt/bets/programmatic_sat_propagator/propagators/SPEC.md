# SPEC — programmatic SAT propagator for cascade-DP SHA-256 collisions

This document specifies the propagation rule set for an external IPASIR-UP propagator that injects cascade-DP structural reasoning into a CDCL SAT solver (CaDiCaL via IPASIR-UP, or Kissat via fork+UP-extension if available).

## Why a custom propagator

The encoder-only approach (`bets/cascade_aux_encoding`) injects cascade structure at the CNF level via Theorems 1-4. Mode B forces `dE[61..63] = 0` and `dA[61] = dE[61]` as hard CNF constraints. Empirically this gives no observable speedup vs. standard encoding at 90-min budget (TIMEOUT × 7 runs).

The hypothesis: CNF can express the constraints, but CDCL has to *discover* the propagation pattern through resolution. A propagator that DIRECTLY enforces modular-difference reasoning at the variable level can fire faster than CDCL's resolution chains, especially on the high-degree non-linear constraints (modular addition, Sigma0/Sigma1 rotations, Maj/Ch).

## Propagator API model

Use IPASIR-UP (CaDiCaL ≥ 1.7). The propagator subclasses `CaDiCaL::ExternalPropagator` and overrides:
- `notify_assignment(literal)` — called on every variable decision/propagation.
- `cb_check_found_model(model)` — called on a candidate full assignment.
- `cb_propagate()` — return next forced literal (or 0 = no propagation).
- `cb_add_reason_clause_lit(propagated_lit)` — explain a forced literal as a clause.
- `cb_decide()` — optional: external decision heuristic.

The propagator maintains a parallel "differential state model" mapping CNF variables to:
- bits of `dW[57..63]` (delta-W values),
- bits of `dA[r], dB[r], ..., dH[r]` for r ∈ {56, 57, ..., 63},
- bits of `a[r]`, `e[r]` ACTUAL register values (needed for non-linear constraints involving Sigma0, Maj, Ch).

When CDCL assigns a variable, the propagator updates its state model and checks whether any of the cascade rules now propagates new information.

## Propagation rules (ordered by trigger speed)

### Rule 1 — Cascade diagonal (Theorem 1)

**Trigger**: `dA[57]` value bits decided.
**Propagation**: enforce `dA[57] = 0`. If any bit decided to non-zero → conflict; if not yet zero → propagate to zero.
Repeat for r = 58, 59, 60 (`dA[r] = 0`), and for `dB[58..60]`, `dC[59..60]`, `dD[60]` per Theorem 1's diagonal.

**Cost**: O(32) checks per assignment in the cascade region. Cheap.

### Rule 2 — dE[60] = 0 (Theorem 2)

**Trigger**: any bit of `dE[60]` decided.
**Propagation**: force all 32 bits of `dE[60]` to zero. If any decided to non-zero → conflict.

### Rule 3 — Theorem 3 three-filter

In MODE_FORCE only: enforce `dE[61] = dE[62] = dE[63] = 0` (32 × 3 = 96 bits).

### Rule 4 — Modular Theorem 4 unified (cascade-aware)

This is the NEW propagation enabled by the unified Theorem 4 extension:

```
For r ∈ {61, 62, 63}:
    da_r − de_r ≡ dT2_r  (mod 2^32)
where:
    dT2_r = dSigma0(a_{r-1}) + dMaj(a_{r-1}, b_{r-1}, c_{r-1})
```

**Specialization at r=61**: `a_60, b_60, c_60` all cascade-zero (same value in pair-1 and pair-2), so `dT2_61 = 0`. Rule fires `dA[61] = dE[61]` modular as soon as cascade is established at round 60. This is the original Theorem 4 with explicit modular semantics (NOT XOR — see `20260425_spec_bug_retraction.md`).

**Trigger at r=62, r=63**: when actual values `a_{r-1}, b_{r-1}, c_{r-1}` (in either pair-1 or pair-2) are sufficiently determined that `dSigma0(a_{r-1})` and `dMaj(...)` can be partially evaluated, propagate constraints on `dA[r] − dE[r]`.

**Cost**: O(32) per Sigma0/Maj evaluation, fired at most once per (a, e)-bit assignment. Aggregated cost ~O(N^2) per cascade-trace.

### Rule 5 — R63.1 register equality (cascade memory)

```
dC[63] ≡ dG[63]  (mod 2^32)
```

Both equal `dA[61] = dE[61]` (Theorem 4 r=61 specialization), shifted forward via the SHA-256 register pipeline.

**Trigger**: `dC[63]` or `dG[63]` bits decided. **Propagation**: 32 bit-equality clauses.

### Rule 6 — Modular sum at r=63 (R63.3)

```
dA[63] − dE[63] ≡ dT2_63  (mod 2^32)
where dT2_63 = dSigma0(a_62) + dMaj(a_62, a_61, a_60)
```

**Trigger**: when `(a_60, a_61, a_62)` actual values + `dA[63]` bits or `dE[63]` bits are decided, propagate the modular sum.

This is the MOST POWERFUL rule. It links the 32-bit `dA[63]` and 32-bit `dE[63]` values via a *value-dependent* modular sum, which CDCL would have to derive through dozens of Sigma0/Maj clauses.

### Rule 7 — Schedule-determined W[60] (sr=61 only)

```
W[60] = sigma1(W[58]) + W[53] + sigma0(W[45]) + W[44]   (mod 2^32)
```

Once W[44], W[45], W[53], W[58] are partially determined (and they are largely fixed by the candidate's m[0..15]), `W[60]` is deterministically constrained.

**Trigger**: any of the relevant W[t] bits decided.

### Rule 8 — Impossible-residue early termination

Maintain a hash table of "failed residual interfaces" — partial assignments at the cascade boundary (rounds 56-60) that have led to conflict in past restarts. On a new restart, if the same interface re-occurs, propagate UNSAT directly without re-deriving.

**Cost**: O(1) lookup per cascade-state hash.

## What this rule set DOES NOT do

- **Does not** modify the variable order or CDCL decision strategy directly. (Rule 8's `cb_decide()` extension is optional.)
- **Does not** enforce any constraint that's not implied by the underlying CNF. The propagator is *helpful* (faster propagation), not *restrictive* (more solutions).
- **Does not** depend on candidate m[0..15] specifics — all rules are candidate-independent.

## Implementation roadmap

### Phase 1 — N=8 prototype (1-2 weeks)
- Stub `propagators/cascade_propagator.py` as a Python-side simulator (no CaDiCaL link).
- Verify rules 1-7 fire correctly on the existing N=8 CNFs.
- Measure: with vs. without each rule, count CDCL conflicts on a known N=8 instance.

### Phase 2 — IPASIR-UP integration (2-4 weeks)
- C++ implementation linked against CaDiCaL.
- Build via `cmake -DCADICAL_VERSION=...`.
- Run on N=8, N=10, N=12 cascade-aux CNFs.
- Compare conflict count vs. vanilla CaDiCaL on the same instances.

### Phase 3 — Decision gate
- If 10x conflict reduction at N=8: scale to N=16, N=32.
- If <2x reduction: kill the bet (per `kill_criteria.md`).
- If 2-10x: triage — is the bottleneck the propagator or CDCL itself?

## References

- Alamgir / Nejati / Bright SAT/CAS — closest analog, programmatic propagation for SHA-1 / preimage. Literature.yaml#alamgir_nejati_bright_sat_cas_sha256 (needs-verification confidence).
- Cadical IPASIR-UP API: https://github.com/arminbiere/cadical (head + tutorials).
- AlphaMapleSAT (arXiv:2401.13770) — programmatic cube selection, methodological influence.

## Status of structural foundation (as of 2026-04-25)

The propagator's RULE 4, 5, 6 depend on the unified Theorem 4 extension and the R63 modular constraints. These are now **empirically locked**:
- Unified Theorem 4: 105,700/105,700 records (104,700 corpus + 1000 fresh + 50 + 50 trail starters).
- R63.1, R63.3: same scale.
- R61.1, R62.1, R62.2, R63.2: 4000/4000 fresh samples across two kernel families and three candidates.

References: `bets/mitm_residue/results/20260425_residual_structure_complete.md`, `20260425_theorem4_unified_104k.md`.

So the propagator's structural rules can be implemented without further validation work. The work is engineering: API integration, C++ glue, comparative experimentation.
