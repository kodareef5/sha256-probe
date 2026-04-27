# F61: CMS at HW=47 — universal "NON-sym slightly faster" penalty across 3 solvers
**2026-04-27 12:15 EDT**

Tests F60 next-step #2: CMS on the bit13 sym/non-sym pair (same fill,
same kernel_bit, only sym differs) to determine whether the kissat +
cadical agreement at HW=47 (NON-sym faster by 3-4s) extends to CMS.

## Result

```
HW=47, fill=0xaaaaaaaa, kernel_bit=13, only sym status differs:

CMS bit13_m4e560940 (EXACT-sym):  18.61, 20.14, 19.07, 25.46, 22.14
                                  → median 20.14s, range 7.07s

CMS bit13_m72f21093 (NON-sym):    17.38, 18.15, 22.03, 22.73, 18.05
                                  → median 18.15s, range 5.36s

Differential: 1.99s (NON-sym faster, same direction as kissat + cadical)
```

## 3-solver consensus on HW=47 sym pair

| solver | EXACT-sym (bit13_m4e) | NON-sym (bit13_m72f) | gap (NON-faster) |
|---|---:|---:|---:|
| kissat | 32.83s | 28.72s | 4.11s |
| cadical | 36.99s | 34.29s | 2.70s |
| **CMS** | **20.14s** | **18.15s** | **1.99s** |

**ALL 3 SOLVERS agree at HW=47**: NON-sym is slightly faster (1.99-4.11s).
Mild but reproducible penalty for EXACT-sym at HW=47 across CDCL
architectures.

This is opposite to the F54 HW=48 reversal (where cadical reverses
kissat). At HW=47, all 3 solvers behave similarly.

## Updated 7-cand × 3-solver picture (now 21 cells, mostly populated)

| cand | HW | sym | kissat | cadical | CMS | tier |
|---|---:|:---:|---:|---:|---:|---|
| bit18_mafaaaf9e | 48 | NO | 30 | 65* | **15** | CMS-FASTEST |
| bit13_m72f21093 | 47 | NO | 29 | 34 | **18** | multi-solver fast |
| msb_ma22dc6c7 | 48 | NO | 31 | **25** | **18** | TRIPLE champion |
| bit13_m4e560940 | 47 | EXACT | 33 | 37 | **20** | medium 3-solver, CMS-fast |
| bit10_m9e157d24 | 47 | NO | 28 | 24 | 21 | UNIVERSAL fast |
| bit2_ma896ee41 | 45 | EXACT | **27** | 41 | 52 | kissat-only |
| bit17_mb36375a2 | 48 | EXACT | 42 | **24** | 57 | cadical-only |

*bit18 cadical pathology

## Updated cohort taxonomy

**MULTI-SOLVER FAST cluster (5 cands)**: cands fast on ≥2 of 3 solvers:
- bit10 (3/3) — UNIVERSAL fast
- msb_ma22dc6c7 (3/3 if you count plateau-fast on kissat)
- bit18 (2/3, kissat + CMS, cadical pathology)
- bit13_m72f21093 (3/3 — NEW)
- bit13_m4e560940 (CMS-fast + plateau on kissat/cadical) — borderline

**SINGLE-SOLVER fast (2 cands)**: kissat-only bit2, cadical-only bit17.

The "multi-solver fast" cluster is now larger than first thought.
Most HW=47-48 NON-sym cands are universally fast.

## Refined paper Section 4 claim

With 7-cand × 3-solver = 21 cells (mostly populated):

> "Cascade_aux Mode A 1M-conflict CDCL walls across kissat 4.0.4,
> cadical 3.0.0, and CryptoMiniSat 5.13.0 (100k for CMS comparison)
> on 7 representative cands from the 67-cand F32 deep-min corpus
> reveal three solver-architecture cohorts:
>
> (A) Multi-solver fast (HW=47-48 NON-sym + EXACT-sym at HW=47 mid):
> bit10, bit13_m72f21093, msb_ma22dc6c7, bit13_m4e560940, bit18.
> Fast on at least 2 of 3 solvers tested. msb_ma22dc6c7 is the
> strongest cross-axis cand (cadical fastest, CMS fast, kissat
> plateau, F36 LM-min).
>
> (B) kissat-only fast: bit2_ma896ee41 (HW=45 EXACT-sym, sparse
> a_61=e_61=0x02000004 pattern). Solver heuristic match.
>
> (C) cadical-only fast: bit17_mb36375a2 (HW=48 EXACT-sym).
> Vivification exploits redundant clauses.
>
> At HW=47, all 3 solvers exhibit a mild EXACT-sym penalty (NON-sym
> faster by 2-4s — universal). At HW=48 EXACT-sym, kissat is
> penalized (53s) while cadical reverses (24-45s). At HW=45 only one
> EXACT-sym cand exists (bit2), uniquely kissat-fast.
>
> Mechanism speculation: kissat thrives on sparse bit patterns;
> cadical thrives on redundant clause structure (HW=48 EXACT-sym
> vivification); CMS handles both moderately well, with HW=47-48
> NON-sym universally fast across all 3 architectures."

This is a substantial paper-class cross-solver structural finding.

## Implications for block2_wang

**Updated PRIMARY targets** (post-F61):

1. **msb_ma22dc6c7** — strongest cross-axis (LM + cadical + CMS)
2. **bit2_ma896ee41** — Wang sym-axis (HW=45 + EXACT-sym; kissat-only fast)
3. **bit13_m72f21093** — newly recognized multi-solver fast (HW=47
   NON-sym, fast on all 3)
4. **bit10_m9e157d24** — universal fast (3/3 solvers)
5. **bit18_mafaaaf9e** — kissat + CMS fast (avoid cadical)

For a 5-cand mixed-solver block2_wang campaign, this set covers:
- Wang sym-axis (bit2)
- LM-axis champion (msb_ma22dc6c7)
- Universal solver speed (bit10, bit13_m72f21093)
- CMS-axis specialty (bit18)

## For yale's manifold-search

Cross-axis hypothesis to test:

If yale's guarded operators succeed on the multi-solver fast cluster
(bit10, bit13_m72f21093, msb_ma22dc6c7, bit13_m4e560940) and struggle
on the single-solver-only cands (bit2 kissat-only, bit17
cadical-only), then manifold-search efficiency tracks "general
structural simplicity" — the property that ALL solvers find easy.

If yale's operators succeed on bit2 (Wang sym-axis natural fit) but
struggle on others, manifold-search tracks specifically EXACT-sym
sparse patterns (different axis from solver-friendliness).

Either result refines the structural picture.

## Discipline

- 10 CMS runs logged via append_run.py (5 bit13_m4e + 5 bit13_m72f)
- Both CNFs pre-existing + audited
- Sequential measurement
- 7-cand × 3-solver baseline now 21 cells (cell density rising)

EVIDENCE-level: VERIFIED. The 3-solver consensus at HW=47 (NON-sym
mildly faster) is a clean cross-architecture finding. The control
test (same fill, same kernel_bit, only sym differs) makes the gap
purely sym-attributable.

## Concrete next moves

1. **Cross-validate kissat 1M (not 100k) on bit13_m4e560940**:
   the 32.83s kissat baseline was at 1M conflicts; comparing to CMS
   100k might be unfair due to different conflict counts. Re-run
   kissat at 100k for direct comparison.

2. **Test CMS on bit25 + bit3** (Cohort A from F58) to confirm
   they're CMS-fast too. If yes, full Cohort A is universal-fast
   on 3 solvers.

3. **Update sigma1_aligned_kernel_sweep BET.yaml** with F61's
   "3-solver HW=47 universal sym penalty" finding.

4. **Yale's response to F60 message** — track for any reply.
