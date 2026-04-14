# Paper Figures and Data Tables — Ready to Plot

## Figure 1: Cascade Diagonal State-Diff Matrix
Heat map showing 0/C/V pattern across 8 registers × 7 rounds.
Data: `results/20260413_cascade_diagonal_theorem.md`

## Figure 2: Collision Scaling Law (4 N-mod-4 Classes)
Log-linear plot of log2(collisions) vs N, with 4 trend lines.
Data:
| N | Best | log2 | N mod 4 |
|---|------|------|---------|
| 4 | 146 | 7.19 | 0 |
| 5 | 1024 | 10.00 | 1 |
| 6 | 83 | 6.37 | 2 |
| 7 | 373 | 8.54 | 3 |
| 8 | 1644 | 10.68 | 0 |
| 9 | 14263 | 13.80 | 1 |
| 10 | 1467 | 10.52 | 2 |
| 11 | 2720 | 11.41 | 3 |
| 12 | ~4900 | ~12.25 | 0 (running) |

## Figure 3: de58 Image Size vs N
Bar chart showing |de58| at each N, colored by hw(db56).
Data:
| N | |de58| | hw(db56) | Match 2^hw |
|---|--------|---------|-----------|
| 4 | 2 | 1 | YES |
| 6 | 8 | 3 | YES |
| 8 | 8 | 3 | YES |
| 10 | 16 | 4 | YES |
| 11 | 32 | 5 | YES |
| 12 | 512 | 9 | YES |
| 13 | 32 | 5 | YES |
| 14 | 32 | 5 | YES |
| 16 | 256 | 8 | YES |
| 32 | 1024 | 17 | NO (carry collapse) |

## Figure 4: Kernel Advantage vs N
Line plot showing best/MSB ratio → converging to 1.
Data:
| N | Advantage |
|---|-----------|
| 4 | 3.0x |
| 6 | 1.7x |
| 8 | 6.3x |
| 10 | 1.6x |
| 11 | 1.07x |

## Figure 5: sr=61 Cascade Break
Diagram showing diagonal structure at r60 with cascade break point.
The schedule-determined W[60] matches cascade with P = 2^(-N).

## Figure 6: Collision Difficulty Scaling
Plot of (4N - log2(C)) vs N showing 3.33*N growth.
N=32 point at 101.7 bits vs SAT solve at ~2^35 (effective).

## Table 1: Complete sr=60 Collision Counts (Mini-SHA)
All N from 4 to 12 with best kernel, MSB, fill, candidate.

## Table 2: de-set Measurement
de57/de58/de59/de60 cardinalities at N=4,6,8,10,11,12,13,14,32.
All de57/de59/de60 = 1 (constant). Only de58 varies.

## Table 3: sr=61 Impossibility — Four Independent Proofs
| Proof | Method | Source | Key number |
|-------|--------|--------|------------|
| 1 | Sigma1 conflicts | Server | 10.8% |
| 2 | Critical pairs | Macbook | Rotation barrier |
| 3 | Carry invariants | GPU-laptop | 0/10K |
| 4 | Cascade break | GPU-laptop | P = 2^(-N) |
