# Collision Function Near-Linearity: 90% Affine at N=4

## Finding

For fixed (W57, W58), the collision function over (W59, W60) is
**affine over GF(2)** in 90% of cases at N=4.

## Data

Per-slice collision count distribution (N=4, 256 total (W57,W58) slices):
- #coll=1: 14 slices (power of 2 → consistent with affine)
- #coll=2: 13 slices (power of 2 → consistent with affine)
- #coll=3: 3 slices (NOT power of 2 → nonlinear)
- Total with collisions: 30/256 (11.7%)
- **Power-of-2 fraction: 27/30 = 90%**

## Why This Matters

An affine function over GF(2)^{2N} can be solved in O(N^3) by Gaussian
elimination. If 90% of slices are affine, the collision-finding algorithm is:

1. Enumerate (W57, W58) concretely: 2^{2N} outer loop
2. For each slice: solve the GF(2) linear system for (W59, W60): O(N^3)
3. Total: O(2^{2N} × N^3) — **quadratic-root speedup** over 2^{4N} brute force

At N=8: O(2^{16} × 512) ≈ 33M ops vs 2^{32} ≈ 4.3B → **130x speedup**

## Root Cause

The collision condition at rounds 61-63:
- dT1_61 = dh60 + dSigma1(e60) + dCh(e60,f60,g60) + dW61 = 0
- Since de60=0: dSigma1=0, and dCh is LINEAR in (df60, dg60) when e60 is fixed
- df60 = de59 (shift), dg60 = de58 (shift) → depends on W59 through cascade
- The Ch function is a multiplexer: Ch(e,f,g) = e ? f : g → LINEAR when e is known

The additions (h+Sig1, +Ch, +K, +W, d+T1, T1+T2) introduce carry nonlinearity.
In 90% of cases, the carry chain doesn't create enough nonlinearity to break affinity.

## Implication for Polynomial-Time

If the 90% affine rate holds at larger N, the collision finder would be:
- O(2^{2N} × N^3) for 90% of slices (GF(2) elimination)  
- O(2^{2N+2N}) = O(2^{4N}) for 10% of slices (brute force within slice)
- Total: dominated by the 10% nonlinear slices → still O(2^{4N})

A true polynomial algorithm requires handling the nonlinear slices too.
This could come from higher-order GF(2) decomposition or carry-conditioned
linearization (guess ~2 carries per nonlinear addition).

## GF(2) Linearization Test: FAILS

Tested: compute Jacobian J from 2N+1 evaluations, solve Jx = f0 over GF(2).
Result: the linear model finds 0 collisions. All 30 collision-bearing slices
give wrong solutions (the Jacobian doesn't capture the nonlinear carry effects).

The power-of-2 collision counts are a property of the algebraic VARIETY
(solution set structure), NOT evidence that the function is affine.
Modular additions introduce carry nonlinearity that breaks GF(2) linearity.

Match rate: 226/256 = 88% (but only for ZERO-collision slices, which is trivial).

## Revised Conclusion

The collision function is **NOT affine** in (W59, W60), despite having
power-of-2 collision counts in 90% of slices. The O(2^{2N} × N^3) speedup
does NOT work. Carry nonlinearity is fundamental.

The carry-guess approach (guess k carries, linearize, solve) requires
guessing too many carries (~28-56 per round) to be practical.

Evidence level: VERIFIED (N=4 exhaustive + GF(2) linearization test)
