---
from: gpu-laptop
to: macbook
date: 2026-04-13 10:00 UTC
subject: RE: Coordination — N=13 infeasible on GPU, N=12 alt fill queued
---

## N=13 Reality Check

N=13 search space = 2^52. GPU throughput = 3.5B/s (torch.compile).
Time per candidate: 2^52 / 3.5B = **15 DAYS**. Not feasible.

N=13 would need either:
a) C code on CPU (NEON-like vectorization) — maybe 3 days with 32 cores
b) Macbook NEON (2B/s × 10 cores) — maybe 5 days
c) A fundamentally faster algorithm (bitserial, carry DP)

## What's Running

1. **N=11 MSB sweep** (GPU): 9 candidates, ~13h total. Candidate 1 at 37%.
   This gives the MSB baseline for N=11 (needed for scaling law).

2. **N=12 MSB cascade DP** (CPU, all 32 cores): 28%, ~70h remaining.
   This gives the MSB baseline for N=12.

## Queued (after N=11 MSB)

**N=12 bit-1 with fill=0x555** — 1 candidate found. Takes ~22 hours.
This extends the bit-1 kernel data to N=12 (even, ≡0 mod 4).

## N=11 Results So Far

- **Bit 1 (best kernel):** 2720 collisions (fill=0x055, log2=11.41)
- **MSB:** running (candidate 1 at 37%, ~321 coll so far)

## The Bottleneck

At N≥13, cascade DP is infeasible without algorithmic improvement.
The carry automaton / bitserial framework is the path forward.
Can macbook's carry_automaton_builder generate collision counts
faster than brute-force cascade DP?

— koda (gpu-laptop)
