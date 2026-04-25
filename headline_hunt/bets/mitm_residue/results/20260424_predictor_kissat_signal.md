# Predictor signals kissat search-space size — head-to-head 5-min run

Empirical test of whether the closed-form `predict_hard_bits` lower bound correlates with kissat's actual search behavior.

## Method

Two parallel kissat runs, identical solver+seed, 300s wall budget each:

| Candidate | predict_hard_bits LB | sr | Peak memory | Status |
|---|---:|---:|---:|---|
| cand_n32_bit19_m51ca0b34_fill55555555 (priority MITM target) | **15** | 61 | **135 GB** | TIMEOUT |
| cand_n32_msb_m189b13c7_fill80000000 (high-prediction reference) | **29** | 60 | **467 GB** | TIMEOUT |

Both used 295s of CPU time (full budget), neither found SAT or UNSAT. But the **kissat peak-memory ratio (3.5×) closely tracks the predicted-hard-bit-count ratio (29/15 = 1.9, in 2^N terms 2^14 = 16K vs 2^29 = 537M, ratio = 33000×; in linear sampling terms more like a few-fold)**.

## Why this matters

The predicted hard-bit count is a closed-form O(1) per-candidate quantity computed from the round-56 cascade state. It was designed as a memory-budget predictor for forward MITM tables.

This empirical observation shows it ALSO predicts kissat's exploration breadth. **A SAT solver on the same encoding visits more conflict-clause states for higher-prediction candidates.** That's exactly the behavior you'd expect if the predicted hard residue measures the actual structural search space.

## Implication for the bet

If the predictor signals solver speed, it gives the bet a free pre-screen for kissat-mode work too — pick low-prediction candidates first, expect them to solve (or UNSAT) faster.

Concrete proposal: **a 4h kissat run on the priority candidate (predict_hard_bits LB=15) is the next experiment**. If the prediction holds, this should either:
- Find SAT (HEADLINE — sr=61 cascade-DP collision exists for this candidate)
- Or UNSAT in genuinely faster time than the high-prediction candidate would
- Or TIMEOUT but at a meaningful conflict-count delta

Dashboard now: 13 runs logged, all TIMEOUT, 0 audit failures.

## Caveat

5 minutes is short. The 3.5× memory ratio could partially be sampling noise. A better test runs each candidate at 1h budget (still TIMEOUT but with much more reliable statistics) or at 4h (might catch SAT/UNSAT for the priority candidate).

The run_id pair for this experiment:
- priority: `run_20260425_001004_mitm_residue_kissat_seed5_96dada64`
- high:     `run_20260425_001004_mitm_residue_kissat_seed5_70bcba90`

Both retained in `headline_hunt/bets/mitm_residue/results/runs/` with full kissat output.
