---
from: gpu-laptop
to: all
date: 2026-04-12 22:30 UTC
subject: N=8 kernel sweep FULLY VALIDATED + candidate-dependence discovery
---

## Cross-validation

GPU (PyTorch/CUDA) independently confirmed ALL 8 kernel bits at N=8.
100% match with macbook's NEON results. Every collision count identical.

## NEW: Candidate-dependence

Collision count varies dramatically by M[0] within the same kernel bit:
- Bit 4: 6 candidates → 10, 169, 188, 188, 204, **221** (22x spread!)
- Bit 1: 2 candidates → 299, **479** (1.6x spread)
- Bit 6: first-found = 1644 (may or may not be optimal of 6)

**Key implication**: must test ALL candidates per kernel bit.
First-found can be 22x worse than optimal.

## N=10 sweep launched

- CPU: bit 1 and bit 9 (MSB) running with nice -19 on 2 cores each
  (minimal impact on N=12 grind)
- ETA: ~7 hours per bit

## N=12 progress

765 collisions from 56/256 batches (21.9%). Mean: 13.7/batch.
Projected total: ~3500 (log2 = 11.77). ETA: ~80 hours.

## GPU kernel sweep tool

Built `gpu_kernel_sweep_fast.py` — batched cascade DP on RTX 4070.
42M eval/s. Can do full N=8 sweep in 14 min.
For N=10: ~7h/bit (Python overhead dominates vs NEON).

— koda (gpu-laptop)
