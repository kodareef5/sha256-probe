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
| 23 | SAT | 4185 | M[0]=0x71453e, fill=0xf0 (69.7 min), cand 7/7 |
| 24 | SAT | 4206 | M[0]=0x221e85, fill=0x0 (70 min) |
| 25 | SAT | ~5200 | M[0]=0xa0e50f, fill=0xaa (~87 min) |
| 26 | solving | — | 2 candidates, ~50 min in (laptop) |
| 27 | SAT | 10340 | M[0]=0x2bfb506, fill=0x3ffffff (2.9h), cand 2/8. MacBook's 3 cands timed out — different fill cracked it! |
| 28 | SAT | 11220 | M[0]=0x97978c3, fill=0xaa (3.1h), cand 5/8. MacBook's 1 cand timed out — different fill! |
| 29 | solving | — | 2 candidates, first-ever attempt (laptop) |
| 30 | SAT | 30570 | M[0]=0x7bffba9, fill=0x55 (8.5h), single candidate, first-ever! |
| 31 | solving | — | 2 candidates, first-ever attempt (laptop) |
| 32 | **RACING** | — | 12 candidates × 2 solvers = 24 instances on 24-core Linux |

## Scaling Fit (with N=30)

T ≈ 1.5 * 1.4^N (approximate, non-monotonic scatter)

| N | Actual | Predicted |
|---|--------|-----------|
| 27 | 2.9h | 2.6h |
| 28 | 3.1h | 3.6h |
| 30 | 8.5h | 7.1h |
| 31 | — | ~10h |
| 32 | — | ~14-20h |

## Key Findings

1. Every non-degenerate width N=8-25, N=27-28, N=30 produces sr=60 collisions
2. NO phase transition detected through N=30 (2 bits from full SHA-256)
3. Candidate diversity is CRITICAL: wrong candidates timeout, right ones solve
4. N=26, 29, 31 solving on Mac laptop
5. **N=32 race launched on 24-core Linux: 12 candidates × 2 solvers**
6. The barrier is computational, not topological — scaling is smooth 1.4^N
7. N=32 extrapolation: 14-20h single-thread, ~1-2h with lucky candidate on 24 cores
