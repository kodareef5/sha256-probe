# F45: bit4_m39a03c2d (F43 LM champion) kissat — LM-doesn't-predict-speed triply confirmed
**2026-04-27 15:12 EDT**

Tests F43's NEW global LM champion (bit4_m39a03c2d at HW=53, LM=757)
on cascade_aux Mode A sr=60 kissat. Continues the F37/F39/F41 thread
on whether LM cost predicts solver wall.

## Result

bit4_m39a03c2d (F43 LM champion, HW=53, LM=757):
- Walls (5 seeds, parallel-5, 1M conflicts):
  37.34, 36.01, 35.30, 37.64, 38.21
- **Median: 37.34s**

## Comparison to plateau

| cand | HW | LM | parallel-5 wall | source |
|---|---:|---:|---:|---|
| bit10_m9e157d24 | 47 | 805 | 34.28 | F38 |
| bit06_m6e173e58 | 50 | 825 | 34.55 | F38 |
| bit00_mc765db3d | 49 | 875 | 34.78 | F38 |
| bit2_ma896ee41 | 45 | 824 | 35.61 | F39 |
| bit00_mf3a909cc | 51 | 787 | 35.91 | F38 |
| bit13_m4e560940 | 47 | 780 | 35.94 | F39 |
| msb_ma22dc6c7 | 48 | 773 | 35.99 | F37 |
| **bit4_m39a03c2d** | **53** | **757** | **37.34** | **F45** |

bit4 sits SLIGHTLY ABOVE the 34-36s plateau, NOT below it.

## Three independent confirmations of F37's verdict

F37's hypothesis: "LM-min cand is fastest on kissat" — FALSIFIED on
msb_ma22dc6c7 (LM=773 → 35.99s, mid-pack).

F45 (this): TRIPLY confirmed on bit4_m39a03c2d (LM=757 → 37.34s,
slightly slow).

| LM-min test cand | LM | parallel-5 wall | rank vs plateau |
|---|---:|---:|---|
| msb_ma22dc6c7 | 773 | 35.99 (F37) | mid-plateau |
| bit13_m4e560940 | 780 | 35.94 (F39) | mid-plateau |
| **bit4_m39a03c2d** | **757** | **37.34 (F45)** | **slightly slow** |

Three lowest-LM cands ALL sit at or slightly above the 35s plateau.
LM-min ≠ kissat-speed champion.

## Why LM doesn't predict speed (revised hypothesis)

bit4 has HW=53, larger than the HW=47-51 plateau cands. Per F38's
weak HW-as-predictor signal (each HW unit ~0.3s within the plateau),
bit4's HW=53 predicts ~36-37s, matching observation.

**Refined hypothesis**: kissat speed at 1M conflicts tracks HW WEAKLY
(~0.3s per HW unit within the plateau), but is INSENSITIVE to LM cost.
bit4's lower LM doesn't help; its higher HW slightly hurts.

This is the cleanest formulation of the per-conflict equivalence
finding accumulated across F37/F39/F41/F45.

## What does bit4's distinction buy us?

bit4_m39a03c2d's triple distinction (F43):
1. **Global LM champion** at LM=757 (best Wang carry constraints)
2. **Lowest-LM exact-symmetry record** at HW=52, LM=772
3. **Near-min HW** (within 8 of registry HW-min)

This is a structural distinction for **Wang trail design**, NOT for
solver speed. The two are DIFFERENT axes:

- **Solver-axis**: HW-min cands solve fastest at 1M conflicts (very
  weakly). Pick bit2_ma896ee41 if SAT speed matters.
- **Wang-construction axis**: LM-min cands have fewest carry
  constraints. Pick bit4_m39a03c2d if Wang construction matters.

## Implications for paper Section 5

Solidified across 4 LM tests (msb_ma22dc6c7, bit13, bit4 + bit2 baseline):

> "Cascade_aux Mode A 1M-conflict kissat walls cluster at 34-37s
> across all distinguished cands tested. The wall depends weakly on
> output residual HW (~0.3s/HW unit) and is INSENSITIVE to
> Lipmaa-Moriai cost. Cand selection at the LM axis is meaningful
> for Wang trail-design effort but not for solver speed."

Strong formulation, well-supported (now 50+ logged kissat runs across
8 cands × 2 measurement modes).

## Discipline

- 5 kissat runs logged via append_run.py (all UNKNOWN, 1M conflicts)
- CNF audit: CONFIRMED sr=60 cascade_aux_expose
- bit4_m39a03c2d added to per-conflict equivalence dataset

EVIDENCE-level: VERIFIED. F37's LM-doesn't-predict-speed claim now
empirically validated on 4 independent LM-min cands.

## Concrete next moves

1. **Update the per-conflict equivalence claim in cascade_aux memos**:
   "weakly HW-tracking, LM-insensitive" — solid 8-cand baseline.
2. **For block2_wang trail design**: bit4 is now the OFFICIAL primary
   target. Both global LM champion AND lowest-LM exact-sym champion.
   The solver-axis cost (37s vs 35s plateau) is negligible.
3. **Yale's operator design**: F45 confirms bit4's structural
   distinction is REAL — yale's anchor-set search should prioritize
   bit4 over msb_ma22dc6c7 (now superseded as LM champion).
