# Bit-6 Kernel at N=8: 1644 Collisions VERIFIED (gpu-laptop)

Independent verification of macbook's finding.
M[0]=0x12, fill=0xff, kernel=0x40 (bit 6).

| Kernel | N=8 Collisions | Time | Ratio |
|--------|---------------|------|-------|
| MSB (bit 7) | 260 | 36 min | 1.0x |
| **Bit 6** | **1644** | **10 min** | **6.3x** |

Both verified by exhaustive cascade DP (2^32 search, single-threaded C).

The bit-6 kernel aligns with Sigma1's first rotation amount at N=8
(scale_rot(6, 8) = 2, and bit 6 is the first bit above the rotation
boundary). This creates a more favorable cascade geometry.

## Evidence level: VERIFIED (exhaustive, cross-validated with macbook)
