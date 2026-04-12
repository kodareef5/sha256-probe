# Carry Automaton Width at N=10 — 2026-04-12

## Result

946 collisions at N=10. Carry automaton width measured at each bit:

| Bit | Distinct carry states | = #collisions? |
|-----|----------------------|----------------|
| 0 | 944 | NO (2 duplicates) |
| 1 | 946 | YES |
| 2-9 | 946 | YES |

**The carry automaton is a near-perfect permutation at N=10.**

## Comparison with N=8

| N | Collisions | Bit 0 | Bits 1+ | Perfect? |
|---|-----------|-------|---------|----------|
| 8 | 260 | 260 | 260 | YES |
| 10 | 946 | 944 | 946 | 99.8% |

The bit-0 degeneracy at N=10 is because carry-out at bit 0 = x_0 AND y_0
(no carry-in), capturing less state information than higher bits which
depend on full carry chains. The 2 duplicate states diverge at bit 1.

## Implication

The permutation property scales: each collision has a unique carry
trajectory from bit 1 onward. The automaton width grows with #collisions
(260 at N=8, 946 at N=10), confirming it tracks the solution set.

Growth rate: 946/260 = 3.64x for N=10/N=8.
log2(946)/log2(260) = 9.89/8.02 = 1.23.
Scaling: ~2^{0.94N} (subexponential in N).
