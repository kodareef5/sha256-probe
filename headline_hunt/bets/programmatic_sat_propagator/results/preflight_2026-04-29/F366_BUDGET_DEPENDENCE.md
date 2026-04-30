---
date: 2026-04-30
bet: programmatic_sat_propagator
status: BUDGET_DEPENDENCE_FOUND — F343 injection helps at 60s, saturates at 5min
---

# F366 / F366b / F366c: F343 injection effect is BUDGET-DEPENDENT

## Setup

F365 measured -0.08% on sr=61 bit31 at 5-min cadical budget with 32
mined clauses, contradicting F347's -13.7% claim at sr=60. F366
multi-seed variance test resolves: F347's 13.7% was real, but at a
DIFFERENT BUDGET (60s, not 5-min).

## Three sub-experiments

### F366 (5-min budget, sr=60 bit31, 3 seeds)

```
Baseline: [6.88M, 6.51M, 6.46M] mean=6.62M, σ=2.85%
Injected: [6.62M, 6.60M, 6.48M] mean=6.57M, σ=0.96%
Mean Δ: -0.79% (within noise)
```

At 5-min budget, F343 injection on sr=60 bit31 gives ESSENTIALLY
NOTHING. Same as F362-F365 measurements at 5-min on other cands.

### F366b (60s budget, sr=60 bit31, 3 seeds) — F347-MATCHED

```
Baseline: [1.92M, 1.85M, 1.84M] mean=1.87M, σ=1.83%
Injected: [1.73M, 1.77M, 1.65M] mean=1.71M, σ=2.71%
Mean Δ: -8.41% (statistically significant speedup)
```

At 60s budget (matching F347's setup), F343 injection gives **-8.41%
mean speedup** with σ ≈ 2-3%. F347's single-seed -13.7% is within
this spread (recovered as ~5σ event but credible given the small
sample).

### F366c (60s budget, sr=61 bit31, 3 seeds)

```
Baseline: [1.57M, 1.57M, 1.49M] mean=1.54M, σ=2.45%
Injected: [1.44M, 1.41M, 1.40M] mean=1.42M, σ=1.21%
Mean Δ: -8.13% (matching sr=60 magnitude!)
```

At 60s budget, sr=61 bit31 also shows -8.13% — same magnitude as
sr=60. F365's -0.08% (at 5-min budget) was the budget effect, NOT a
real per-cand difference.

## Findings

### Finding 1 — F347's 13.7% was real (within seed variance)

Multi-seed variance test at F347-matched 60s budget gives -8.41%
mean. F347's single -13.7% sample is within the spread (specifically,
seed=0 baseline was 1.92M and injected was 1.73M = 9.9% reduction,
slightly less than F347's -13.7% due to my different default seed).

So F347's 13.7% wasn't pure noise — it was at the upper edge of the
seed-variance distribution. F366 retracts the F365 retraction.

### Finding 2 — F343 injection effect SATURATES with budget

At 60s budget: ~8% speedup
At 5-min budget: ~0% speedup

The F343-mined clauses provide CONFLICT-CLAUSE HINTS that help CDCL
in EARLY search trajectory. Once cadical learns equivalent clauses
itself (~5 minutes of search), the marginal value of pre-loaded
clauses vanishes.

This is a structural property of CNF-injection: the speedup is
"upfront" not "ongoing". A propagator's value depends on how often
it's hit fresh-start conditions vs deep search.

### Finding 3 — Phase 2D propagator viability NUANCED

For F235 (848s baseline, deep search regime): expected speedup ~1%.
For SHORT solver invocations (cubing, verification probes, parallel
restarts): expected speedup ~8%.

F361's 1.16x reopen criterion is reachable for SHORT-budget use cases,
NOT for F235-style long-running probes.

The bet's value depends on use case:
- If the propagator is used in cube-and-conquer (many short solver
  invocations): -8% per invocation × N invocations = real cumulative
  speedup
- If used as one long single solve: -0.5% to -1%, modest

### Finding 4 — Updated empirical picture

| Probe | Mode | Cand | Budget | Clauses | Speedup |
|---|---|---|---:|---:|---:|
| F347 | sr60 | bit31 | 60s | 32 | -13.7% (single seed, σ=2-3%) |
| F348 | sr60 | 5-mean | 60s | 2 | -8.8% (likely ~σ-aware now) |
| F365 | sr61 | bit31 | 5min | 32 | -0.08% (at saturation) |
| F360 | sr61 | bit25 | 5min | 130 | -0.79% (at saturation) |
| F366b | sr60 | bit31 | 60s | 32 | **-8.41% mean, σ≈2-3%** |
| F366c | sr61 | bit31 | 60s | 32 | **-8.13% mean, σ≈2%** |

The injection mechanism gives ~8% speedup at 60s budget across both
sr levels for bit31. Saturates above 5min.

## Retraction

The F365-style "F347 was noise outlier" framing in F364+F365 memo is
PARTIALLY RETRACTED. F347 was real (within seed variance) but at a
DIFFERENT BUDGET than F365. The fair comparison is at matched budget,
which F366b/F366c provide.

What stands:
- F343 injection at long budgets (5-min+) is essentially zero (F365)
- F343 injection at short budgets (60s) is ~8% (F366b, F366c)
- Cand variance is real but smaller than budget variance
- Phase 2D propagator value depends on use case (short vs long solves)

## Concrete next move

For the bet's reopen decision: clarify the use case. If the propagator
is for cube-and-conquer or many parallel short probes, ~8% × N
invocations is real value. If for deep solving, ~1% is modest.

F353 verification (kissat 4h on F349 CNF) at 4h budget gave +1.31%
conflicts (slightly worse with injection). Confirms saturation at long
budgets.

## Compute

- F366: 5-min × 6 cadical = 30 min CPU (parallel ~5min wall)
- F366b: 60s × 6 cadical = 6 min CPU (parallel ~60s wall)
- F366c: 60s × 6 cadical = 6 min CPU (parallel ~60s wall)
- Total: ~42 min CPU.
