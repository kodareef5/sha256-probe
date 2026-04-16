# Linear Invariants of the Cascade Collision Set

**Date**: 2026-04-16  
**Status**: VERIFIED at N=4. **At N=8: no linear invariants** — structure is nonlinear.

## Finding at N=4

The 49 cascade collisions at N=4 (MSB kernel, fill=0xF) form a subset
of a 14-dimensional affine subspace of the 16-dimensional W1[57..60]
space. Two linear invariants hold across ALL 49 collisions:

| Invariant | Value |
|-----------|-------|
| W1[59].b3 (MSB) | **1** |
| W1[59].b2 | **0** |

Thus W1[59] ∈ {0x8, 0x9, 0xa, 0xb} for every collision. The top 2 bits
of W1[59] are structurally determined by the cascade.

## Method

1. Enumerated all 49 collisions via `cascade_dp_fast` at N=4.
2. Formed 49×16 binary matrix M where row i = W1[57..60] for collision i
   (4 bits per word × 4 words = 16 bits).
3. Computed the null space of the span of {M[i] - M[0] : i=1..48} over GF(2).
4. Null space has dimension 2, giving 2 linear invariants across all collisions.

## Ranks

- Linear rank (from origin): **15/16** (1 bit of through-origin constraint)
- Affine rank (from collision 0): **14/16** (2 bits of affine constraint)
- Per-word linear ranks:
  - W1[57]: 4/4 (fully spanned)
  - W1[58]: 4/4 (fully spanned)
  - W1[59]: **3/4** (only 8 of 16 values appear)
  - W1[60]: 4/4 (fully spanned)

## Interpretation

The cascade mechanism structurally constrains specific bits of W1[59].
Why W1[59] and not other words? Hypothesis: the cascade offsets propagate
differential bits through the shift register, and W[59] is the last
"free" word BEFORE the schedule-determined W[60]. At N=4 with MSB kernel,
the MSB bit must propagate into W[59] to zero out the register difference
at round 59, which forces MSB of W1[59] = 1.

The second invariant (W1[59].b2 = 0) is more subtle — suggests bit 2
participates in a carry-chain constraint that locks its value.

## Computational Consequence

Search space reduction: from 2^16 = 65536 candidates to
- 2^4 × 2^4 × 2^2 × 2^4 = 2^14 = 16384 candidates.

The cascade DP already enumerates efficiently, but this analysis shows
the **space of cascade collisions itself has structure** — not just
the candidate M[0] values.

## If Invariants Generalize to N=32

If similar structural constraints hold at full SHA-256:
- O(1) free bits in W1[59] could become O(N/2) or O(log N)
- Combined with cascade DP (2^4N), search space could shrink further

## N=8 Extension (260 collisions)

Ran the same analysis at N=8 with 260 collisions:

- Affine rank: **32/32 (no linear invariants)**
- Linear rank: **32/32 (no through-origin invariants)**
- Per-word linear ranks: all 8/8 (each word individually spans fully)

BUT:
- W1[59] takes only **42 of 256 possible values** (16.4% cardinality)
- Distribution of W1[59] values is bit-balanced (no constant bits)
- Hamming weight distribution biased toward hw ∈ {2,3,4,5}

## Revised Interpretation

The N=4 linear invariants (W1[59].b2=0, b3=1) are an **artifact of
N=4's scaled rotations and small word size**, NOT a fundamental
property of the cascade.

At N=8 the cascade constraint is **nonlinear**: the collision set
is a subvariety of W1 space that is NOT a linear subspace. The
42 allowed values of W1[59] form a structured but nonlinear set.

This means:
1. Linear invariants are NOT a useful algebraic tool for pruning at N ≥ 8
2. The collision set IS a structured subset, but the structure is
   nonlinear (higher degree ANF)
3. BDD / ZDD compilation of the collision set may be more productive
   than GF(2) rank analysis

## Why This Matters

The user's prompt asks for "cross-register correlations" and
"higher-order differentials". Linear invariants were a natural
first thing to check. The negative result at N=8 informs:

1. **Don't rely on linear structure at N ≥ 8.** Cross-register
   correlations at N=8 (already tested, negative) and this linear
   invariant analysis (now tested, negative at N=8) both point
   to the collision set being essentially "nonlinear" in the
   free-message coordinates.

2. **The W1[59] cardinality reduction (42/256) is real structure.**
   Some values of W1[59] simply never appear in collisions. If we
   could characterize this set a priori (without enumerating all
   collisions), we'd get a 6x pruning. But characterizing a
   nonlinear 42-subset of 256 requires a more sophisticated
   description — possibly a small Boolean circuit or low-order ANF.

3. **The paper story for N=4 invariants**: mention as a pedagogical
   example, caveated by the N=8 result showing it doesn't generalize.

## Test Plan

- [x] Verify at N=4: 2 invariants out of 16 (12.5% fixed)
- [x] Verify at N=8: 0 linear invariants (32/32 rank)
- [x] W1[59] cardinality at N=8: 42/256 (nonlinear structure)
- [ ] Characterize the 42 allowed W1[59] values at N=8 (ANF, circuit)
- [ ] Extend to other kernel bits at N=8 — is the cardinality bias
      kernel-specific or universal?
