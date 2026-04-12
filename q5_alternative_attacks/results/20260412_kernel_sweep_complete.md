# Kernel Sweep Results — 2026-04-12

## Best single-bit kernel per N (words 0,9)

| N | Best bit | Best coll | MSB coll | Improvement | Best M[0] | Fill |
|---|---------|----------|---------|-------------|-----------|------|
| 4 | 1 | **146** | 49 | 3.0x | 0x03 | 0x00 |
| 5 | 0 | **37** | 0 | 0→37 | 0x0a | 0x0f |
| 6 | 4 | **83** | 50 | 1.7x | 0x15 | 0x1f |
| 7 | 1 | **373** | 0 | 0→373 | 0x55 | 0x00 |
| 8 | **6** | **1644** | 260 | **6.3x** | 0x12 | 0xff |
| 9 | running | | 0 | | | |

## N=8 full bit profile

| Bit | Collisions | Notes |
|-----|-----------|-------|
| 0 | 180 | |
| 1 | 479 | |
| 2 | 307 | |
| 3 | 133 | worst |
| 4 | 221 | |
| 5 | 324 | |
| **6** | **1644** | **BEST — 6.3x MSB** |
| 7 | 260 | MSB (standard) |

## Best-kernel scaling law (provisional)

| N | Best coll | log2 |
|---|----------|------|
| 4 | 146 | 7.19 |
| 5 | 37 | 5.21 |
| 6 | 83 | 6.37 |
| 7 | 373 | 8.54 |
| 8 | 1644 | 10.68 |

Growth from N=7→8: +2.14 bits (vs +0.99 for MSB kernel).
The optimal kernel gives MUCH faster collision growth.

## Implication

The MSB kernel was a dramatically suboptimal choice. At N=8, bit 6
gives 6.3x more collisions. The carry automaton properties (permutation,
42% invariant fraction) should be re-verified with the optimal kernel —
they may give even cleaner structure with more collisions.
