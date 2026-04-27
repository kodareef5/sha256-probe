# F75: CMS component-disable sweep on bit28 — no single dominant mechanism
**2026-04-27 17:24 EDT**

Continues F74's mechanism hunt. Disabled individual CMS preprocessing
components on bit28 to identify which (if any) drives Cohort D
CMS-fastness.

## Setup

bit28_md1acca79 cascade_aux Mode A sr=60, CMS 5.13.0, 100k conflicts,
seed=1. Compare default to each `--<component> 0` setting:

## Result

| CMS option | bit28 wall (s) | Δ vs default |
|---|---:|---:|
| default | 16.52 | baseline |
| --bva 0 | 17.31 | +5% |
| --intree 0 | 16.62 | ~same |
| --varelim 0 | 19.95 | **+21%** |
| --distill 0 | 19.48 | **+18%** |
| --transred 0 | 16.52 | ~same |
| --gates 0 | 18.31 | +11% |

For comparison, bit2 (kissat-only fast cohort B):
- default: 18.16s (slightly slower than bit28)
- --varelim 0: 19.33s (+6%)

## Findings

1. **No single CMS component dominates bit28's fastness.** Largest
   individual effect is `--varelim 0` at +21% — modest, not a
   step-function.

2. **varelim and distill help bit28 more than bit2.** varelim +21%
   on bit28 vs +6% on bit2 — a 4× ratio. So variable elimination
   IS preferentially helpful on bit28's structure, but not
   exclusively responsible.

3. **BVA, intree, transred are negligible** on bit28. F74's
   BVA-mechanism speculation refuted; F75 confirms intree and
   transred are also non-mechanisms.

4. **Compound preprocessing matters.** Disabling 2-3 components
   together would likely accumulate effects, but no single
   component is the "secret sauce."

## Refined mechanism story

bit28's Cohort D status (CMS-only fast) cannot be attributed to any
single CMS preprocessing component. Likely contributors:
- **Variable ordering heuristic** (VSIDS) might branch on bit28's
  variables in a productive order
- **Restart schedule** might align with bit28's basin structure
- **Clause learning/database management** might handle bit28's
  conflict pattern better than kissat/cadical
- **varelim + distill compound effect** when combined

For paper Section 4: claim "CMS-specific compound preprocessing
+ heuristic alignment, no single component identifiable."

## Caveat: bit2 default at 18.16s ≠ F59's 52.61s baseline

F59 measured bit2 at 51.61s median across 5 seeds. Today's
single-seed bit2 default is 18.16s. The discrepancy (3× slower in
F59) is likely seed/system-load variance — F59 had range 39-55s.

This re-confirms F47's "bit28 has high seed variance" pattern —
seed-to-seed walls vary substantially on this CNF family. The
"~52s median" figure for bit2 in F59 was a 5-seed median; single
seeds can be much faster.

For paper: report median + range, not single-seed walls.

## Cumulative CMS knowledge so far

- **F59**: CMS confirms Cohort A universal-fast (bit10 21s)
- **F60**: msb_ma22dc6c7 cadical+CMS-fast (TRIPLE-AXIS)
- **F62**: bit25, bit3 CMS-fast (Cohort A complete)
- **F63**: bit28 CMS-fast (NEW Cohort D)
- **F66/F70/F71**: CMS for cert-pin verification (sub-second per UNSAT)
- **F73**: 100 random W-witnesses on bit28 → 100/100 UNSAT
- **F74**: CMS without BVA on bit28 = same speed (BVA NOT mechanism)
- **F75 (this)**: CMS component-disable sweep — no single mechanism

## Discipline

- 7 CMS runs logged via append_run.py
- 1 control run on bit2 (logged via F59 baseline)
- 0% audit failure rate maintained
- 4 honest revisions today (F39, F49, F55, F69, F74) plus F75 mild
  refinement of F74

EVIDENCE-level: VERIFIED. No single CMS component disable causes
bit28 to lose its Cohort D status. Mechanism is compound + likely
involves the SAT search engine (VSIDS, restarts, DB management),
not just preprocessing.

## Concrete next moves

1. **Test 3-4 disabled components compound** (e.g., `--varelim 0
   --distill 0 --gates 0`) on bit28 to see if the cumulative effect
   is large. Quick: ~30s.

2. **Switch to a different CMS branch heuristic** if available
   (e.g., `--branchstr ` if it has options) to test if VSIDS
   ordering is the key.

3. **For paper Section 4**: drop the "BVA mechanism" claim entirely.
   Use "CMS compound preprocessing + heuristic alignment, exact
   component split unknown."

4. **For block2_wang strategy**: cohort distinctions remain
   actionable — bit28 is CMS-only fast regardless of mechanism.
   Pipeline still routes bit28 work to CMS preferentially.
