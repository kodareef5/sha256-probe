# 4-point kissat metrics: signal is sr-level, not predict_hard_bits

Detailed kissat metrics from the 4-point predictor curve. Earlier writeups
suggested the predictor correlated with kissat behavior, then retracted on
non-monotonic memory. This deeper look identifies the actual confound.

## Raw data (5-min runs, seed=5, aux-force, kissat 4.0.4)

| Candidate | lb | sr | Conflicts | Decisions | Propagations | Restarts | Peak RSS (GB) |
|---|---:|---:|---:|---:|---:|---:|---:|
| priority_bit19_m51ca0b34 | 15 | **61** | 7.35M | 24.93M | 785.8M | **173k** | 135 |
| m44b49bc3 | 22 | 60 | 7.27M | 29.32M | 745.8M | 211k | 354 |
| MSB_cert m17149975 | 26 | 60 | 7.24M | 30.01M | 753.0M | 209k | 193 |
| m189b13c7 | 29 | 60 | 7.62M | 29.90M | 732.6M | 208k | 467 |

## Metric-by-metric interpretation

- **Conflicts**: 7.2-7.6M across all 4. Range 5%. Essentially flat — not predictive.
- **Decisions**: lb=15 at 24.9M vs others at 29-30M. **17% lower** for lb=15. Possible signal.
- **Propagations**: 732-786M, lb=15 actually HIGHEST. Anti-correlated.
- **Restarts**: lb=15 at 173k vs others at 208-211k. **17% lower** for lb=15. Same direction as decisions.
- **Peak RSS**: 135-467 GB, not monotonic with lb.

## The confound

**lb=15 is the ONLY sr=61 candidate in the set; the other 3 are sr=60.** The 17% lower decisions/restarts could be:
- A real predictor effect (lb really does signal solve work)
- An sr-level effect (sr=61 force-mode happens to be easier for kissat than sr=60 in this brief window — possibly because force-mode at sr=61 is contradiction-rich and propagates conflicts faster)
- Noise — 5 minutes × 1 seed is a small sample

The 3 sr=60 candidates cluster tightly on decisions/restarts (29-30M decisions, 208-211k restarts) regardless of lb (22, 26, 29). Within sr=60, the predictor shows NO signal in these 5-min metrics.

## Conclusion

The "predictor signals kissat behavior" hypothesis is **not supported by clean within-sr comparisons**. The cross-sr observation is confounded.

To establish a real correlation:
1. Run multiple seeds at fixed (sr, lb) to characterize noise.
2. Run multiple candidates at fixed sr-level spanning the lb range.
3. Use a longer budget where solver enters its asymptotic regime.

Estimate: 5 sr=60 candidates × 3 seeds × 30min = ~7.5 CPU-h. Or 3 sr=61 candidates × 3 seeds × 30min = ~4.5 CPU-h. Either is feasible.

For now: the closed-form predictor's value remains its **MITM-table-size correctness** (verified 8/8). Its solver-difficulty implications are unestablished.

## Run record

All 4 runs committed at `headline_hunt/bets/mitm_residue/results/runs/`. dashboard.md shows 15 mitm_residue runs total.
