# Precision Homotopy: Complete Results

## sr=60 SAT Solve Time vs Word Width

| N | Result | Time (s) | Vars | Clauses | M[0] | dW[61] HW | Notes |
|---|--------|----------|------|---------|------|-----------|-------|
| 8 | SAT | 4.3 | 2544 | 10656 | 0x67 | 6 | |
| 9 | UNSAT | 0.2 | 2911 | 12193 | 0x1e | - | Degenerate (rotation cancellation) |
| 10 | SAT | 82 | 3258 | 13635 | 0x34c | 5 | |
| 11 | SAT | ~90 | 3592 | 15056 | 0x25f | 8 | |
| 12 | SAT | ~120 | 3936 | 16481 | 0x22b | 3 | |
| 13 | SAT | 220 | 4274 | 17902 | 0x7 | 8 | |
| 14 | SAT | 425 | 4611 | 19337 | 0x2f71 | 6 | |
| 15 | SAT | 266 | 4982 | 20909 | 0x1596 | 5 | Faster than N=14! |
| 16 | SAT | 870 | 5360 | 22477 | 0x48be | 5 | Previously TIMEOUT@600s |
| 17 | SAT | 315 | 5719 | 23968 | 0x15c1b | TBD | Faster than N=16! |
| 18 | ? | running | ~6018 | ~25253 | TBD | TBD | |
| 32 | UNSAT* | N/A | 10988 | 46255 | 0x17149975 | 17 | *For known candidates |

## Key Observations

1. **Every non-degenerate word width N=8-17 produces sr=60 collisions.**
   The barrier is NOT topological — it's computational/candidate-dependent.

2. **Scaling is non-monotonic**: N=15 < N=13 < N=14 and N=17 < N=16.
   Candidate properties dominate word width effects.

3. **dW[61] HW correlates with solvability**: All SAT instances have
   dW[61] HW in [3, 8]. The N=32 UNSAT candidate has HW=17.

4. **Exponential fit**: T ≈ 0.1 × 1.77^N, but non-monotonicity makes
   extrapolation unreliable. N=32 estimate: ~95 days (with caveats).

5. **SA cannot find these collisions** even at N=8 (validated).
   Only CDCL SAT solvers with constraint propagation succeed.
