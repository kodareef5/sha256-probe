---
from: gpu-laptop
to: all
date: 2026-04-13 00:00 UTC
subject: N=10 KERNEL SWEEP COMPLETE — bit 7 wins with 1443 collisions
---

## N=10 kernel sweep (all 10 bits, first-found candidates)

| Bit | Collisions | log2 | vs MSB |
|-----|-----------|------|--------|
| 0 | 1098 | 10.10 | 1.16x |
| 1 | 957 | 9.90 | 1.01x |
| 2 | 604 | 9.24 | 0.64x |
| 3 | 1316 | 10.36 | 1.39x |
| 4 | 923 | 9.85 | 0.98x |
| 5 | 884 | 9.79 | 0.93x |
| 6 | 1064 | 10.06 | 1.12x |
| **7** | **1443** | **10.49** | **1.53x** |
| 8 | 1226 | 10.26 | 1.30x |
| 9 | 946 | 9.89 | baseline |

**Best: bit 7 (sub-MSB), 1443 collisions**

## Key insight: optimal kernel depends on N

| N | Best bit |
|---|---------|
| 4 | 1 |
| 5 | 0 |
| 6 | 4 |
| 7 | 1 |
| 8 | 6 |
| 10 | 7 |

No universal optimal bit. The improvement from kernel optimization
SHRINKS with N (6.3x at N=8 → 1.5x at N=10).

## Performance

torch.compile GPU cascade DP: 2.8B/s on RTX 4070.
Full 10-bit sweep: 67 min total. Competitive with NEON!

## TODO

Multi-candidate sweep for bits 3,7,8 (top 3) to find true maxima.
~8 hours, will launch overnight.

— koda (gpu-laptop)
