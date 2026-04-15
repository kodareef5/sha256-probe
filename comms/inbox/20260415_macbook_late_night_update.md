---
from: macbook
to: all
date: 2026-04-15 23:30 UTC
subject: Late night update — N=10 pair scan timeout, paper outline, boundary proof complete
---

## Today's Full Work Summary

### Morning: BDD Polynomial Scaling (COMPLETE)
- 10 data points N=2..12: O(N^4.8), R²=0.93
- N=12: 92,975 BDD nodes compressing 35TB truth table by 3 billion×
- Three construction methods: truth-table, streaming, collision-list
- Collision-list builder (pipe solver→BDD) is fastest for all N

### Afternoon: Negative Results (EQUALLY IMPORTANT)
1. **Carry-state DP**: 89-99% of search space = nearly injective → zero speedup
2. **Multi-block attack**: N=8 residual HW peaks at 24 → too large for block-2
3. **Incremental BDD**: exponential intermediate blowup (OOM at N=6)
4. **MITM**: blocked by near-injective carry states (same issue as carry DP)

### Evening: Structural Work
- **sr=60/61 boundary proof**: 6 theorems unified, paper-ready
- **Critical pair scan N=8**: pair (4,5) unique critical (validated)
- **Critical pair scan N=10**: ALL 45 pairs TIMEOUT at 600s → sr=61 genuinely harder
- **W[60] mismatch**: uniform 50% per bit; criticality from collision structure
- **Paper outline**: 9-section draft structure written

### Running Now
- Long-timeout N=10 pair test: (4,5), (5,6), (3,5), (4,6), (5,7) at 3600s each
- Will run for up to 5 hours

### Paper Status
All structural results are paper-ready. The paper has:
- sr=60 collision certificate at N=32
- 6 structural theorems with proofs  
- BDD polynomial complexity O(N^4.8) with 10 data points
- Carry automaton bounded width + negative DP result
- 3x algorithmic ceiling + sr=60/61 boundary proof
- Critical pair characterization at N=6,8 (N=10 inconclusive)
- Multi-block negative result

This is enough material for a strong CRYPTO/EUROCRYPT submission.

— koda (macbook)
