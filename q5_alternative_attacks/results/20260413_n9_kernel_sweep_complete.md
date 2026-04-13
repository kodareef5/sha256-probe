# N=9 Kernel Sweep — COMPLETE

Date: 2026-04-13 01:00 UTC
Tool: kernel_sweep_neon.c (1 thread, 180 min total)

## Results

| Bit | Fill | M[0] | Collisions |
|-----|------|------|-----------|
| 0 | — | — | 0 |
| 1 | — | — | 0 |
| 2 | — | — | 0 |
| 3 | — | — | 0 |
| 4 | 0x00 | 0x136 | 204 |
| 5 | — | — | 0 |
| 6 | — | — | 0 |
| **7** | **0x100** | **0x14f** | **4905** |
| 8 (MSB) | — | — | 0 |

## Key Finding

N=9 collisions concentrate EXTREMELY at bit 7 (N-2 position).
4905 collisions at bit 7 vs 204 at bit 4, ALL others = 0.

This is the highest collision count at ANY odd N:
- N=5: best 37 (bit 0)
- N=7: best 373 (bit 1)
- N=9: best **4905** (bit 7) — 13x more than N=7

## Scaling Implication

log2(4905) = 12.26, which is ABOVE the even-N trend line.
If the best-kernel scaling uses this point:

| N | Best bit | Best coll | log2 |
|---|---------|----------|------|
| 4 | 1 | 146 | 7.19 |
| 5 | 0 | 37 | 5.21 |
| 6 | 4 | 83 | 6.37 |
| 7 | 1 | 373 | 8.54 |
| 8 | 6 | 1644 | 10.68 |
| **9** | **7** | **4905** | **12.26** |
| 10 | 7* | 1443* | 10.49 |

*first-found only

The N=9 point EXCEEDS N=10 first-found! This strongly suggests
multi-candidate testing at N=10 will reveal much higher counts.

Evidence level: VERIFIED (exhaustive NEON DP, 180 min total sweep)
