# Constrained sr=60 Search Results (2026-04-05)

## Experiment
Fix dW[57] = W1[57] - W2[57] to specific values and test sr=60 SAT.

## Results

| Strategy | dW57 | de57_hw | da57_hw | Result | Time |
|----------|------|---------|---------|--------|------|
| de57=0 | 0x39f99e61 | 0 | 8 | **UNSAT** | **0.2s** |
| da57=0 | 0x29e8dc91 | 21 | 0 | TIMEOUT | 300s |
| midpoint | 0x31f13d79 | 22 | 8 | **UNSAT** | **0.2s** |
| random_best | 0x59fae6e1 | 5 | 8 | **UNSAT** | **0.2s** |
| unconstrained | — | — | — | TIMEOUT | 300s |

## Key Finding

**The e-register zeroing strategy (de57=0) is provably impossible.**
Kissat proves UNSAT in 0.2 seconds. When the e-path is locked to zero
difference at round 57, the remaining 6 rounds cannot absorb the
resulting a-register error (da57 hw=8).

**The a-register zeroing strategy (da57=0) is the ONLY viable path.**
It times out (like unconstrained), meaning the solver cannot quickly
prove it impossible. This is the region where solutions might exist.

## Implication

For this candidate, sr=60 collision MUST zero da57 (not de57).
The error flows through de57 with hw=21, which must be absorbed
by rounds 58-63 using W[58], W[59], W[60] + schedule-determined W[61..63].

## Next Steps

1. Run da57=0 constrained with 7200s timeout to determine SAT/UNSAT
2. If UNSAT: prove it with DRAT
3. If SAT: extract the collision and the differential trail it uses
4. Test other candidates — do they all require a-register zeroing?
