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

1. Every non-degenerate width N=8-25, N=27 produces sr=60 collisions
2. N=27 cracked by wider candidate search (fill=0x3ffffff, not tried on MacBook)
3. Candidate diversity is CRITICAL: N=23 needed cand 7/7, N=27 needed cand 2/8
4. N=26, 28-31 still solving on laptop (15 Kissat processes)
5. N=27 at 10340s (2.9h) — NOT accelerating as feared, consistent with original fit
6. The barrier is computational, not topological
