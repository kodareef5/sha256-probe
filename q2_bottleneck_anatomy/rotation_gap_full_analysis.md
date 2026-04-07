# Rotation Gap Analysis: Full Sigma1 Family vs SAT Status

## Data (N=20 through N=32)

| N | Sigma1 rots | g1 | g2 | small sig1 | status |
|---|-------------|----|----|------------|--------|
| 20 | 4, 7, 16 | 3 | 9 | sm=1 | SAT |
| 21 | 4, 7, 16 | 3 | 9 | sm=1 | SAT |
| 22 | 4, 8, 17 | 4 | 9 | sm=1 | SAT |
| 23 | 4, 8, 18 | 4 | 10 | sm=2 | SAT |
| 24 | 4, 8, 19 | 4 | 11 | sm=1 | SAT (slow) |
| 25 | 5, 9, 20 | 4 | 11 | sm=2 | SAT |
| 26 | 5, 9, 20 | 4 | 11 | **sm=1** | **TIMEOUT** |
| 27 | 5, 9, 21 | 4 | 12 | sm=2 | SAT |
| 28 | 5, 10, 22 | 5 | 12 | sm=2 | SAT |
| 29 | 5, 10, 23 | 5 | 13 | sm=2 | TIMEOUT(?) |
| 30 | 6, 10, 23 | 4 | 13 | sm=2 | SAT |
| 31 | 6, 11, 24 | 5 | 13 | sm=2 | TIMEOUT |
| 32 | 6, 11, 25 | 5 | 14 | sm=2 | racing |

## Findings

**Single-factor hypotheses ruled out:**
- N=26 has sm=1 (small sigma1 gap=1) and TIMEOUT — original hypothesis
- BUT N=20, 21, 22, 24 all have sm=1 and SAT
- So sm=1 alone is not the cause

**Sigma1 first-gap g1=5 candidates:**
- N=28: SAT
- N=29: TIMEOUT(?)
- N=31: TIMEOUT
- N=32: racing
- 1 SAT, 2 TIMEOUT — not a clean predictor

**The non-monotonicity is multi-factorial.** Possible factors:
1. Rotation gap interactions (S1 + sigma1 + Sigma0)
2. Candidate density at the specific width
3. Constant truncation effects (K[i] & MASK)
4. SAT solver heuristic interactions with the problem geometry

## Implication

We cannot predict TIMEOUT widths from rotation gaps alone. Empirical testing
remains necessary. N=32 has gaps in line with other SAT widths, so structural
arguments suggest it should be solvable — the question is purely compute time
and candidate selection.

EVIDENCE level: HYPOTHESIS — pattern observed but underdetermined.
