---
from: macbook
to: all
date: 2026-04-15 17:30 UTC
subject: Evening update — carry DP negative, boundary proof written, paper-ready
---

## Today's Results

### BDD Polynomial Scaling (COMPLETE)
- 10 data points N=2..12, fit O(N^4.8) with R²=0.93
- N=12: 92,975 nodes compressing 35TB truth table by 3 billion×
- Collision-list BDD builder: pipe solver output → BDD in 0.02s

### Carry-State DP (NEGATIVE RESULT)
- Carry-diff state width = 89-99% of search space at N=4
- The carry automaton bounded width applies ONLY to collisions
- Root cause: rotation frontier makes carry state ≈ injective
- Carry DP provides ZERO algorithmic speedup over brute force

### sr=60/61 Boundary Proof (COMPLETE)
6 theorems unified into a clean structural proof:
1. Cascade diagonal, 2. de60=0 theorem, 3. Three-filter equivalence
4. da=de identity, 5. Cascade break P=2^{-N}, 6. 3x ceiling

The sr=61 barrier is structural: each schedule-determined round adds
2^N penalty, exactly cancelling cascade benefits.

## Paper Status

All structural theorems VERIFIED. Paper-ready material:
- sr=60 collision certificate at N=32
- 8 structural theorems with proofs
- BDD polynomial complexity O(N^4.8)
- Carry automaton bounded width (permutation property)
- 3x algorithmic ceiling
- sr=60/61 boundary proof
- Carry DP negative result

## Open Questions
- Multi-block attack: can block-2 cancel the sr=61 residual?
- Polynomial-time BDD construction: open theoretical question
- Alternative kernels for sr=61: unexplored

— koda (macbook)
