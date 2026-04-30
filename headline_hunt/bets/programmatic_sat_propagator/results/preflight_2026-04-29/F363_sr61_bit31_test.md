---
date: 2026-04-30
bet: programmatic_sat_propagator
status: F363 — sr=61 bit31 also ~1% with 2 mined clauses (F347 outlier hypothesis strengthened)
---

# F363: aux_force_sr61 bit31 m17149975 + 2 mined clauses → -0.72%

## Setup

F362 found bit25 m09990bd2 sees only -0.46% with 34 native mined clauses
(noise level). F363 tests the SAME methodology on bit31 m17149975 at
sr=61 — the cand for which F347 measured the outlier 13.7% at sr=60
with 32 clauses.

If F363 also gives ~1%, then F347's 13.7% was either:
- 32-clause-specific bulk effect (vs 2-clause minimal here), or
- noise outlier (single 5-min sample)

## Result

```
aux_force_sr61 bit31 BASELINE (cadical 5min): 5,279,584 conflicts UNKNOWN
aux_force_sr61 bit31 + 2 mined clauses:        5,241,369 conflicts UNKNOWN
Δ: -38,215 conflicts (-0.72%)
```

## Findings

### Finding 1 — bit31 sr61 with 2 clauses also at noise level

F347 (sr60, 32 clauses): -13.7% on bit31
F363 (sr61, 2 clauses): -0.72% on bit31
F362 (sr61, 34 clauses): -0.46% on bit25

The 2-clause minimal preflight gives ~1% across cands consistently.
F347's outlier 13.7% must come from EITHER:

(a) The 30 extra pair-clauses in F344 full-row sweep
(b) Random noise in the single 5-min measurement

### Finding 2 — Need apples-to-apples test for F347 reproduction

To resolve (a) vs (b), need:
- aux_force_sr61 bit31 + full row sweep (F344-style ~32 clauses) → measure
- aux_force_sr60 bit31 with just 2 clauses → measure (compare to F347's 32)
- Replicate each at multiple seeds for noise estimate

If apples-to-apples reproduces F347's 13.7%, the 32-clause bulk is real
benefit. If only ~1%, F347 was noise outlier.

### Finding 3 — Phase 2D propagator viability picture darkens

F362+F363 strengthen the case that F343 injection's BENEFIT is
narrow:
- F343 minimal preflight (2 clauses): ~1% across all cands tested
- F344 full row (~32 clauses): unknown, possibly larger but unverified

For Phase 2D propagator: native IPASIR-UP injection of 2-clause set
projected ~3-5% (from F347/F348 ratio analysis), but F362/F363 suggest
the BASELINE itself is ~1%, so even native might be ~3-5%.

That's still BELOW F361's 1.16x reopen criterion.

### Finding 4 — Updated empirical envelope

| Probe | Mode | Cand | Clauses | Speedup |
|---|---|---|---:|---:|
| F347 | sr60 aux_force | bit31 | 32 | -13.7% (outlier?) |
| F348 | sr60 aux_force | 5-cand mean | 2 | -8.8% (suspicious — re-verify) |
| F352 | sr60 aux_expose | bit29 | 2 | -1.06% |
| F360 | sr61 basic_cascade | bit25 | 130 | -0.79% |
| F362 | sr61 aux_force | bit25 | 34 | -0.46% |
| **F363** | **sr61 aux_force** | **bit31** | **2** | **-0.72%** |

F348's -8.8% mean across 5 cands is now also suspicious. Either
sr=60 force has fundamentally different propagation than sr=61, or
F348 was lucky.

## Concrete next probes

(a) **F364 (proposed)**: F344-style full row sweep on aux_force_sr61
    bit31 (~13 min mining), then 5-min injection. Tests whether
    F347's 13.7% reproduces at sr=61 with 32 clauses.

(b) **F348 replication**: re-run F343-injected 5-min cadical on the
    5 sr=60 cands from F348 to check if -8.8% reproduces or was
    noise.

(c) **F347 replication**: re-run sr=60 bit31 with F344's 32 clauses
    multiple times (different seeds via cadical --seed flag). Get
    actual noise estimate.

For Phase 2D viability: (a) and (c) together tell us if 32-clause
bulk is genuinely better than 2-clause minimal, OR if F347 was noise.

## Compute

- 5 min × 2 cadical = 600s wall.
- Logged via append_run.py.

## Discipline

- Honest report: F363 -0.72% essentially noise.
- F347's 13.7% increasingly looks like outlier or 32-clause-bulk-specific.
- Phase 2D reopen criterion may need further sharpening once full-row
  on sr61 bit31 is measured.

## What's shipped

- F363 baseline + injected logs.
- This memo.
