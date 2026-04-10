# CRITICAL: Phase transition SCALES with N — collision needs ALL of W[60] free

## sr=60.5 results across word widths

| N | K_max (SAT) | K_min (UNSAT) | % of W[60] that must be free |
|---|-------------|---------------|------------------------------|
| 8 | 4 (SAT) | 5 (UNSAT) | > 37.5% (4/8 free minimum) |
| 10 | 0 (SAT) | 1 (TIMEOUT) | > 90% (9/10 free minimum) |
| 32 | ? | ? | extrapolates to ~100% |

At N=8: you can enforce 4 of 8 bits and still find collision.
At N=10: enforcing just 1 of 10 bits already kills it.

## What this means

If the trend holds at N=32, the collision requires essentially ALL of
W[60] to be free. Even sr=60.0001 (one bit enforced) would be UNSAT.
This explains why sr=61 is so definitively impossible — it enforces ALL
32 bits, but the collision can't tolerate even 1.

## Candidate dependency

Multi-candidate test at N=8 shows the transition is NOT universal:
- cand1 (fill=0xff): K=4 SAT, K=5 UNSAT (sharp)
- cand2 (fill=0x00): K=4 TIMEOUT, K=5 UNSAT (the transition moved left!)

Some candidates are easier than others even at the same K value.

## Also complete: Cube attack confirms degree ≤ 9

Register h bit 0 cube attack at N=4: constant superpolys appear at k=5+,
confirmed degree ≤ 9 (exact ANF says 8). Consistent.

## Running: sr=60.5 N=16 and N=32 sweeps, near-collision N=32 skip-h
