# F41: Sequential vs Parallel kissat — F39 verdict reaffirmed under both
**2026-04-27 13:42 EDT**

Tests F39's claim ("bit2 has no real advantage; F30's 26.51s was a
parallelism artifact") under SEQUENTIAL measurement. Closes the
F30→F37→F38→F39→F41 thread definitively.

## Setup

For each cand, run kissat 5×1M conflicts SEQUENTIALLY (1 process at a
time, no contention). Compare to parallel measurements from
F37/F38/F39 (5 simultaneous processes).

| cand | HW | sym | parallel median | sequential median | parallel/seq |
|---|---:|:---:|---:|---:|---:|
| bit2_ma896ee41  | 45 | EXACT | 35.61s (F39) | **27.08s** (F41) | 1.31× |
| bit10_m9e157d24 | 47 | no    | 34.28s (F38) | **28.04s** (F41) | 1.22× |

## Findings

### Finding 1: parallelism slows kissat ~1.25× uniformly

Both cands experience similar slowdown going parallel-to-sequential.
The 30% slowdown is **system load**, not cand structure.

This explains the F30 vs F37/F38 discrepancy entirely:
- F30 measured bit2 SEQUENTIALLY (no other kissats running) → 26.51s
- F37/F38 measured cands in PARALLEL → 35-36s
- F39 re-ran bit2 in PARALLEL → 35.6s ✓ matches F37/F38 plateau
- F41 (this) runs both SEQUENTIALLY → both ~27s

### Finding 2: sequential per-cand differential is ALSO within noise

Sequential medians: bit2=27.08s, bit10=28.04s. Differential 0.96s
(~3.5%). Within seed noise (per-seed variation ±2s).

So bit2 has **no measurable kissat advantage** over bit10 even under
the favorable sequential condition. F39's negative finding is
**doubly verified**.

### Finding 3: per-conflict equivalence is robust to measurement mode

The cascade_aux Mode A sr=60 cand selection at 1M conflicts gives
walls that are:
- Independent of cand (within HW=45..51 range tested) ← confirmed F37, F38, F39, F41
- Independent of encoder mode (A vs B) ← confirmed F40
- Dependent on parallelism (1 vs 5 processes) ← confirmed F41

Solver-axis cand differentiation does NOT exist at 1M conflicts.

## What this leaves unresolved

The hypothesis "bit2 structural advantage (HW=45 + exact symmetry)
shows at DEEP budgets (12h+ kissat)" remains UNTESTED. F-series at
1M conflicts cannot resolve it. Would need:
- 12-hour kissat × multiple seeds × bit2 cascade_aux Mode A
- Same on bit10 (or another HW=47 plateau cand)
- If bit2 finds SAT in <12h and bit10 doesn't → structural advantage
- If neither finds SAT → cand selection irrelevant at depth too

Compute cost: 4 cores × 12h × 2 cands = 96 CPU-h. Substantial.
Needs explicit user authorization.

## Per-conflict baseline solidified

Combining F30/F37/F38/F39/F40/F41:

**Sequential (1M conflicts, no contention)**:
  All distinguished cands tested:  ~26-29s

**Parallel-5 (1M conflicts, 5 simultaneous)**:
  All distinguished cands tested:  ~34-36s

Both modes show essentially flat behavior across cand selection. At
1M conflicts, the cand IS NOT the relevant variable for kissat speed.

## Discipline

- 10 kissat runs logged via append_run.py (5 bit2 + 5 bit10, all
  sequential)
- CNF audit: both CONFIRMED sr=60 cascade_aux_expose
- Reproducible: seeds 1, 2, 3, 5, 7
- Runtime: ~5 minutes total (sequential is slow but clean)

EVIDENCE-level: VERIFIED. F39's verdict is now doubly verified
(parallel + sequential). Per-conflict equivalence is the new
baseline finding.

## Concrete next moves

1. **Document `parallelism_artifact` in CLAUDE.md or methodology**:
   future kissat measurements MUST report whether sequential or
   parallel, and N parallel processes if applicable. Critical for
   reproducibility.
2. **Update F30 retrospectively**: add a footnote "F30 was measured
   sequentially; comparable F37/F38 measurements were parallel-5;
   see F39/F41 for reconciled per-conflict baseline."
3. **For deep-budget testing**: if attempted, run sequential
   (clean conditions) for max wall efficiency. Multi-cand parallel
   is fine for screening but loses ~30% efficiency.
4. **For the paper Section 4/5**: claim "per-conflict cascade_aux
   Mode A walls are cand-invariant at 1M conflicts" with strong
   evidence (F37+F38+F39+F40+F41 = 50 logged kissat runs across 6
   cands AND 2 measurement modes).
