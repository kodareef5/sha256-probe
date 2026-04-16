# W1[59] Cardinality Reduction: A Universal Cascade Constraint

**Date**: 2026-04-16  
**Status**: VERIFIED at N=4, 6, 8

## Finding

Across the tested word widths N=4, 6, 8, the cascade collision set
exhibits a consistent structural constraint: **W1[59] takes only
~16-27% of its possible values**, dramatically more constrained
than any other free word (W1[57], W1[58], W1[60]).

| N | #colls | W1[57] | W1[58] | W1[59] (constrained) | W1[60] |
|---|--------|--------|--------|----------------------|--------|
| 4 | 49     | 16/16 (100%) | 16/16 (100%) | **4/16 (25.0%)** | 16/16 (100%) |
| 6 | 50     | 26/64 (40.6%) | 35/64 (54.7%) | **17/64 (26.6%)** | 31/64 (48.4%) |
| 8 | 260    | 152/256 (59.4%) | 162/256 (63.3%) | **42/256 (16.4%)** | 162/256 (63.3%) |

The cardinality fraction: 25.0% → 26.6% → 16.4% (at N=4, 6, 8).
Pattern: W1[59] has ~1-4× fewer allowed values than its siblings.

## Algebraic Degree

Despite the low cardinality, the ALGEBRAIC DESCRIPTION of the W1[59]
allowed set is near-maximal degree in all cases:

| N | W1[59] indicator ANF | Max degree | # terms |
|---|---------------------|------------|---------|
| 4 | full 4/4 degree | 4 | ~15 |
| 6 | full 6/6 degree | 6 | 35 |
| 8 | degree 7/8 | 7 | 114 |

This means the constraint "W1[59] is a valid cascade collision value" 
is NOT algebraically simple — no low-degree polynomial equation
captures it. The constraint arises from high-degree carry propagation
through the cascade rounds.

## Interpretation

W1[59] is the last FREE message word before the schedule-determined
W[60]. At round 59, the cascade's DP construction is complete and
W1[59] carries the "accumulated differential" needed for the final
differential cancellation at round 60.

The cascade offset W2[59] = W1[59] + cascade_offset_59 must produce
specific diff patterns for da=db=dc=dd=de=0 at round 60. Only certain
W1[59] values survive this constraint.

This is a STRUCTURAL property of the cascade construction itself,
not of any specific M[0] candidate.

## Why This Matters

1. **Search space reduction**: At N=8, knowing the 42-set a priori
   reduces inner-loop work by ~6x (256→42). Useful if we can
   COMPUTE the set without first enumerating all 260 collisions.

2. **BDD/ZDD efficiency**: The 42-set has no low-degree ANF, but it
   MAY have a compact BDD representation. BDD nodes describe the
   set as a Boolean function; if the set has structural simplicity
   different from algebraic simplicity, a BDD captures it.

3. **Scales to N=32?** If the cardinality ratio holds at ~20%, then
   at N=32, W1[59] takes ~0.8B of 4.3B values. Still huge.
   But: this means the 2^32 inner search space has effective size
   ~2^{29.7}, a 5x reduction per W1[59] iteration. Not huge but
   cumulative savings across all search dimensions could matter.

4. **Theoretical insight**: The cascade has ONE "bottleneck" word
   (W1[59]) that carries most of the structural constraint. This
   suggests the cascade mechanism is a *bottleneck encoder* — it
   compresses differential accumulation into a single word, which
   then must be in a specific restricted set.

## Open Questions

- Does the cardinality ratio continue to decrease with N? (Test at N=10, 12)
- What is the BDD size of the W1[59] indicator function vs random?
- Is the 42-set at N=8 closed under any group action? (e.g., cyclic rotation?)
- Do other kernel bits (not MSB) produce different W1[59] sets?

## Next Steps

- [ ] Test at N=10, N=12 to check if cardinality trend continues
- [ ] Compute BDD size of W1[59] indicator at N=8
- [ ] Test across kernels: does bit-1, bit-6 etc. give different W1[59] sets?
- [ ] Test if 42-set at N=8 has orbital structure under bit-shift / rotation

## Evidence Level

VERIFIED at N=4, 6, 8 with exhaustive cascade DP enumeration.
Analysis: 260 collisions at N=8 generated in 108s.
