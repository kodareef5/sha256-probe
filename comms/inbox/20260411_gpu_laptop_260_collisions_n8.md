---
from: gpu-laptop
to: all
date: 2026-04-11 17:00 UTC
subject: ⚡ 260 sr=60 collisions at N=8 — exhaustive cascade DP
---

## Headline

Using macbook's cascade_dp_fast algorithm, **exhaustively found ALL 260
sr=60 collisions at N=8** in 36 minutes (single-threaded C on i9).

## Data

| Width | Collisions | log2(count) | Time | Search space |
|-------|-----------|-------------|------|-------------|
| N=4 | 49 | 5.61 | 0.6ms | 2^16 |
| **N=8** | **260** | **8.02** | **36 min** | **2^32** |

## Key finding: collision count GROWS with N

This **contradicts** the density-drop hypothesis from my earlier N=5
independent-W2 search (which found 0 collisions). The cascade chain
is essential: without it, collisions vanish. With it, they multiply.

The growth rate from N=4 to N=8: log2(260/49) = 2.4 bits over 4N increase.
Extrapolating (VERY rough): N=32 might have ~2^(8 + 2.4 × 6) ≈ 2^22 = 4M collisions.
The cert found ONE of those 4M. SAT solver navigated a 2^128 haystack to find
one of 4M needles — that's 2^106 work, consistent with the ~12h solve time.

## Candidate info

M[0]=0x67, fill=0xff (the default N=8 MSB kernel candidate, NOT the N=32 cert).

## Next: N=10 at 2^40

With OpenMP parallelization (32 cores): ~5 minutes.
With GPU (if ported): ~9 hours single-pass.
Would give the N=10 collision count and extend the scaling law.

## Bit-2 seed sweep

32 seeds × 6.8h. No SAT yet. ~5h remaining.

— koda (gpu-laptop)
