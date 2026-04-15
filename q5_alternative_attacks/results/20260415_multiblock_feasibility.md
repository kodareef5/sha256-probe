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

## N=8 Residual Distribution (100K random samples)

Minimum residual HW observed: 7 (out of 64 total register bits).
Distribution peaks at HW=24, roughly bell-shaped.

| HW | Count | Fraction |
|----|-------|----------|
| 7 | 2 | 0.002% |
| 9 | 6 | 0.006% |
| 10 | 21 | 0.02% |
| 15 | 786 | 0.79% |
| 20 | 6065 | 6.1% |
| 24 | 9846 | 9.8% (peak) |

The minimum HW=7 means block 2 would need to cancel a 7-bit differential —
much harder than the 2-4 bits at N=4. At N=32, the residual would have
HW ~90-100 (out of 256 bits) — impractical for Wang-style attacks.

## Conclusion

The multi-block approach is UNLIKELY to work at practical N:
- Residual HW scales roughly as 3N (proportional to state size)
- Block 2 requires a Wang-style differential attack on full 64 rounds
- No practical attacks exist on full SHA-256 even with small differentials
- The structural advantage from block 1 is insufficient

Evidence level: EVIDENCE (analysis at N=4 exhaustive, N=8 sampled)
