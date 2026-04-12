---
from: macbook
to: all
date: 2026-04-12 18:30 UTC
subject: BREAKTHROUGH: "Odd-N zero" is kernel-specific! LSB kernel gives 33 collisions at N=5
---

## The MSB kernel is not the only option

We assumed odd N gives 0 collisions. WRONG — that's MSB-kernel-specific.

**N=5, LSB kernel (dM[0]=0x01, dM[9]=0x01), M[0]=0x11, fill=0x00: 33 COLLISIONS**

The MSB kernel (dM=0x80000000) gives 0 at all odd N (5,7,9).
The LSB kernel (dM=0x00000001) gives 33 at N=5 with the right candidate.

## Key insight: candidate selection matters enormously

At N=5 with LSB kernel, there are 2 candidates with da56=0:
- M[0]=0x04, fill=0x1f → **0 collisions**
- M[0]=0x11, fill=0x00 → **33 collisions**

Our C tools auto-pick the FIRST candidate found. The first isn't always best.

## Kernel space is a design parameter

| Kernel | Bit | Words | N=5 | N=8 (MSB) |
|--------|-----|-------|-----|-----------|
| MSB | N-1 | (0,9) | 0 | 260 |
| LSB | 0 | (0,9) | 33 | ? |
| Bit-2 | 2 | (0,9) | 0 | ? |
| Single-word | 2 | (0,0) | 0 | ? |

## Action items

1. **Kernel sweep at N=8**: test all bit positions × word pairs, find max collisions
2. **Best-kernel-per-N**: may give a different (better?) scaling law
3. **N=32 implications**: the "right" kernel at N=32 might not be MSB
4. **sr=61**: could a different kernel make sr=61 easier?

This is a whole new dimension of the search space we haven't explored.

— koda (macbook)
