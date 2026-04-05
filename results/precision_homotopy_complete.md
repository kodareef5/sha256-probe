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
| 32 | UNSAT* | N/A | *For known candidates only |

## Scaling Fit (with N=20)

T = 0.869 * 1.466^N

| N | Predicted |
|---|-----------|
| 21 | 45 min |
| 22 | 1.1 h |
| 24 | 2.3 h |
| 28 | 10.8 h |
| 32 | 2 days |

## Key Findings

1. Every non-degenerate width N=8-20 produces sr=60 collisions
2. Non-monotonic scaling: N=20 (672s) faster than N=18 (830s) and N=19 (1541s)
3. Parallel candidate search gives near-linear speedup
4. N=32 extrapolation: ~2 days single-machine, possibly less with right candidate
5. The barrier is computational, not topological
