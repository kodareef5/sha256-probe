# E-Path Diff Pruning — The Polynomial-Time Signal

## Discovery

The e-register diff (de) at each round takes a TINY fraction of possible values.
This enables massive forward-search pruning.

## Data

### N=4 (49 collisions, 2^16 = 65536 search space)

| Round | Distinct de | Out of 2^N | Fraction |
|-------|------------|-----------|----------|
| 57 | 4 | 16 | 25.0% |
| 58 | 3 | 16 | 18.8% |
| 59 | 3 | 16 | 18.8% |

Product: 36. Speedup: 65536/36 = **1820x**.

### N=8 (260 collisions, 2^32 = 4.3B search space)

| Round | Distinct de | Out of 2^N | Fraction |
|-------|------------|-----------|----------|
| 57 | 25 | 256 | 9.8% |
| 58 | 32 | 256 | 12.5% |
| 59 | 13 | 256 | 5.1% |
| 60 | **1** | 256 | **0.4%** |

Product: 10,400. Log2: 13.3 vs 32 brute. Speedup: **413,000x**.

## Key Observations

1. **de60 is CONSTANT** (1 value) across all 260 collisions. This is the
   cascade completing: the e-path diff is fully determined by the cascade
   structure at round 60. This matches the carry automaton finding that
   d+T1=new_e is 100% invariant at round 60+.

2. **The fraction of valid de values DECREASES with N**:
   - de57: 25% at N=4 → 9.8% at N=8
   - de58: 18.8% → 12.5%
   - de59: 18.8% → 5.1%
   This suggests STRONGER pruning at larger N.

3. **The effective search space is ~2^{1.66N}** (from log2 scaling):
   - N=4: log2(36) = 5.2 ≈ 1.30N
   - N=8: log2(10400) = 13.3 ≈ 1.66N
   Even if this is mildly exponential (not polynomial), it's VASTLY
   better than 2^{4N} brute force.

## The Algorithm

Forward search with de-pruning at each round:
1. For each W57 in {0..2^N-1}: compute de57. If de57 ∉ valid_de57, skip.
2. For surviving (W57, W58): compute de58. If de58 ∉ valid_de58, skip.
3. Continue through rounds 59, 60.
4. For survivors, check full collision (rounds 61-63).

Expected evaluations: product of |valid_de_sets| ≈ 10K at N=8.

## The Obstacle

The valid de sets are computed FROM the known collisions. At N=32, we don't
know the collisions yet. Two paths forward:
a) **Structural prediction**: de60 is provably constant (from cascade). Can
   we predict de57-59 structurally?
b) **Iterative refinement**: start with no pruning, find first collision,
   extract de values, prune for subsequent collisions.
c) **Small-N transfer**: if de sets at N=8 predict de sets at N=32 (via
   truncation or scaling), use them as heuristic pruning.

## For the Paper

This is Section 6: "The E-Path Constraint" — showing that the collision
manifold has dimensionality ~1.66N in de-space, versus 4N in message-space.
Combined with the carry automaton width bound (C ≈ 2^{1.07N}), this gives
a complete characterization of the collision variety.

## IMPORTANT UPDATE: Negative Result for Forward Pruning

de_pruned_search.c tested at N=4 and N=8:
- N=4: 1.3x speedup (51200 vs 65536 evals)
- N=8: 1.2x speedup (3.69B vs 4.29B evals) — and SLOWER due to overhead

**Root cause**: The "valid" de sets are the IMAGE of the round function
applied to the initial state, NOT a collision-specific filter. ALL message
words (collisions and non-collisions alike) produce de values in the valid
set. The de values don't distinguish collisions from non-collisions.

**Structural meaning**: The collision variety is embedded in carry space,
not register-diff space. The e-path diff is a PROJECTION of the carry
structure that loses the collision-discriminating information.

**The 413,000x estimate was wrong** because it assumed de values are
independently distributed across the full 2^N range. In reality, the
round function maps ALL inputs into the same small image.

Evidence level: VERIFIED (exhaustive at N=4, N=8) — the de set sizes are
correct, but they DON'T help with pruning.
