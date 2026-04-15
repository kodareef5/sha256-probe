# N=9 Freedom Threshold: COMPLETE Phase Transition

## Result

sr=61 at N=9 (kernel bit 1) is UNSAT with ANY number of enforced W[60]
schedule bits (1 through 9). The phase transition is maximally sharp:

| Enforced bits | Freed bits | Status | Count |
|---------------|-----------|--------|-------|
| 0 (sr=60) | 9 | **SAT** | known |
| **1** | **8** | **UNSAT** | **9/9 proved** |
| 2 | 7 | UNSAT | 36/36 proved |
| 3 | 6 | UNSAT | 82/84 proved, 2 timeout |
| 4 | 5 | UNSAT | 126/126 proved |
| 5 | 4 | UNSAT | 126/126 proved |
| 6 | 3 | UNSAT | 84/84 proved |
| 7-9 | 2-0 | UNSAT (sr=61) | not tested individually |

**Total: 463 UNSAT proofs + 2 timeouts across all freedom levels.**

## Significance

The sr=60 → sr=61 transition at N=9 is the SHARPEST POSSIBLE:
enforcing ANY SINGLE schedule bit on W[60] makes the system unsatisfiable.

This means:
1. The cascade MUST have COMPLETE freedom over W[60] at N=9
2. There is no "partial sr=61" — it's all-or-nothing
3. The schedule constraint at EVERY bit position independently kills collisions
4. This is consistent with the 2^{-N} cascade break theorem:
   P(one bit compatible) = 1/2, but the collision equation dT1_61=0
   creates a global constraint that NO single bit can independently satisfy

## Comparison with N=8

At N=8 (kernel bit 3): sr=61 is SAT with 2 freed bits (pair (4,5)).
At N=9 (kernel bit 1): sr=61 is UNSAT even with 8 freed bits.

The transition from N=8 to N=9 is dramatic:
- N=8: 2/8 = 25% freedom needed → SAT
- N=9: 9/9 = 100% freedom needed → UNSAT at any partial freedom

This is likely a property of N=9's rotation structure (N=9 is odd,
rotations degenerate) rather than a monotonic scaling law.

Evidence level: VERIFIED (463 UNSAT proofs + 2 timeouts, exhaustive at N=9)
