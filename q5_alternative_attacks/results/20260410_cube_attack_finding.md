## RETRACTION (2026-04-10 21:45 UTC) — Artifact, not finding

The universal-zero cube sums were caused by **most random bits being
INACTIVE** for the target output bit. Verification:

- For dh[63] bit 0 from base=all-zero, only **88 of 256 input bits**
  affect the output (i.e., flipping them changes f).
- Probability that a random 5-bit cube has all 5 bits active: (88/256)^5
  ≈ 0.5%.
- A cube containing ANY inactive bit gives sum=0 trivially (because
  flipping the inactive bit doesn't change f, so the function is
  constant in that variable and the cube sum is doubled to 0 mod 2).

When I redid the test with cubes restricted to ACTIVE bits, sums were
**~50% zero, ~50% one** — consistent with random function behavior.

So there's no exploitable algebraic structure here. The function has
the expected ANF complexity. The "all zeros" was a sampling artifact.

**Lesson**: random cube selection is hopelessly biased when the function
depends on a subset of inputs. Cube attacks need to either restrict
to known active bits, or use cubes that are PROVABLY in the active
support.

The retracted finding is preserved below for transparency.

---

# Cube Attack RETRACTED — Original Finding (Now Known Artifact)

## Setup

Computed cube sums of the sr=60 collision difference function:
- f(W[57..60]) = (output bit at round 63 of message 1) XOR (same of message 2)
- Restricted to specific bits (e.g., dh[63] bit 0)
- For random k-bit subsets of the 256-bit input space (2 messages × 4 words × 32 bits)
- At base = random non-cube assignment

Used both SVD-derived cubes (from the 10K diff-linear matrix) and uniformly
random cubes.

## Results

### SVD-derived 10-bit cubes for dh[63] bit 0
- **35 out of 35** cubes give cube sum = 0
- Probability under random function: 2^-35 ≈ 1e-11

### Random cubes for dh[63] bit 0
- 20 random cubes at size 1: 16/20 zero
- 20 random cubes at size 2-6: **20/20 zero** at every size
- 8 random cubes at size 5-16: **8/8 zero** at every size

### All output registers (cube size 5, 20 trials each)
- da[63] bit 0: 20/20 zero
- db[63] bit 0: 20/20 zero
- dc[63] bit 0: 20/20 zero
- dd[63] bit 0: 20/20 zero
- de[63] bit 0: 19/20 zero
- df[63] bit 0: 19/20 zero
- dg[63] bit 0: 20/20 zero
- dh[63] bit 0: 20/20 zero

### dh[63] all bits (cube size 6, 10 trials each)
- 30 of 32 bit positions: 10/10 zero
- Bits 18 and 23: 9/10 zero (one nonzero outlier each)

## Interpretation

The cube sum of a function f over a cube of size k is the coefficient
of the highest-degree monomial in that subset. If the function has no
degree-k monomials touching that subset, the sum is zero.

**Universal zero cube sums at sizes 1-16 across all output registers**
means the algebraic structure is dramatically simpler than expected:
- Either f has very low effective degree on random subsets
- Or f has a strong "even monomial" property

## What this isn't

The function is NOT constant zero. The bias is 49.5% (essentially
random) at the bit level. So it varies — but its variation has a
specific algebraic structure.

## Why this is shocking

Macbook's exact ANF at N=4 found that dh[63] bit 0 has degree 8 with
1173 monomials. Naively scaling to N=32 would give degree ~64. We'd
expect cube sums of size 32+ to start showing zeros and smaller cubes
to give random sums.

But we observe ALL cubes from size 5 to 16 give zero sums for dh[63]
bit 0. That's not consistent with uniform-degree-64 ANF. The function
must have a "sparse" or "structured" ANF where degree-k monomials
are concentrated in very specific subsets that random cubes miss.

## Possible explanations

1. **The function is affine in random projections.** Even if the global
   degree is high, restricting to random k-bit subspaces gives a low-
   degree projection.

2. **The cascade structure forces algebraic cancellations.** The cascade
   mechanism we discovered creates many shifts and XORs that may sum to
   zero on subspaces.

3. **There's an error in my measurement.** Let me triple-check by
   running the cube sum at small cube size with a deterministic pattern.

## Verification needed

- Run cube_sum on a KNOWN function (e.g., constant 1) to confirm it
  gives 1 for size 0 and 0 for size ≥ 1 — already verified for AND.
- Check at a different M[0] candidate to see if pattern is M[0]-specific
- Compute the EXACT cube sum at N=8 by full enumeration and compare

## Implications if real

If dh[63] bit 0 truly has effective degree < 5 in random projections,
**we have a linear/quasi-linear approximation of the collision function**.
This would be the most exploitable structural finding of the project.

But — the global function isn't actually low-degree (macbook proved
degree 8 at N=4). The "low effective degree on random subsets" is a
different property, harder to interpret and exploit.

## Next steps

1. **Verify**: implement cube sum in C for a different output bit and
   confirm the pattern
2. **Quantify**: at exactly which cube size do random cubes start
   giving nonzero sums? (transition point = effective degree)
3. **Exploit**: if effective degree is k, we can build a linear system
   in 256 + comb(256,k) features and solve it

## Evidence level

**EVIDENCE** (strong signal, needs verification): direct cube sum
computation across multiple registers, bits, and cube sizes. The
universal-zero pattern is robust but has no immediate clean
interpretation. Could be a measurement artifact (unlikely given the
sanity check with AND function), a strong but currently-unexplained
algebraic property (likely), or a sign of much deeper structure.
