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
| 27 | TIMEOUT | >8h | 3 candidates all timed out |
| 28 | TIMEOUT | >8h | 1 candidate timed out |
| 29 | solving | — | 2 candidates, first-ever attempt (laptop) |
| 30 | solving | — | 1 candidate, first-ever attempt (laptop) |
| 31 | solving | — | 2 candidates, first-ever attempt (laptop) |
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

1. Every non-degenerate width N=8-25 produces sr=60 collisions (N=23 filled!)
2. N=26-31 solving on laptop (14 cores), N=27-28 timed out on MacBook
3. N=23 required 7th candidate (fill=0xf0) — candidate diversity matters
4. Scaling accelerating: ~2.35x/bit after N=25 (was 1.37x/bit)
5. N=32 extrapolation: ~24 days at accelerated rate (was ~19h at old rate)
6. The barrier is computational, not topological
