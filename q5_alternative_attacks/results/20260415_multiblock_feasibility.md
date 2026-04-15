# Multi-Block sr=61 Attack: Feasibility Analysis

## Observation

The sr=60 cascade DP produces many "near collisions" where only registers
a and e differ at round 63. The residual structure is highly constrained:

At N=4 (65536 inputs):
- 49 full collisions (all 8 registers match)
- 283 near-collisions (HW of residual ≤ 4)
- Most common: da=de=0x6, all others zero (128 instances, HW=4)
- Second most common: da=de=0x8, all others zero (43 instances, HW=2)
- **da = de pattern**: confirms da=de theorem (Theorem 4)

## Multi-Block Strategy

### Block 1: Run sr=60 cascade, produce near-collision
Instead of requiring a full collision (sr=63), accept a near-collision
where the state diff after round 63 is small (e.g., 1-2 active bits
in registers a and e).

### Block 2: Cancel the residual
Block 1's output becomes block 2's IV. The two messages have:
  IV_1 = state63_path1 (from block 1)
  IV_2 = state63_path2 (from block 1)
  IV_diff = residual (small: da=de=few bits)

Block 2 must find M such that SHA256(IV_1, M) = SHA256(IV_2, M).
This is a "related-IV collision" — full 64 rounds, but with:
- 16 message words of freedom (not just 4-5)
- A SMALL IV difference (2 active register bits, not arbitrary)
- No cascade construction needed (standard differential attack)

### Why This Could Work

Wang-style differential attacks on SHA-256 handle much larger differentials
(~15 active bits across multiple registers) through careful message
modification. Our residual is much smaller:
- Only 2 registers differ (a and e)
- Only 1-2 active bits per register
- The shift register will spread the differential, but slowly

### Why This Might Not Work

- Block 2 is 64 FULL rounds (not reduced-round)
- No practical collision attacks exist on full SHA-256
- Wang-style modifications are tuned for specific differential trails
- The "small residual" advantage may be insufficient for 64 rounds

### What Would Make It Work

If we could find a near-collision at sr=60 with residual HW ≤ 1
(a single bit difference in one register), block 2 would start with
a 1-bit IV difference. This is the best possible starting point for
a differential attack on full SHA-256.

At N=4: no single-bit residuals observed (minimum HW=2).
At larger N: the residual distribution needs to be characterized.

## Next Steps

1. Characterize residual HW distribution at N=8, N=10, N=12
2. If single-bit residuals exist, they define the multi-block differential trail
3. The trail analysis for block 2 is a separate research problem (Wang-style)

Evidence level: HYPOTHESIS (analysis at N=4 only)
