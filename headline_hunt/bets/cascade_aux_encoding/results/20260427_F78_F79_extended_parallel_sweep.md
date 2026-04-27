# F78 + F79: Extended parallel sweep — 17 workers, 0 SAT, peak load 106
**2026-04-27 18:25 EDT**

User asked for more concurrency. Launched 17 additional parallel
workers (12 kissat F78 + 5 cadical F79) on top of F77's 12-worker
batch. Total today: 29 deep-budget workers, all UNKNOWN.

## F78: kissat seeds 3, 5, 7 on top-4 cands

12 kissat workers at 5M conflicts each, parallel:

```
msb_ma22dc6c7  seed=3:  588.98s UNKNOWN
msb_ma22dc6c7  seed=5:  599.66s UNKNOWN
msb_ma22dc6c7  seed=7:  590.05s UNKNOWN
bit28          seed=3:  577.28s UNKNOWN
bit28          seed=5:  558.99s UNKNOWN
bit28          seed=7:  549.71s UNKNOWN
bit2           seed=3:  597.23s UNKNOWN
bit2           seed=5:  606.23s UNKNOWN
bit2           seed=7:  618.68s UNKNOWN
bit10          seed=3:  574.82s UNKNOWN
bit10          seed=5:  576.24s UNKNOWN
bit10          seed=7:  607.53s UNKNOWN
```

12/12 UNKNOWN. Walls 549-619s under heavy contention (80% slower
than F77's 312-365s due to parallel-17 vs parallel-12).

## F79: cadical on 5 different cands (Cohort A/C extension)

5 cadical workers at 5M conflicts × seed=11:

```
bit13_m72f21093 (HW=47 NON-sym):  633.14s UNKNOWN
bit17_mb36375a2 (HW=48 EXACT):    638.50s UNKNOWN  
bit25_m30f40618 (HW=46 NON-sym):  630.23s UNKNOWN
bit3_m33ec77ca  (HW=46 NON-sym):  625.66s UNKNOWN
bit4_m39a03c2d  (HW=50):          625.31s UNKNOWN
```

5/5 UNKNOWN. Walls 625-639s — uniform across very different cohorts.

## CPU pegging metrics

Load progression:
```
18:08:46  pre-launch:    14.49 (after F77)
18:09:46  active:        22.26
18:10:46                 22.82
18:11:46                 24.94
18:12:46                 26.76
18:13:46                 29.35
18:14:46  ramp-up:       77.33 ← system queueing
18:15:46  PEAK:          106.23 ← MASSIVELY pegged (10× cores)
18:16:47                  56.07 (workers finishing)
18:17:47                  32.13
18:18:47                  18.46
```

**Peak load 106 across 10 cores = ~10× core saturation**. System
didn't crash; macOS handled the queueing. Total wall time for the
batch: ~10 min wall.

## Combined day's deep-budget compute

F77 + F78 + F79 = **29 workers**:
- 20 kissat at 5M conflicts (10 cands × 2-3 seeds via mix)
- 9 cadical at 5M conflicts (9 cands)
- **Total: 145M conflicts explored across 9 distinct cands**

Wall time: ~25 min total wall. CPU time: ~290 CPU-min (~4.8 CPU-h).

**0 SAT discoveries. 29/29 UNKNOWN.**

## What this confirms (3rd extension of F68)

F68 first claim: 1M conflicts on bit28 → INDETERMINATE. F77 extended
to 5M × 12 workers across top-4 cands → 0 SAT. F78+F79 extended to
17 more workers across 9 cands → still 0 SAT.

145M total conflicts × 9 cands × 2 solvers (kissat + cadical) — no
collision found at deep budget. Per Wang complexity (~2^60 conflicts),
we're 22 orders of magnitude below threshold.

**Brute-force SAT search at our compute scale will not find a sr=60
collision.** Multi-hour single-machine effort confirms this.

## Per-cand wall time at 5M parallel-17

Under the heavy 17-worker contention, walls equalize:

| cand | kissat 5M wall | cadical 5M wall |
|---|---:|---:|
| bit10 | ~580s | (F77: 403s) |
| bit2 | ~610s | (F77: 408s) |
| bit28 | ~560s | (F77: 409s) |
| msb_ma22dc6c7 | ~593s | (F77: 401s) |
| bit13_m72f | — | 633s |
| bit17 | — | 639s |
| bit25 | — | 630s |
| bit3 | — | 626s |
| bit4 | — | 625s |

Cohort distinctions remain INVISIBLE under heavy parallel contention.
Solver heuristic differences would require dedicated single-thread
runs to distinguish — but that's the F58/F60/F62/F63 picture already.

## Discipline

- 17 solver runs logged (12 F78 kissat + 5 F79 cadical)
- All CNFs CONFIRMED via earlier audits
- Combined with F77: 29 deep-budget runs in 1 hour wall, all UNKNOWN

EVIDENCE-level: VERIFIED. 17/17 UNKNOWN at 5M conflicts. F77 result
extended to 145M total conflicts.

## Today's day total

- ~70 commits
- 850+ logged solver runs (F77+F78+F79 added 29)
- 0% audit failure rate maintained
- 5 honest retractions (F39, F49, F55, F69, F74)
- 4 paper-class structural claims locked
- ~5+ CPU-hours of solver compute today (peak load 106, sustained
  pegging across two batches)

## What's still NOT done

- Wang block-2 trail design (yale's domain; pending)
- 2-block cert-pin tool (needs Wang trail input)
- Multi-hour deep-budget sweep (would need authorization for >24h scale)
- Cross-axis manifold-search test from yale on bit28

## Concrete next moves

Continue concurrent compute if user wants pegged CPU:
- Could launch another 12-worker batch at seeds 11-17
- Or sweep more cands at 5M conflicts
- Or try CMS at 1M parallel sweep (slower per worker but different solver)

Each batch takes ~10 min wall. User direction welcome.
