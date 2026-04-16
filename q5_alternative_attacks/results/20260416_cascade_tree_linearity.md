# Cascade Collision Tree Linearity

**Date**: 2026-04-16  
**Status**: VERIFIED at N=8 (260 collisions fully enumerated)

## Finding

The cascade collision set at N=8 has a near-linear tree structure
in the forward-search tree (W57 → W58 → W59 → W60):

| Step | Branching |
|------|-----------|
| Step 1: Select W57 | 152 / 256 values productive (59.4%) |
| Step 2: Given W57, select W58 | avg **1.64** productive W58 per W57 |
| Step 3: Given (W57,W58), select W59 | **~1.00** (250 pairs, 251 triples) |
| Step 4: Given (W57,W58,W59), select W60 | **~1.04** (242 of 251 triples give 1 W60) |

Effective search space: 152 × 1.64 × 1 × 1.04 ≈ **260** (= total collisions).

## Interpretation

The collision "tree" in the cascade search space is essentially LINEAR
after the initial W57 choice. Once you pick a productive W57, the
remaining words are almost uniquely determined.

This matches the **carry entropy theorem**: log2(260) = 8.02 bits = N bits
of effective information. The cascade compresses 4N = 32 bits of free
choice into N bits of effective degree of freedom.

## Relation to Prior Theory

- **Rotation Frontier Theorem**: Forward-pass intermediate pruning fails.
  TRUE — we cannot ELIMINATE branches during the search.
- **Cascade Tree Linearity** (this): The TRUE collision tree has
  branching factor ~1. Most branches we explore in a naive search
  are just wasted.

These are NOT contradictory:
- Rotation Frontier is an algorithmic constraint (no local pruning).
- Cascade Tree Linearity is a structural property of the collision set.

The gap between them is the challenge: we know the collision set is
"thin" (carry entropy = N bits), but we cannot discover this thinness
through forward search alone.

## Algorithmic Consequence (Conjectural)

If we could find a FUNCTION f(W57) → (W58, W59, W60) such that
- f produces the collision (W57, W58, W59, W60) for productive W57
- f returns "no-collision" for non-productive W57

Then collision search becomes O(2^N) instead of O(2^{4N}).

**The function f is well-defined** (up to the ~4% multi-branches).
**The function f is NOT algebraically simple** (from the ANF analysis
of W1[59]: degree 7/8 at N=8).

Potential approaches to learn f:
1. **Supervised learning**: train a model on (W57 → W58,W59,W60)
   pairs at N=8, test generalization
2. **BDD-based**: compile the collision set into a BDD, extract
   f as a circuit
3. **Symbolic pattern analysis**: find algebraic structure in
   the f map (bitwise, modular, permutation-based)

## Next Steps

- [ ] Confirm N=10 cascade tree structure (cascade_dp running, ~100 min)
- [ ] Check branching factors per step at N=10
- [ ] Attempt a simple f(W57) prediction (e.g., linear approximation)
- [ ] BDD compilation of the (W57 → W58) map at N=8

## Why This Matters for N=32

If the tree-linearity holds at N=32:
- 2^32 W57 values → ~60% productive = 2.5B
- Each productive W57 → ~1-2 continuations
- Total collision count ≈ 2^32 = 4.3B

This is more than the fleet has ever seen at N=32 (currently 0 verified
sr=60 collisions beyond the principal M[0]=0x17149975). If the tree is
truly linear, collision DENSITY at N=32 is ~1 per 2 productive W57.

Our current SAT-based search is finding "a" collision per candidate.
If the tree is linear, each candidate should have ~2^N collisions,
not just 1. Why does SAT find "one" and no more?

Possibly: the SAT encoding does not exploit tree structure. It enumerates
a "random" path through the solution space and stops at the first found.
A tree-aware search might enumerate all 2^N collisions in O(2^N) time.

## Open Question

**Can we find a polynomial-time cascade collision finder by learning
the f(W57) map at small N and extrapolating to N=32?**

At N=8, f maps 152 values of W57 to (W58, W59, W60) triples.
Total data size: 260 × 32 bits = 8 KB. Very small training set.
If f has structure, it might be learnable.
