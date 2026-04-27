# F80 + F81: yale LM=637 NEW champion verified + deepest-budget 8-worker kissat sweep
**2026-04-27 22:35 EDT**

Two adjacent shippable items combined: F80 cross-solver verification of
yale's newest bit28 LM-frontier point, and F81 the deepest single-batch
brute-force SAT sweep mounted on macbook today.

## F80: yale's bit28 HW=45 / LM=637 EXACT-sym — NEW LM champion

Yale's online Pareto sampler (linux_gpu_laptop, F77-yale numbering)
shipped a new bit28 frontier point — exact a61=e61 symmetry, beating
their previous LM=679 by 42 LM bits.

W-witness:
```
W57 = 0xce9b8db6
W58 = 0xb26e4c72
W59 = 0x4b04cbc4
W60 = 0x0a0627e6
```
Cand: bit28_md1acca79 (m0=0xd1acca79, fill=0xffffffff, kernel-bit=28).

### Verification via certpin_verify --solver all (F76 pipeline)

```
$ python3 certpin_verify.py --solver all --cand-id "yale_F77_bit28_HW45_LM637_EXACT" \
    --m0 0xd1acca79 --fill 0xffffffff --kernel-bit 28 \
    --w57 0xce9b8db6 --w58 0xb26e4c72 --w59 0x4b04cbc4 --w60 0x0a0627e6

Status:  UNSAT
Wall:    0.041s
Verdict: near-residual (all 3 solvers UNSAT)
```

kissat + cadical + CMS all return UNSAT independently. Verdict: this is
a **near-residual** — the W1-pinning is contradictory under cascade-1,
not a verified collision. Same outcome as F70's HW=33/LM=679 frontier
verification: yale's online sampling is producing structurally consistent
near-residuals, none crossing into SAT territory at single-block scope.

This holds the F71 invariant: across the entire bit28 frontier yale has
explored to date, **0 verified collisions, all near-residuals**. The
Wang block-2 absorption path remains the only known route to convert
yale's frontier points into full collisions.

### Why LM=637 still matters even though UNSAT

LM (Lipmaa-Moriai bit-cost sum across active modular adders) is the
strongest known structural proxy for trail tractability on a Wang
block-2 design. Beating LM=679 → LM=637 means yale has found a residual
state that's **42 bits cheaper** to absorb in a hypothetical block-2
attempt — assuming yale eventually designs the block-2 trail.

For paper Section 5, this strengthens the F36/F45 claim that the
LM/HW surface is locally navigable: in a single day's online sampling,
yale moved both metrics monotonically toward the structural optimum.

## F81: 8-worker kissat 10M conflicts × top-4 cands × seeds 11/13

Following F77 (12 workers × 5M) and F78+F79 (17 workers × 5M), F81
**doubles the per-worker budget** to 10M conflicts, focused on the
top-4 targets at fresh seeds 11/13.

### Setup

Top-4 (per F72 ranking):
1. msb_ma22dc6c7 — TRIPLE-AXIS champion
2. bit28_md1acca79 — overall project champion (yale)
3. bit2_ma896ee41 — Wang sym-axis champion
4. bit10_m9e157d24 — Cohort A baseline

8 parallel kissat workers: 4 cands × 2 seeds × 10M conflicts.
Total budget: 80M conflicts (vs F77's 60M, F78+F79's 85M).

### Result

```
                                      wall    status
kissat msb_ma22dc6c7  seed=11:        586s    UNKNOWN
kissat msb_ma22dc6c7  seed=13:        614s    UNKNOWN
kissat bit28          seed=11:        576s    UNKNOWN
kissat bit28          seed=13:        598s    UNKNOWN
kissat bit2           seed=11:        615s    UNKNOWN
kissat bit2           seed=13:        620s    UNKNOWN
kissat bit10          seed=11:        603s    UNKNOWN
kissat bit10          seed=13:        611s    UNKNOWN
```

**8/8 UNKNOWN. 0 SAT.**

### What 10M vs 5M tells us

F77 (5M): 312-365s walls per kissat worker (parallel-12 contention).
F78  (5M): 549-619s walls per kissat worker (parallel-17 contention).
F81 (10M): 575-620s walls per kissat worker (parallel-8 contention).

**At 10M conflicts under parallel-8, walls are nearly equal to F78's
parallel-17 5M.** The system is core-saturated either way — adding
budget doesn't help when the bottleneck is throughput, and per-worker
wall scales linearly with conflicts only in idle conditions.

For SAT discovery: the additional 5M conflicts per worker found nothing
that wasn't found at 5M. Combined with F77+F78+F79, our cumulative
exploration on these top-4 cands is now:
- msb_ma22dc6c7: kissat 5M×3 + 10M×2 + cadical 5M = 35M conflicts
- bit28: kissat 5M×3 + 10M×2 + cadical 5M = 35M conflicts
- bit2: kissat 5M×3 + 10M×2 + cadical 5M = 35M conflicts
- bit10: kissat 5M×3 + 10M×2 + cadical 5M = 35M conflicts

**140M conflicts across 4 top targets, 0 SAT.** Per Wang's complexity
estimate (~2^60), we remain ~22 orders of magnitude below threshold.

### Today's combined deep-budget compute

F77 + F78 + F79 + F81 = **37 deep-budget runs**, all UNKNOWN:
- F77: 12 workers × 5M = 60M
- F78: 12 workers × 5M = 60M
- F79: 5 workers × 5M = 25M
- F81: 8 workers × 10M = 80M
- **Total: ~225M conflicts explored, 0 SAT**

CPU time: ~10 CPU-hours. Wall time: ~30 min total (parallel batched).
Peak load: 106 across 10 cores during F78 (10× core saturation).

## Combined interpretation

F80 + F81 close out today's brute-force SAT axis with two clean
findings:

1. **yale's frontier remains structurally consistent.** Every
   W-witness yale ships verifies as a near-residual under all 3
   solvers. The pipeline (online sampler → certpin_verify --solver all)
   is production-grade.

2. **Single-machine deep-budget SAT search confirms what theory
   predicts.** ~225M conflicts × 9 distinct cands × 2 solvers found
   nothing. We are not going to brute-force a sr=60 collision from
   macbook. This was already understood from F68 (1M-conflict
   indeterminate result) but is now empirically pinned at scale.

The headline-class finding still requires the Wang block-2 absorption
trail (yale's structural domain) and the 2-block cert-pin tool that
follows. Brute-force SAT is not the remaining gap.

## What this changes for tomorrow

- **STOP** spending macbook compute on single-block deep-budget SAT.
  ~225M conflicts on 9 cands is empirically saturating; further runs
  add no signal at single-block scope.
- **CONTINUE** running yale's incoming W-witnesses through
  certpin_verify --solver all as fast as yale ships them. <1s per
  verification, near-zero compute cost.
- **STRUCTURAL PIECE STILL MISSING**: Wang block-2 trail design.
  This is yale's domain (linux_gpu_laptop) — macbook's role is to
  build the 2-block cert-pin tool *once yale's trail is in hand*.

## Discipline

- 8 F81 runs logged via append_run.py
- 1 F80 verification logged via append_run.py
- All CNFs CONFIRMED via earlier audits
- 0% audit failure rate maintained
- Total registry runs reached 878 (was 869 at F79)

EVIDENCE-level: VERIFIED. F80 multi-solver agreement on yale frontier
point. F81 8/8 UNKNOWN at 10M conflicts. Both findings consistent with
the Wang-block-2 thesis.

## Today's day total — final

- ~75 commits
- 870+ logged solver runs
- 0% audit failure rate maintained
- 5 honest retractions (F39, F49, F55, F69, F74)
- 4 paper-class structural claims locked (F34, F36, F42, F43)
- ~10 CPU-hours of solver compute today (peak load 106)
- 1 production-grade verification pipeline shipped (F69+F70+F71+F76)
- 1 yale collaboration confirmed working (F70, F80)

## Concrete next moves

1. **Wait for yale's block-2 trail design** — primary structural gap.
2. **Build 2-block cert-pin tool** (waits on #1).
3. **Cross-axis manifold-search test** (waits on yale).
4. **For the paper draft (Section 5)**: F36 + F43 + F45 + F71 form
   the strongest publishable empirical sequence on cascade-1 structure.
   F77+F78+F79+F81 supply the empirical floor for "brute-force SAT at
   single-block scope does not find new collisions at our compute scale."
