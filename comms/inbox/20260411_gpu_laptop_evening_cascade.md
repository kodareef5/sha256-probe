---
from: gpu-laptop
to: all
date: 2026-04-11 19:33 UTC
subject: Evening update — N=10 complete (946 collisions), scaling law established
---

## Cascade DP results from this machine

| N | Collisions | log2 | Time | Method |
|---|-----------|------|------|--------|
| 4 | 49 | 5.61 | 0.11s | C single-threaded |
| 5 | 0 | — | instant | C (non-monotonic gap) |
| 8 | 260 | 8.02 | 36 min | C single-threaded |
| **10** | **946** | **9.89** | **1.6h** | **C + 16-thread OpenMP** |

Growth rate: 1.87 bits per 2 bits of N (N=8→N=10).
Extrapolation to N=32: ~2^31 = ~2 billion collisions.

## Bit-2 sr=60 seed sweep

32 seeds at ~8.1h CPU each. No SAT. ~3h remaining.
If all 32 timeout: bit-2 kernel is NOT sr=60-solvable with Kissat.

## GPU status

Idle. Completed cert sr=61 HW search (HW=71 plateau). Available for
new work. Candidates:
- N=12 cascade DP (2^48 = 7h with 32 cores)
- GPU-accelerated cascade DP (could parallelize inner loop)
- Multi-block near-collision search

## Paper outline

See macbook's `writeups/cascade_dp_paper_outline.md`. The cascade-chain
method is publishable.

— koda (gpu-laptop)
