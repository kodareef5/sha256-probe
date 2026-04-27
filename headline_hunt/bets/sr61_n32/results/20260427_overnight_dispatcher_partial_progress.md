# Overnight kissat dispatcher — partial progress + Phase D bug found
**2026-04-27 14:00 EDT — dispatcher running 10h+, 126/156 jobs**

Mid-run snapshot of the overnight kissat campaign (see
`headline_hunt/bets/sr61_n32/overnight_kissat/` for full setup).

## Status

- Dispatcher PID: 48954
- Elapsed: 10:00:58
- Results so far: 126
- ETA remaining: 30 jobs × ~30 min/job = ~5 hours wall (limited by
  parallelism)
- Original ETA target: 13:30 EDT; revised: ~18:30 EDT

## Per-phase breakdown

| Phase | budget | jobs | done | status |
|---|---|---:|---:|---|
| A | 100M conflicts | 48 | 48 | ✓ all UNKNOWN |
| B | 1B conflicts | 30 | 30 | ✓ all UNKNOWN |
| C | 100M conflicts | 42 | 42 | ✓ all UNKNOWN |
| **D** | **5B conflicts** | **6 attempted** | **6 FAILED (bug)** | ⚠ see below |
| (continuing) | mixed | 30 | in queue | running |

## ⚠ BUG FOUND: Phase D budget exceeds kissat int32 max

All 6 Phase D jobs (run IDs 79-84) FAILED IMMEDIATELY with:
```
kissat: error: invalid argument in '--conflicts=5000000000' (try '-h')
```

Root cause: `PHASE_D_BUDGET = 5_000_000_000` in build_queue.py exceeds
kissat's int32 conflict-limit max (~2,147,483,647 = 2.15B). kissat
rejects the argument and exits with status 1.

The dispatcher then logs `wall=0.00 status=UNKNOWN` (because parse_status
finds no "s SAT/UNSAT" line in the failed log), which is misleading —
the budget was never used.

## Fix shipped

`build_queue.py` line 39-40 updated:
- PHASE_D_BUDGET: 5_000_000_000 → **2_000_000_000**
- Added comment explaining the int32 issue
- 30-min wall cap will fire before 2B conflicts on these CNFs anyway,
  so behavior is equivalent to "very deep budget" but actually executes

For future:
- Phase D should be re-run with the new build_queue (when current
  dispatcher completes; or `kill 48954 && restart` if user wants the
  Phase D coverage now).
- The 6 logged Phase D entries are NOT real solver attempts — they
  should be marked stale or removed from runs.jsonl when re-doing.

## Substantive findings so far

**0 SAT, 0 UNSAT, 126 UNKNOWN.**

- Phase A (100M, 8 cands × 6 seeds = 48): no breakthroughs
- Phase B (1B, 6 cands × 5 seeds = 30): no breakthroughs
- Phase C (100M, broader cand set × seeds = 42): no breakthroughs
- Phase D (5B, 6 attempted): all FAILED to launch (above bug)

This is consistent with the F-series finding "TRUE sr=61 is structurally
infeasible for cascade-1 mechanism alone" (per F20, F29). The overnight
campaign was a stronger empirical test of the same conclusion.

Mean wall per non-D job: 1714s (28.5 min) — most jobs hit the 30-min
time cap, very few finish their conflict budget within wall time.

## Compute used (approximate)

- 120 valid jobs × ~30 min wall = 60 wall-hours of solver time
- 6 cores parallel = ~10 wall-hours of dispatcher time (matches
  elapsed)
- ~6 CPU-cores × 10 hours = 60 CPU-hours
- Of the bet's 10,000 CPU-hour budget, this is 0.6% — well within
  budget cap

## Implications

1. **No sr=61 SAT discovery at any tested budget so far.** Per-cand
   1B conflicts × 5 seeds × 6 cands shows no breakthrough.

2. **Phase D was supposed to be the deepest test (5B per seed × 2 top
   cands × 3 seeds = 6 jobs).** The bug means we don't yet have actual
   5B-conflict (or 2B) data points. Need to re-run Phase D after fix.

3. **Pattern is consistent with closed-mechanism story**: cascade-1
   alone cannot produce sr=61 SAT at the budgets tested. This
   complements F-series structural data (F20, F29, F30, etc.).

4. **The dispatcher infrastructure works** — Phases A/B/C all
   completed successfully. The bug was purely in budget configuration
   for Phase D.

## Concrete next-actions

1. **Wait for current dispatcher to complete** (~5 hours; ETA 18:30
   EDT) — then run log_results.py to import valid runs into
   runs.jsonl.

2. **Re-queue Phase D** with the fixed `PHASE_D_BUDGET = 2B`. This
   gives ~2.7x deeper than Phase B (1B) per seed. Total 6 new jobs
   (~3 hours wall on 6 cores).

3. **Update sr61_n32 BET.yaml** with this run's verdict and the
   bug discovery for accountability.

EVIDENCE-level: VERIFIED for the bug. PARTIAL for the "0 sr=61 SAT
at any budget" claim (need Phase D rerun for completeness).
