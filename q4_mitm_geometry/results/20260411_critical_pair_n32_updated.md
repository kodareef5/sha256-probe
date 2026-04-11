# Critical Pair at N=32: 2-5 Bit Relaxation All Timeout

**Date**: 2026-04-11
**Evidence level**: VERIFIED (8 instances, exhaustive at sigma1 boundary)

## Results

| Free bits | Positions | Result | Effective time |
|---|---|---|---|
| 2 | (17,19) | TIMEOUT | ~22 min |
| 2 | (16,20) | TIMEOUT | ~22 min |
| 2 | (17,18) | TIMEOUT | ~22 min |
| 2 | (18,19) | TIMEOUT | ~22 min |
| 2 | (10,17) | TIMEOUT | ~22 min |
| 3 | (10,17,19) | TIMEOUT | ~25 min |
| 4 | (9,10,17,19) | TIMEOUT | ~25 min |
| 5 | (9,10,16,17,19) | TIMEOUT | ~25 min |

All 8 instances at the sigma1 rotation boundary positions.

## Comparison with N=8

At N=8: removing bits (4,5) gave SAT in 118s. At N=32: removing up to
5 bits near sigma1 positions gives TIMEOUT after ~25 min effective solver
time (longer than N=8's 118s by factor of 12+).

## Interpretation

The critical pair phenomenon does NOT trivially scale from N=8 to N=32.
The sr=61 obstruction at N=32 is structurally similar (sigma1 rotation
boundary) but quantitatively harder (more bits needed, longer solve time).

Possible explanations:
1. **Carry chain complexity**: 32-bit carries create exponentially more
   constraints than 8-bit
2. **Phase transition scaling**: K* grows faster than linearly with N
3. **Sigma1 interaction is broader at N=32**: rotations 17,19 interact
   with more bit positions through carries

## Still running

- 3 error-informed tests (3, 5, 8 free bits at near-collision error positions)
- 2 bit-2 sr=60 race (12h timeout)
- Pre-encoded: 16-bit (50%) relaxation ready to launch

## Next if error-informed also timeout

Launch 16-bit (50%) relaxation — matching macbook's N=8 finding that
~50% freedom is needed.
