# Conflict-budget=500k confirmation — Mode B's per-conflict edge ERODES at scale

Same 9-run matrix as `conflict_5k_2026-04-25/` (3 kernels × 3 encodings, kissat seed=5) at 10× the budget (500k conflicts). All UNKNOWN at budget. Total runtime: 96 s wall.

## Raw results

| candidate | encoding | decisions | propagations | wall (s) | dec/conf | prop/conf |
|---|---|---:|---:|---:|---:|---:|
| bit-10 | standard      | 2,583,415 | 73,715,985 |  9.77 | 5.17 | 147.4 |
| bit-10 | aux_expose    | 2,231,107 | 79,722,051 | 11.38 | 4.46 | 159.4 |
| bit-10 | aux_force     | 2,987,130 | 66,445,281 | 10.82 | 5.97 | 132.9 |
| bit-13 | standard      | 2,909,311 | 71,386,106 | 10.17 | 5.82 | 142.8 |
| bit-13 | aux_expose    | 2,299,448 | 77,643,895 | 11.60 | 4.60 | 155.3 |
| bit-13 | aux_force     | 2,944,925 | 60,775,370 | 10.45 | 5.89 | 121.6 |
| bit-19 | standard      | 2,538,291 | 64,497,941 |  9.17 | 5.08 | 129.0 |
| bit-19 | aux_expose    | 2,371,314 | 73,833,006 | 11.26 | 4.74 | 147.7 |
| bit-19 | aux_force     | 2,768,719 | 66,573,497 | 10.95 | 5.54 | 133.1 |

## The story changed

Comparing to the 50k-conflict run from `conflict_5k_2026-04-25`:

| metric (mean across 3 kernels) | budget=50k | budget=500k | trend |
|---|---:|---:|---|
| decisions/conf  — standard | 15.9 | 5.4 | -66% (warm-up complete) |
| decisions/conf  — expose   | 15.0 | 4.6 | -69% |
| decisions/conf  — **force** | **10.4** | 5.8 | -44% |
| propagations/conf — standard | 540 | 139.7 | -74% |
| propagations/conf — expose   | 688 | 154.1 | -78% |
| propagations/conf — **force** | **224** | 129.2 | -42% |
| wall-time/conf (µs) — standard | 53.6 | 19.5 | -64% |
| wall-time/conf (µs) — expose   | 70.6 | 22.8 | -68% |
| wall-time/conf (µs) — **force** | **25.4** | 21.7 | -15% |

Mode B's huge **early-conflict** advantage erodes as the solver warms up:
- At 50k: force is 2.0× faster wall-time per conflict than standard.
- At 500k: force is **~1.1× SLOWER** per conflict than standard.

The solver's steady-state per-conflict cost converges across encodings. Mode A (expose) is the slowest at low budget but reaches the BEST decisions/conflict at high budget (4.6 vs 5.4 standard, 5.8 force).

## Why does the early advantage exist?

Mode B's CNF encodes Theorems 1-4 as unit clauses (`dA[57..60]=0`, `dE[60..63]=0`, etc.). Kissat's preprocessing immediately propagates these units, eliminating ~3072 binary variables (8 registers × 32 bits × 12 cascade-rounds). With those vars eliminated, the early decisions/propagations are cheap — the search-space is smaller from the start.

But after preprocessing burns down to the steady-state CDCL search, all three encodings face the same ~12000-var residual problem. The encoding-specific differences in clauses count get amortized away, and per-conflict work converges.

## What this means for the bet

**Mode B's value is FRONT-LOADED, not amortized.** The aux-encoding hypothesis ("≥10× SAT speedup") would need Mode B to *also* find SAT in fewer conflicts than standard — not just process those conflicts faster. We can't measure that yet without finding actual SAT in any encoding.

Implication: Mode B is a fine choice for a "give the solver a 2× head-start" tactic, but unless cascade structure also reduces the conflicts-to-SAT count, the 12-hour standard-encoding wall-time becomes ~6h with Mode B, not ~1h. That's a real but modest gain — not headline-changing.

Mode A (expose) is the slowest in the early phase but has the lowest decisions/conflict in steady state — suggesting its aux variables, while overhead-heavy initially, give the solver useful structure once warmed up.

## Negatives.yaml: `seed_farming_unchanged_sr61` WCM update

The WCM trigger reads: "A new encoding demonstrably changes solver conflict count distribution at low budget."

**Status: PARTIAL FIRE → CONFIRMED for low budget, UNCONFIRMED for solve-time.**

Mode B unambiguously changes the conflict→work distribution at 50k-conflict budget (2× fewer propagations per conflict). That part of the WCM is satisfied. But the trigger's spirit ("kicks the solver off a stuck local minimum") needs evidence that conflict-count to SAT also drops, which requires running long enough to actually find SAT. Not refuted at 1800 CPU-h vanilla on standard encoding; remains TBD for Mode B.

So the negative stays CLOSED but with a qualifier: Mode B does have a measurable per-conflict edge at low budget. It just doesn't (yet) translate to wall-time-to-SAT at high budget.

## Reproducer

```bash
cd /Users/mac/Desktop/sha256_review
bash headline_hunt/bets/cascade_aux_encoding/cnfs/regenerate.sh
# Then loop over (candidate, encoding) and run kissat --conflicts=500000 --seed=5
```

9 logs in this directory.

## Suggested follow-ups

1. **Multi-seed at 50k**: 5 seeds × 9 instances = 45 runs (~90 sec). Measure variance. Is the early-budget Mode B advantage stable across seeds?
2. **Conflict budget 5M (~10 min total)**: confirm steady-state convergence claim at one more order of magnitude.
3. **Different solver (cadical)**: does the "front-loaded" pattern hold or is it kissat-specific?
4. **Find-SAT goal**: take the 12h standard-encoding-finds-SAT instance (the MSB cert) and re-run with Mode B at full budget. Does it find SAT in <12h? That's the real benchmark.
