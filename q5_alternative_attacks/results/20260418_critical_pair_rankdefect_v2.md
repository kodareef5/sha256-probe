# Critical Pair Rank-Defect Predictor v2: Linear Bridge Too Coarse

**Date**: 2026-04-18
**Evidence level**: VERIFIED (N=8, 260 collisions)

## Method

For each collision, built the linearized GF(2) schedule bridge:
  sigma1 matrix H (N×N over GF(2)), schedule constant c
  Reduced system (removing pair rows i,j): H_red * W58 = target_red
  
Checked rank(H_red) == rank(augmented(H_red, target_red)) for consistency.

## Result

ALL 28 pairs score 260/260 (100% compatible).

The sigma1 matrix at N=8 has rank 7 (not 8). Removing ANY 2 rows from
a rank-7 system always leaves a consistent system. The linear schedule
bridge CANNOT distinguish between critical and non-critical pairs.

## Interpretation

The critical pair selection happens at the NONLINEAR level:
- The sigma1 bridge is necessary but not sufficient
- The cascade's carry propagation (MAJ/Ch) determines which pairs
  actually produce satisfiable sr=61 instances
- Same pattern as all other results: linear analysis is too coarse

## Implication

To predict critical pairs without SAT, we need to account for:
1. The nonlinear carry propagation through the round function
2. The cascade offset's dependency on intermediate state values
3. The full 7-round evaluation (not just the sigma1 map)

This is equivalent to the BDD quotient problem: the critical pair
structure is visible in the compiled function, not in the linear shell.
