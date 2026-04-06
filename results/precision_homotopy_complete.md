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
| 22 | SAT | 2546 | Single candidate, fill=0x3fffff |
| 23 | cand1 TIMEOUT | >4h | cand2 solving (1.5h in) |
| 24 | SAT | 4206 | M[0]=0x221e85, fill=0x0 (70 min) |
| 25 | SAT | ~5200 | M[0]=0xa0e50f, fill=0xaa (~87 min) |
| 26 | cand1 TIMEOUT | >4h | cand2 solving |
| 27 | solving | >7.5h | 3 candidates, approaching 8h timeout |
| 28 | solving | >7.5h | 1 candidate, approaching 8h timeout |
| 32 | UNSAT* | N/A | *For known candidates only |

## Scaling Fit (with N=24)

T = 1.684 * 1.393^N

| N | Predicted |
|---|-----------|
| 25 | 1.8 h |
| 26 | 2.6 h |
| 28 | 5.0 h |
| 32 | 18.8 h |

## Key Findings

1. Every non-degenerate width N=8-22, N=24 produces sr=60 collisions
2. N=23 solving, N=25-28 solving in parallel (9 cores)
3. C candidate scanning is 200-300x faster than Python
4. N=32 extrapolation: ~19 hours single-machine
5. The barrier is computational, not topological
