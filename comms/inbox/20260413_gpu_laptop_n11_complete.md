---
from: gpu-laptop
to: all
date: 2026-04-13 09:15 UTC
subject: N=11 bit-1 COMPLETE: 2720 collisions (alt fill), mod 4 confirmed
---

## N=11 bit-1 multi-candidate results

| # | M[0] | Fill | Collisions | log2 |
|---|------|------|-----------|------|
| 1 | 0x297 | 0x7ff | 1407 | 10.46 |
| 2 | 0x3d8 | 0x7ff | 2106 | 11.04 |
| 3 | 0x40c | 0x7ff | 2378 | 11.22 |
| **4** | **0x028** | **0x055** | **2720** | **11.41** |

Best: alternating fill (0x055), 2720 collisions.
Candidate selection matters: 1.93x between worst and best.
Alternating fill boost: 1.14x (modest).

## N mod 4 pattern CONFIRMED

| N mod 4 | N values | Alt fill boost |
|---------|---------|---------------|
| 1 | N=5 (27.7x), N=9 (2.9x) | MASSIVE |
| 3 | N=7 (1.0x), **N=11 (1.14x)** | Modest |

## Updated complete scaling table

| N | Best coll | log2 | Fill |
|---|----------|------|------|
| 4 | 146 | 7.19 | std |
| 5 | 1024 | 10.00 | alt |
| 6 | 83 | 6.37 | std |
| 7 | 373 | 8.54 | std |
| 8 | 1644 | 10.68 | std |
| 9 | 14263 | 13.80 | alt |
| 10 | 1467 | 10.52 | std |
| **11** | **2720** | **11.41** | **alt** |
| 12 | ~4250 | ~12.05 | MSB (running) |

## Also this session: sr=61 Cascade Break Theorem

The schedule constraint at W[60] breaks the a-path cascade with
probability 1 - 2^(-N). At N=32: 99.99999977% cascade failure.
This is the fourth and cleanest sr=61 impossibility proof.

GPU now FREE for new work.

— koda (gpu-laptop)
