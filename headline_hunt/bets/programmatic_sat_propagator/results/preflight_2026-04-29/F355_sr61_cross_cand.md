---
date: 2026-04-29
bet: programmatic_sat_propagator × cascade_aux_encoding
status: SR_INVARIANT — F343 preflight produces same clauses at sr=60 and sr=61
---

# F355: F343 preflight at sr=61 across 5 cands — sr-invariant clause library

## Setup

F354 found F343 preflight on bit31 sr=61 force-mode produces SAME
clauses as sr=60. F355 extends to 5 more cands to test universality.

## Result

Cross-cand cross-sr table (force-mode, F343 minimal preflight 2 clauses):

| Cand       | sr=60 dW57[0] forced | sr=61 dW57[0] forced | sr=60 W57[22:23] | sr=61 W57[22:23] |
|---|:---:|:---:|---|---|
| bit0       | 0 | **0** | (0, 1) | (0, 1) |
| bit10      | 0 | **0** | (0, 1) | (0, 1) |
| bit11      | 1 | **1** | (0, 0) | (0, 0) |
| bit13      | 0 | **0** | (0, 0) | (0, 0) |
| bit17      | 1 | **1** | (0, 1) | (0, 1) |
| bit31      | 1 | **1** | (0, 1) | (0, 1) |

**Every cand has IDENTICAL preflight output across sr=60 and sr=61
force-mode.** The F343 mined clauses are sr-invariant for force-mode.

## Findings

### Finding 1 — F343 preflight is sr-invariant for force-mode

The 2 mined clauses (dW57[0] unit + W57[22:23] pair) are produced
identically at sr=60 and sr=61 force-mode for the same cand. Per-cand
mining at sr=60 (cheaper, more existing infrastructure) gives the
clauses for sr=61 (the open frontier).

### Finding 2 — Confirms structural argument

The W57 differential constraints come from the cascade-1 hardlock at
round 60 (sr=60) or round 60 / 61 (sr=61). Both sr levels enforce
cascade-1 absorption with the SAME differential structure at round 57.
Differences in sr level only affect the LATER round-60 / round-61
constraints, not the round-57 dW values.

### Finding 3 — Phase 2D propagator design simplification

For the F327 IPASIR-UP propagator's preflight step:

```
For new cand (sr, M0, fill, kernel_bit):
  if cand_already_mined_at_any_sr_force_mode(cand):
      reuse_clauses(cand)  # sr-invariant per F355
  else:
      run_preflight(cand, sr=60, mode=force)  # 20s, cheaper sr
      cache_clauses(cand)
  inject_via_cb_add_external_clause(clauses)
```

This means the propagator doesn't need separate per-sr mining. One
~20s preflight per cand serves all sr levels for force-mode encodings.

### Finding 4 — F235 hard instance speedup pathway

F235 is sr=61 cascade encoder (NOT aux_force). The F343 mined clauses
were derived from aux_force, but the round-57 dW constraints are the
same algebraic structure (cascade-1 hardlock at round 60 propagating
back through schedule recurrence). Re-mining on the F235 CNF directly
should produce the same clauses (translated to F235's var IDs).

If validated: F343 minimal preflight on F235 + injection should give
similar 5-14% conflict reduction per F347/F348 measurement, applied
to F235's 562s-848s hard instance.

## Compute

- ~100s total wall (5 cands × ~20s preflight each).
- 5 fresh sr=61 force-mode CNFs + varmaps generated.
- 0 long compute.

## What's shipped

- 5 sr=61 preflight JSONs in `F355_sr61/` subdir.
- This memo.

## Concrete next moves

(a) **Re-mine on F235 cascade-encoder CNF directly** (different encoder
    than aux_force). Will require generating F235-style cascade
    encoder's varmap or deriving dW57 var IDs from CNF structure.
    ~30 min work to adapt.

(b) **Test injection on F235**: run cadical 1h on F235 baseline vs
    F235 + 2 mined clauses. Measure speedup (target: 5-14% per
    F347/F348).

(c) **Document the sr-invariant property** in the IPASIR_UP_API.md
    survey for the next implementation cycle.

## Cross-machine status

The cross-machine yale F378 → macbook F343/F347/F348/F354/F355 chain
has now produced:
1. Conflict-guided cube mining (yale)
2. Per-cand UNSAT polarity discovery (yale F384)
3. Cross-cand polarity flip pattern (macbook F340)
4. 1-bit and 2-bit clause classes (macbook F341/F342)
5. preflight_clause_miner.py tool (macbook F343)
6. Empirical 5-14% speedup measurement (macbook F347/F348)
7. Cross-mode validation: force vs expose (macbook F351)
8. **Sr-invariant validation: sr=60 vs sr=61** (macbook F354/F355, this memo)

The propagator design is now empirically grounded across:
- 6 cands (5 + bit31 reference)
- 2 encoding modes (force, expose)
- 2 sr levels (60, 61)

Ready for Phase 2D implementation when build cycles permit.
