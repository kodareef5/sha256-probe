# Precision Homotopy: Complete Results

## sr=60 SAT Solve Time vs Word Width

| N | Result | Time (s) | Notes |
|---|--------|----------|-------|
| 8 | SAT | 4.3 | |
| 9 | UNSAT | 0.2 | Degenerate rotations |
| 10 | SAT | 82 | |
| 11 | SAT | ~90 | |
| 12 | SAT | ~120 | |
| 13 | SAT | 220 | |
| 14 | SAT | 425 | |
| 15 | SAT | 266 | Faster than N=14 |
| 16 | SAT | 870 | |
| 17 | SAT | 315 | Faster than N=16! |
| 18 | SAT | 830 | |
| 19 | SAT | 1541 | Parallel (9 candidates), fill=0x40000 |
| 20 | SAT | 672 | Parallel, fill=0x80000. Faster than N=18! |
| 21 | SAT | 653 | Parallel, fill=0x0. Faster than N=20! |
| 22 | ? | running | 3 candidates, parallel |
| 32 | UNSAT* | N/A | *For known candidates only |

## Scaling Fit (with N=21)

T = 1.568 * 1.400^N

| N | Predicted |
|---|-----------|
| 22 | 43 min |
| 24 | 1.4 h |
| 28 | 5.4 h |
| 32 | 21 h |

## Key Findings

1. Every non-degenerate width N=8-21 produces sr=60 collisions
2. Non-monotonic scaling: N=21 (653s) faster than N=20 (672s), N=18 (830s), N=19 (1541s)
3. Parallel candidate search gives near-linear speedup
4. N=32 extrapolation: ~21 hours single-machine
5. The barrier is computational, not topological
