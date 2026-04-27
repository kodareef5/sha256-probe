# F37: LM-min hypothesis FALSIFIED — HW predicts kissat speed, LM does not
**2026-04-27 12:30 EDT**

Tests F36's hypothesis: "if LM cost measures carry-constraint
complexity, the LM-min cand should solve faster on kissat."

## Setup

- **HW champion**: bit2_ma896ee41 (HW=45, LM=824)
- **LM champion**: msb_ma22dc6c7 (HW=48, LM=773)
- **Verified-cert baseline**: msb_m17149975 (HW unknown, sr=60 SAT verified)

All three under cascade_aux Mode A sr=60 encoding (same encoder,
same constraints structure). 5 seeds × 1M conflicts × parallel kissat
on Apple M5.

## Result

| cand | HW | LM | median wall | runs | observation |
|---|---:|---:|---:|---:|---|
| **bit2_ma896ee41** | **45** | 824 | **26.51s** | 5 | F30 (HW champion) |
| msb_m17149975 | n/a | n/a | 27.09s | 5 | F21 (verified cert) |
| **msb_ma22dc6c7** | 48 | **773** | **35.99s** | 5 | F37 (LM champion) |

**Differential analysis**:
- bit2 vs msb_ma22dc6c7: bit2 is **9.48s faster** (35% speedup)
- LM-min cand is the SLOWEST of the three — not faster.

## Hypothesis falsified

F36 conjectured: "If LM measures carry constraints, lower LM should
mean fewer per-conflict heuristic obstacles, so faster solve time."

**Observation**: msb_ma22dc6c7 has LM=773 (lowest of 67) but kissat
median wall is 35.99s (slower than HW-min cand and verified-cert
baseline).

**Conclusion**: per-conflict kissat heuristic does NOT track LM cost.
LM is a measure of CARRY-CONSTRAINT COMPLEXITY in the residual; kissat
solves something different (the full cascade_aux Mode A SAT instance).

## What DOES kissat track? Hypothesis: HW

| cand | HW | wall | (HW, wall) trend |
|---|---:|---:|---|
| bit2 | 45 | 26.51s | low HW → fast |
| (extrapolated) | ~48 | ? | medium |
| msb_ma22dc6c7 | 48 | 35.99s | high HW → slow |

This is consistent (preliminary) with HW being the predictor — but
N=2 is too small. Need cross-cand sweep to confirm.

## Implications

### For block2_wang strategy

The LM metric (F35/F36) is a **structural metric** for carry
constraints, not a SOLVER speedup predictor. Don't use LM-min for
cand selection on the SAT solving axis.

For solver-time-driven cand selection, **HW** appears to be the
operative metric. F28's bit2 still wins.

For Wang trail-design carry-constraint counting, **LM is the
correct metric**. F36's msb_ma22dc6c7 still wins.

The two metrics serve DIFFERENT purposes — both are useful, just for
different things.

### For paper Section 5

Both HW and LM are quantitatively meaningful, but for DIFFERENT
applications:
- HW: predicts kissat solver speed at moderate budgets (preliminary)
- LM: counts Wang-style carry constraints

A rigorous Section 5 acknowledges both metrics serve different
purposes.

### Negative result: F36's "LM is universally good" reading was wrong

F36 implicitly suggested LM-min cand is "best" overall. F37 shows
it's NOT — at least not on the kissat axis. This is a useful
correction.

## Per-conflict equivalence broadens

Previous F-series finding: "all distinguished cands have median wall
25-32s at 1M conflicts." F37 EXTENDS this: msb_ma22dc6c7 at 36s is
SLIGHTLY OUTSIDE this range, suggesting:

- The per-conflict equivalence holds for the F28 distinguished
  set (HW-min subset)
- But cands with higher HW (e.g., msb_ma22dc6c7's HW=48) sit on the
  slower edge of the range or beyond.
- HW=48+ cands take 30-40s, HW=45 cands take 26-28s.

Potential trend (hypothesis-only, N=3): each unit of HW adds ~3s of
wall time at 1M conflicts. Need cross-cand sweep to verify.

## Concrete next moves

1. **Cross-cand HW vs wall sweep**: pick 5 cands across HW range
   45-51, run kissat 5×1M each (parallel), plot HW vs median wall.
   Confirms or refutes HW-as-predictor hypothesis.
2. **F37 + F32 join**: enrich F32 corpus with kissat wall data
   per-cand (where available). Observable cross-cand structure.
3. **Refine F28's "champion" claim**: the bit2 NEW CHAMPION's
   advantage shows up in HW (lower) AND in kissat wall (faster).
   The LM cost is mid-pack but not relevant to solver speed.

## Discipline

- 5 kissat runs logged via append_run.py
- CNF audit: CONFIRMED sr=60 cascade_aux_expose
- Reproducible: seeds 1, 2, 3, 5, 7
- Parallelism caveat: 5 simultaneous kissat processes; per-process wall
  may be inflated vs sequential. But trend is consistent across 3 cands
  under same parallel setup.

EVIDENCE-level: VERIFIED for the LM-min hypothesis falsification on
this single cand. The HW-as-predictor hypothesis is HYPOTHESIS-only
(N=3, needs broader sweep).
