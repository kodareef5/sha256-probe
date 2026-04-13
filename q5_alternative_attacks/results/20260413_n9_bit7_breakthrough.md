# N=9 Bit-7 Kernel: 4905 COLLISIONS

Date: 2026-04-13 00:50 UTC

## Result

| Bit | Fill | M[0] | Collisions | log2 |
|-----|------|------|-----------|------|
| 7 | 0x100 | 0x14f | **4905** | **12.26** |

## Context

This is 24x more than the previous best at N=9 (bit 4 = 204) and
3x more than the N=8 champion (bit 6 = 1644)!

| Bit | Status | Collisions |
|-----|--------|-----------|
| 0 | tested | 0 |
| 1 | tested | 0 |
| 2 | tested | 0 |
| 3 | tested | 0 |
| 4 | tested | **204** |
| 5 | tested | 0 |
| 6 | tested | 0 |
| **7** | **FOUND** | **4905** |
| 8 (MSB) | pending | (expected 0) |

## Significance

1. N=9 is NOT a collision desert — collisions concentrate at bit 7
2. log2(4905) = 12.26 is ABOVE the trend line for MSB kernel
3. The "odd-N zero" phenomenon is kernel-specific, not fundamental
4. Bit 7 = N-2 position — the sub-MSB is the magic position at N=9

## Updated Best-Kernel Scaling

| N | Best bit | Best coll | log2 |
|---|---------|----------|------|
| 4 | 1 | 146 | 7.19 |
| 6 | 4 | 83 | 6.37 |
| 8 | 6 | 1644 | 10.68 |
| **9** | **7** | **4905** | **12.26** |
| 10 | 7* | 1443* | 10.49 |

*N=10 is first-found only, multi-candidate may be much higher

Evidence level: VERIFIED (exhaustive cascade DP, NEON)
