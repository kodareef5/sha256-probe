# Correction: predictor-vs-kissat-memory is NOT monotonic on 4 points

The earlier finding (`20260424_predictor_kissat_signal.md`) reported a 3.5× peak-memory delta between predict_hard_bits lb=15 and lb=29. That observation is real. The interpretation that the predictor signals kissat memory growth is **overstated**.

## Full 4-point curve (5-min kissat, seed=5, aux-force mode)

| Candidate | lb | sr | Peak memory | Process time |
|---|---:|---:|---:|---|
| cand_n32_bit19_m51ca0b34_fill55555555 (priority) | 15 | 61 | **135 GB** | 4m 55s |
| cand_n32_msb_m44b49bc3_fill80000000 | 22 | 60 | **337 GB** | 4m 53s |
| cand_n32_msb_m17149975_fillffffffff (MSB cert) | 26 | 60 | **193 GB** | 4m 53s |
| cand_n32_msb_m189b13c7_fill80000000 | 29 | 60 | **467 GB** | 4m 55s |

**The peak-memory ranking does NOT follow lb monotonically.** lb=22 has higher memory than lb=26. The 2-point comparison (lb=15 vs lb=29) gave a clean 3.5× ratio that misled into a strong-correlation claim.

## What's actually true

The predictor:
- IS valid for MITM table sizing (verified 8/8 candidates with extras in [0,3] vs empirical sweep)
- Does NOT reliably predict kissat solve-time-or-memory at 5-min budgets
- The 3.5× lb=15-vs-lb=29 delta is just two extreme samples of a noisy distribution

Other factors plausibly dominating kissat memory at 5min:
- sr level (lb=15 is sr=61, others sr=60 — different problem class)
- Specific candidate's structural features beyond hard-residue size
- 5-min is too short for stable memory/conflict statistics
- kissat's heuristics are seed-sensitive in ways the predictor doesn't capture

## Honest reassessment

The closed-form predictor is a clean structural result for MITM forward-table size. It is NOT an empirically validated SAT-solver-difficulty predictor — yet. To establish that would require:
- Multi-seed runs per candidate (at least 5 seeds)
- Longer budget (1h+) for stable measurement
- Wider candidate sample (10+ across the prediction range)

That's ~50 CPU-h. Not a 5-minute experiment.

## Run record

- run_20260425_001827_mitm_residue_kissat_seed5_bdb1ef3b (lb=22)
- run_20260425_001827_mitm_residue_kissat_seed5_4b02ca9e (lb=26)
- (priority and high-prediction runs are in the prior 001004 set)

Dashboard now: 15 runs, 0 audit failures.

## What stands

- predict_hard_bits.py is correct for MITM table size (verified)
- Priority candidate cand_n32_bit19_m51ca0b34_fill55555555 with lb=15 remains the natural target IF MITM tables are the path
- The "predictor signals solver behavior" claim from the 2-point study is retracted pending more data

This correction is shipped explicitly to prevent the prior writeup from being treated as an established result.
