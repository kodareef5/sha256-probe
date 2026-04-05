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
| 20 | ? | running | Parallel search in progress |
| 32 | UNSAT* | N/A | *For known candidates only |

## Scaling Fit (with N=19)

T = 0.456 * 1.545^N

| N | Predicted |
|---|-----------|
| 20 | 46 min |
| 22 | 1.8 h |
| 24 | 4.3 h |
| 28 | 1 day |
| 32 | 6 days |

## Key Findings

1. Every non-degenerate width N=8-19 produces sr=60 collisions
2. Non-monotonic scaling: candidate choice dominates word width
3. Parallel candidate search gives near-linear speedup (9 candidates on 10 cores)
4. N=32 extrapolation: ~6 days single-machine, possibly less with right candidate
5. The barrier is computational, not topological
