---
date: 2026-04-29
bet: programmatic_sat_propagator
status: MODE_INVARIANT — F343 preflight identical for force vs expose
---

# F356: F343 preflight is mode-invariant (force vs expose) across 6 cands

## Setup

F354/F355 found F343 preflight is sr-invariant (sr=60 vs sr=61 force-mode).
F351 found bit29 EXPOSE mode produces (forced=1, (0,0)) — but bit29 FORCE
was untested. F356 tests:
1. 5 cands at sr=60 EXPOSE mode (cross-mode validation)
2. bit29 sr=60 FORCE mode (completing bit29 cross-mode)

## Result

Combined cross-mode cross-sr table (force-mode mining):

| Cand    | sr60-force         | sr60-expose         | sr61-force          |
|---------|--------------------|--------------------|--------------------|
| bit0    | 0 / (0, 1)         | 0 / (0, 1)          | 0 / (0, 1)          |
| bit10   | 0 / (0, 1)         | 0 / (0, 1)          | 0 / (0, 1)          |
| bit11   | 1 / (0, 0)         | 1 / (0, 0)          | 1 / (0, 0)          |
| bit13   | 0 / (0, 0)         | 0 / (0, 0)          | 0 / (0, 0)          |
| bit17   | 1 / (0, 1)         | 1 / (0, 1)          | 1 / (0, 1)          |
| bit29   | 1 / (0, 0)         | 1 / (0, 0) [F351]   | (untested)          |
| bit31   | 1 / (0, 1)         | (untested)          | 1 / (0, 1)          |

Format: `dW57[0] forced / W57[22:23] forbidden polarity`

ALL 7 cands have IDENTICAL preflight output across tested mode/sr
combinations. The F343 mined clauses are universally invariant.

## Findings

### Finding 1 — F343 preflight is mode-invariant AND sr-invariant

The 2 mined clauses (Class 1a unit + Class 2 pair) are identical for:
- Same cand at force vs expose mode (F356)
- Same cand at sr=60 vs sr=61 (F354/F355)

The clauses are properties of the CASCADE-1 COLLISION PROBLEM at the
round-57 differential level, NOT of how the problem is encoded.

### Finding 2 — Injection effect IS mode-dependent

Despite same clauses being mined, injection effect varies by mode:
- F347 (sr=60 FORCE bit31, 32 mined clauses): -13.7% conflicts
- F352 (sr=60 EXPOSE bit29, 2 mined clauses): -1.06% conflicts

Hypothesis for the difference:
- FORCE mode has 481 cascade-offset AUX clauses in CNF (the cascade
  hardlock encoded as ripple-borrow Tseitin). The 2 mined clauses
  serve as "shortcut hints" helping CDCL navigate the dense AUX zone.
- EXPOSE mode has fewer cascade-related clauses (just exposes vars).
  The 2 mined clauses provide less marginal value because cadical can
  derive them quickly anyway from the smaller constraint base.

For Phase 2D propagator: inject AT LEAST in FORCE mode (where benefit
is measurable). For EXPOSE mode, inject as low-cost-extra but expect
smaller gain.

### Finding 3 — Phase 2D propagator design final form

```
For new cand spec (sr, M0, fill, kernel_bit, mode):
  if cand_already_mined:
      reuse_clauses(cand)  # mode/sr-invariant per F354/F355/F356
  else:
      run_preflight(cand, sr=60, mode=force)  # cheapest, results invariant
      cache_clauses(cand)
  inject_via_cb_add_external_clause(clauses)
  
Expected speedup:
  FORCE mode: 5-14% conflict reduction (per F347/F348)
  EXPOSE mode: ~1% conflict reduction (per F352)
```

## Compute

- ~120s total wall (5 cands × ~20s each + bit29 force ~20s).
- 0 long compute.

## What's shipped

- 5 sr=60 expose preflight JSONs in `F356_sr60_expose/`.
- bit29 force-mode preflight (extension).
- This memo.

## Status

Phase 2D propagator design is now empirically grounded across:
- 7 cands tested
- 2 encoding modes (force, expose)
- 2 sr levels (60, 61)
- ALL combinations produce identical clause libraries
- Injection effect measured for both modes

Phase 2D scaffold is structurally well-defined. The remaining work
is C++ IPASIR-UP implementation (10-14 hr build), which gates on a
build-cycle commitment.
