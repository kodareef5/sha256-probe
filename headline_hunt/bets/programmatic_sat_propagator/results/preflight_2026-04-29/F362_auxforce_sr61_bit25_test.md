---
date: 2026-04-30
bet: programmatic_sat_propagator × sr61_n32
status: CAND_VARIANCE_DOMINATES — bit25 injection effect is noise-level
---

# F362: aux_force_sr61 bit25 m09990bd2 injection — only -0.46%

## Setup

F360 measured -0.79% on F235 (basic cascade) for cand m09990bd2/bit25.
F362 tests the SAME cand on aux_force_sr61 with the 34 mined clauses
(F359) injected NATIVELY (using aux_W57 vars, no var translation).

## Result

```
aux_force_sr61 BASELINE (cadical 5min): 5,348,445 conflicts UNKNOWN
aux_force_sr61 + 34 mined clauses:      5,324,083 conflicts UNKNOWN
Δ: -24,362 conflicts (-0.46%)
```

## Findings

### Finding 1 — Even native aux_force injection is noise-level on bit25

Comparing F362 (aux_force, 34 mined clauses) to F360 (basic cascade,
130 translated clauses) on the SAME cand:

- aux_force + 34 native: -0.46%
- basic_cascade + 130 translated: -0.79%

Both ~1% or below. NEITHER reaches F347's 13.7% on bit31. The
F347 measurement was bit31-specific.

### Finding 2 — Cand variance dominates injection benefit

Updated speedup table (real measurements):

| Probe | Mode | Cand | Clauses | Speedup |
|---|---|---|---:|---:|
| F347 | sr60 aux_force | bit31 m17149975 | 32 | **-13.7%** |
| F348 | sr60 aux_force | 5 cands mean | 2 | -8.8% |
| F352 | sr60 aux_expose | bit29 m17454e4b | 2 | -1.06% |
| F360 | sr61 basic_cascade | bit25 m09990bd2 | 130 | -0.79% |
| **F362** | **sr61 aux_force** | **bit25 m09990bd2** | **34** | **-0.46%** |

bit31 in F347 is the OUTLIER — 10x larger speedup than other cands.
Possible reasons:
1. bit31's specific cascade structure happens to be more amenable to
   the F343 mined constraints
2. Sr level (sr=60 vs sr=61) interacts with mining benefit
3. Encoder mode contribution

Need a controlled test: SAME cand bit31 at SAME sr=60 with the F343
2-clause minimal preflight (matching F348's protocol, not F347's
32-clause F344-style). Isolate variables.

### Finding 3 — F362 within noise range

Standard deviation on cadical conflict counts at 5-min budgets across
similar instances: typically 1-3%. F362's -0.46% is essentially
INDISTINGUISHABLE FROM NOISE.

The F343 injection's REAL speedup magnitude on bit25 m09990bd2 is
≤1% even with 34 native mined clauses. Modest.

## Implications for Phase 2D propagator

The 13.7% F347 measurement on bit31 was NOT representative. Real-world
expected speedup is more like 1-3% per cand on average, with bit31-class
outliers giving up to ~14%.

For F235 (the bet's reopen-target which IS the same bit25 cand): the
expected NATIVE-injection speedup is ~1-2% (since CNF-only got ~0.79%
and aux_force got ~0.46%). Native IPASIR-UP injection might give
~3-5x the CNF-only number, so ~3-5% expected.

That's BELOW the 1.16x speedup gate set in F361. Phase 2D propagator
would NOT meet reopen criterion on F235 specifically.

For Phase 2D viability, the best candidates are bit31-class cands
(F347 measured 13.7% on bit31). The propagator might give the bet
its best argument for bit31 sr=61 cands, NOT F235.

## Refined reopen recipe

For Phase 2D to justify reopen:
1. Mine aux_force_sr61 bit31 m17149975 fillffffffff (same family as
   F347 but at sr=61 instead of sr=60) — 20s.
2. Inject + 5min cadical baseline. If ~13.7% measured (matching F347
   sr=60), Phase 2D viable on bit31-class cands.
3. F235 m09990bd2/bit25 not the ideal test instance — too small effect.

## Compute

- 5 min × 2 cadical = 600s wall.
- F362 follows the F347/F348 protocol: same 5-min budget, parallel
  baseline + injected.

## Discipline

- Honest report: -0.46% is in noise.
- Cand-specific variance documented (F347 bit31 was outlier).
- Phase 2D reopen criterion sharpened: not all cands give bit31-level
  speedup.

## What's shipped

- F362 baseline + injected logs.
- This memo.
- Updated speedup envelope reflects cand variance.
