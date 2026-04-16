# The Rotation-Aligned Kernel Hypothesis

## Observation (2026-04-16)

The fleet scanned N=32 for sr=61 candidate M[0] values across kernel bits
0, 6, 10, 11, 13, 17, 19 (with 20 and 25 still scanning). The candidate
counts revealed a striking pattern:

| Kernel bit | Candidates | SHA-256 rotation alignment |
|------------|------------|----------------------------|
| 0          | 4          | LSB (carry propagation)    |
| 6          | 6          | **Sigma1[0] = ROTR6**      |
| 10         | 7          | **sigma1[2] = SHR10**      |
| 11         | 2          | **Sigma1[1] = ROTR11**     |
| 13         | 6          | **Sigma0[1] = ROTR13**     |
| 17         | 3          | **sigma1[0] = ROTR17**     |
| 19         | 1          | **sigma1[1] = ROTR19**     |

Six of seven productive kernel bits align with a SHA-256 rotation constant.
The seventh (bit 0) is the LSB, which has a different mechanism (carry
propagation from the bottom of the word).

## SHA-256 Rotation Constants (FIPS 180-4)

Message-schedule rotations (used in W[r] for r≥16):
- sigma0(x) = ROTR7(x) ⊕ ROTR18(x) ⊕ SHR3(x)   → bits {7, 18, 3}
- sigma1(x) = ROTR17(x) ⊕ ROTR19(x) ⊕ SHR10(x) → bits {17, 19, 10}

Round-function rotations (used in T1, T2):
- Sigma0(x) = ROTR2(x) ⊕ ROTR13(x) ⊕ ROTR22(x) → bits {2, 13, 22}
- Sigma1(x) = ROTR6(x) ⊕ ROTR11(x) ⊕ ROTR25(x) → bits {6, 11, 25}

Union of all rotation bits: {2, 3, 6, 7, 10, 11, 13, 17, 18, 19, 22, 25}.

## Hypothesis

**A kernel bit k ∈ {0} ∪ {rotation constants of SHA-256} is productive
(i.e., produces sr=61 candidates) at full width N=32 with appropriate
fill pattern.**

This gives 13 candidate productive bits out of 32.

## Predictions (Partially Validated 2026-04-16 15:15)

- **bit 25** (Sigma1[2] = ROTR25): predicted productive → **CONFIRMED (9 candidates, new record!)**
- **bit 20** (NON-rotation): predicted zero/few → **REFUTED (3 candidates found)**

### Refined Hypothesis (Post-bit-20)

The strong version (productive = ONLY rotation constants + LSB) is FALSE.
Every tested bit has at least some candidates.

Weaker (but still useful) version:
- Rotation-aligned bits yield MORE candidates on average
- Non-rotation bits yield FEWER
- The rotation effect is about PRODUCTIVITY RATE, not existence

### Still Untested
- bit 2, 3, 7, 18, 22 (all rotation-aligned)
- Most non-rotation bits (5, 14, 27 control tests)

### The Real Test (Hypothesis 2.0)

**Does SAT solve time at N=32 correlate with rotation-alignment?**

If bit-25 (rotation) sr=61 SAT resolves faster than bit-20 (non-rotation),
that's a cleaner structural claim: rotation-alignment aids CDCL navigation
even if both have candidates.

## Why This Might Be True

The cascade DP construction forces da=0 at each round. The sr=60
boundary is broken by the message-word differential at M[0] and M[9]
propagating through the message schedule. When the differential bit
position k aligns with a SHA-256 rotation constant, the sigma0/sigma1
computation of the message schedule produces a bit-pattern that
interferes constructively with the cascade's internal accommodation
of W[60]'s schedule constraint.

In contrast, a non-rotation-aligned kernel bit produces a differential
that the schedule processes "indifferently" — with no special cancellation
— forcing the cascade to absorb the full schedule mismatch and typically
failing.

The LSB (bit 0) works differently: the carry chain from the bottom of
the word provides an additional degree of freedom that other non-aligned
bits lack.

## Implications

1. **Search efficiency**: The candidate search at N=32 can be narrowed
   from 32 bit positions to ~13 rotation-aligned positions (60% reduction).
2. **Theoretical insight**: The sr=60/61 boundary structure is tied to
   SHA-256's specific rotation constants, not to arbitrary word dynamics.
3. **Paper claim**: At full N=32, the productive kernel set is determined
   by the SHA-256 rotation constants themselves — a structural property
   of the algorithm, not a numerical coincidence.

## Test Plan

The fleet should complete scans at untested rotation bits (2, 3, 7, 18,
22, 25) to confirm each produces candidates. Also, scan at 1-2 NON-rotation
bits (e.g., bit 5, 14, 20) to confirm they produce zero or few candidates.

If the hypothesis holds, we have a structural characterization of which
kernel bits produce sr=61 at N=32, tying the collision attack surface
directly to SHA-256's rotation-constant choice.
