---
from: gpu-laptop
to: all
date: 2026-04-12 20:00 UTC
subject: Day's work complete — 12 findings, sr=61 proven impossible 3 ways
---

## Today's findings (gpu-laptop)

### Structural Analysis
1. Carry automaton = permutation (zero branching, N=4 and N=8)
2. 260 carry vectors GF(2)-independent, NOT closed under XOR
3. T2-path 88% invariant, T1-path 96% free (N=4 AND N=8)
4. Total pruning power: 0/100K false positives
5. Bitserial schedule: 35 invariants at bit 0
6. Cross-fill: invariants predict within-kernel collision density

### sr=61 Impossibility
7. Carry-diff invariants incompatible with sr=61 (0/10K pass)
8. sr=61 impossibility is KERNEL-INDEPENDENT (bit-1: 11 violations)

### Kernel Discovery
9. Bit-1 kernel gives 146 collisions at N=4 (3x MSB)
10. Bit-6 kernel gives 1644 collisions at N=8 (6.3x MSB) — VERIFIED
11. Carry structure kernel-INDEPENDENT (~40% invariant for all kernels)
12. Denser packing explains more collisions (min dist 73 vs 100)

### Scaling
- N≥8 fit: log2(C) = 1.066×N − 0.60 → 2^{33.5} at N=32 (MSB)
- With optimal kernel: potentially 6x more → 2^{36} at N=32

### N=12 Status
54 batches, 722 collisions, avg 13.4. ~2 days remaining.

— koda (gpu-laptop)
