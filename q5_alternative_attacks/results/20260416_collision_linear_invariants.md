# Linear Invariants of the Cascade Collision Set

**Date**: 2026-04-16  
**Status**: VERIFIED at N=4, testing at N=8

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

## Test Plan

- [x] Verify at N=4: 2 invariants out of 16 (12.5% fixed)
- [ ] Verify at N=8: expect ~4 invariants out of 32 (if structure scales)
- [ ] Test at N=12 if time permits
- [ ] Characterize which bits are always fixed vs which are free
- [ ] Compare invariants across kernel bits

## Why This Matters

The user's prompt asks for "cross-register correlations" and
"higher-order differentials". This is a cleaner variant: **linear
invariants across the collision set**. It's observable, verifiable,
and gives concrete structural understanding of the cascade.

If invariants scale linearly with N (O(N) fixed bits), we have
non-trivial structural pruning for all N.

If invariants scale poly-logarithmically or stay constant, they're
an anecdotal N=4 property with no algorithmic impact.
