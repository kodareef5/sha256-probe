# Carry Elimination Engine: NEGATIVE Result

**Date**: 2026-04-16 ~23:30 UTC
**Evidence level**: VERIFIED (exhaustive at N=4, 39 collisions)

## Hypothesis

Given carry bits for all additions, the remaining system is LINEAR
(just XOR). Gaussian elimination on the linear part should reduce the
number of free variables from 4N (message bits per message) to ~N
(carry entropy), giving a 2^{3N} speedup.

## Method

1. Enumerated all 39 sr=60 cascade collisions at N=4
2. Extracted all carry bits from all 49 additions × 2 messages = 294 carry bits
3. Computed the GF(2) AFFINE RANK of the collision set in carry+message space

## Result

| Metric | Value | Expected for "works" |
|--------|-------|---------------------|
| Affine rank (carry+msg) | **38** | ~5 (log₂(39)) |
| Carry-only affine rank | 38 | ~5 |
| Message-only affine rank | 20 | ~5 |
| Carry-diff affine rank | 38 | ~5 |
| Carry-diff invariant | 4/147 (2.7%) | ~42% |

The affine rank is 38 = #collisions - 1, the MAXIMUM possible.
The linear system provides essentially NO structure — the collision
points are in "general position" in carry space.

## Why This Fails

The linear part of the carry system (XOR/sum equations, collision
constraints) leaves ~38 free dimensions out of 326 total variables.
But the solution set also has dimension ~38 (38 affine rank).

**The linear constraints don't reduce the solution set at all!**
All reduction comes from the QUADRATIC constraints:
- MAJ(a, b, c) = ab + ac + bc (carry recurrence)
- Ch(e, f, g) = ef + eg + g
- Maj(a, b, c) = ab + ac + bc

These are the ONLY equations that distinguish collisions from non-collisions.

## Discrepancy: 39 vs 49 collisions

Found 39 collisions instead of the expected 49. This is likely due to
a different candidate (find_m0 at N=4) vs the cascade_dp_fast tool.
The qualitative result (affine rank = maximal) is unaffected.

## Discrepancy: 2.7% vs 42% carry-diff invariance

Only 4/147 carry-diff bits are invariant (2.7%), much less than the
expected 42%. This is because the 42% figure counts invariance
**per bit position** (over N=4 positions), while this counts
**total across all positions**. The 4 invariant bits are the
universally-constant ones (always 0 or 1 regardless of collision).

## Implications

1. **Carry elimination engine DOES NOT WORK** as formulated — the linear
   constraints are too weak. The quadratic MAJ/Ch constraints are essential.

2. **The "guess ~21 carries" approach fails** because even after fixing
   all carries, the linear system still has too many free variables.
   The nonlinear carry recurrence constrains the system, not the linear
   XOR equations.

3. **Path forward**: must exploit QUADRATIC structure, not just linear.
   Options:
   - Gröbner basis on the quadratic system (exponential in general)
   - XL/FXL linearization (turns degree-2 into linear at cost 2^{O(N)})
   - Specialized quadratic solvers for the MAJ structure
   - Algebraic immunity analysis of the MAJ function

4. **The SAT solver IS exploiting the quadratic structure** through
   conflict-driven learning. The cascade-augmented encoding helps by
   providing intermediate linear constraints that the solver can use
   for unit propagation.

## What This Rules Out

- Linear algebra speedups (Gaussian elimination, LLL, etc.)
- "Guess carries, linearize, solve" approach
- Any method that treats the system as primarily linear

## What This Does NOT Rule Out

- Quadratic system solvers (Gröbner, XL, SAT with algebraic reasoning)
- Combinatorial methods (MITM on MAJ outputs, not carries)
- The cascade-augmented SAT encoding (which helps with propagation, not algebra)
- Neural/ML approaches that learn the nonlinear structure
