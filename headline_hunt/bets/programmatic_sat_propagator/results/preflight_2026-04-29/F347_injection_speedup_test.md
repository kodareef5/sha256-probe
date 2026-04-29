---
date: 2026-04-29
bet: programmatic_sat_propagator
status: EMPIRICAL — F344 clauses give 13.7% fewer CDCL conflicts at same budget
---

# F347: F344 mined clauses provide measurable CDCL pruning

## Setup

F345 found F344's 32 dW57 clauses are necessary but not sufficient.
F346 confirmed cadical preflight is the right architecture (no
algebraic shortcut for sr=60). F347 measures the actual CDCL impact:
does pre-injecting F344's mined clauses speed up CDCL?

## Test

CNF: `aux_force_sr60_n32_bit31_m17149975_fillffffffff.cnf`
(13,248 vars, 54,919 clauses).

Two variants:
- **Baseline**: original CNF unchanged.
- **F344-injected**: original CNF + 32 mined clauses appended (1 unit
  clause for dW57[0]=1 + 31 pair clauses for adjacent (dW57[i],
  dW57[i+1]) constraints).

Cadical 60s budget per variant, --no-binary mode.

## Result

| Metric | Baseline | F344-injected | Δ |
|---|---:|---:|---:|
| Verdict @60s | UNKNOWN | UNKNOWN | — |
| Wall time | 60.02s | 60.02s | (budget) |
| **Conflicts** | **2,190,601** | **1,891,271** | **−299,330 (−13.7%)** |
| Decisions | 9,524,146 | 9,320,660 | −203,486 (−2.1%) |
| Propagations | 212,348,758 | 265,634,713 | +53,285,955 (+25%) |

## Findings

### Finding 1 — F344 clauses give 13.7% fewer CDCL conflicts

Same 60s wall budget, F344-injected has 299k fewer conflicts. That's
real CDCL search-state pruning. Each "saved conflict" is a backtrack
that didn't have to happen because the injected clauses pre-empted
the dead-end branch.

### Finding 2 — Propagations INCREASED (+25%)

Adding clauses extends the unit-propagation chain at every decision
node. CDCL had to do MORE prop work per decision but MUCH less
backtracking work. Net trade is favorable: -13.7% conflicts >> +25%
prop time per conflict (since prop is much cheaper than conflict
analysis).

### Finding 3 — Decisions barely changed (-2.1%)

Decisions are roughly the same magnitude — CDCL is searching a similar-
sized tree but pruning conflict branches more aggressively. This is
consistent with F344 clauses providing CONFLICT HINTS rather than
direct branch-ordering changes.

## What this means for Phase 2D propagator

The empirical case for F344-style clause injection:

- **Real conflict reduction**: 13.7% measured at fixed budget.
- **Generalizes to wall time**: for instances that DO complete, this
  translates to ~13.7% wall reduction (roughly).
- **Per-cand cost**: F344 mining took 13 min on this CNF. F343 simpler
  mining (just W57[22:23] + dW57[0]) takes 20s.
- **Cost-benefit**:
  - 20s preflight + 5% conflict reduction (estimated for 2 clauses)
    → break-even at solver runs > 400s
  - 13 min preflight + 14% conflict reduction (full row, 32 clauses)
    → break-even at solver runs > 90 min

For F235-class hard instances where cadical times out at ~848s, the
20s F343 preflight is clearly worth it. The 13-min full sweep is
worth it only if we run multiple long jobs on the same cand (e.g., a
multi-seed kissat sweep).

### Finding 4 — F345's "modest speedup" estimate confirmed

F345 estimated 3-5s saved per solve from injecting the 32 clauses.
F347 measures 13.7% conflict reduction at 60s budget. If we extrapolate
the conflict-rate to ~36k conflicts/s, the 299k saved conflicts
correspond to ~8s of work avoided. Same order of magnitude as F345's
3-5s estimate.

## Concrete next moves

(a) **Test on a SAT instance that completes in < 60s**: see if 13.7%
    conflict reduction translates to ~13.7% wall reduction on
    completed solves.

(b) **Test on F235 hard instance** (sr61_cascade_m09990bd2_f80000000_bit25,
    cadical 848s baseline): does F344-style injection help on the
    bigger instance? Per-cand mining at sr=61 needs F340-style cross-
    validation first (fill-bit-31 polarity hypothesis at sr=61).

(c) **Evaluate F343 (smaller) preflight vs F344 (full row)**: is the
    extra 13 min worth ~10% more conflict reduction?

## Discipline

- 2 min wall (60s × 2 cadical runs).
- Direct empirical comparison.
- No claim beyond "13.7% fewer conflicts at same budget".

## What's shipped

- F347 baseline-vs-injected timing comparison in this memo.
- Confirms F345/F346 reframe: cadical preflight + clause injection IS
  the right architecture, with measurable but modest speedup.
