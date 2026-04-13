# de58 Growth Law — INDEPENDENTLY VERIFIED on Macbook

Date: 2026-04-13 04:00 UTC

## Verification at N=8

Using MODULAR difference (not XOR!):
- **de57 (mod): 1 value (163)** — constant for ALL 256 W57 values ✓
- **de58 (mod): 8 values** {50,52,66,68,178,180,194,196} ✓
- **de59 (mod): 1 value (142)** — constant ✓
- **de60 (mod): 1 value (0)** — constant ✓

## Critical Methodological Note

Our EARLIER de-pruning analysis used XOR (bitwise) difference, which gave
25 distinct de57 values. This was MISLEADING. The MODULAR (arithmetic)
difference is constant, but the XOR varies because different absolute
values with the same modular diff have different carry patterns.

For de-PRUNING: the modular difference is the correct metric (determines
which W57 values lead to compatible cascade states).

## Implication

The effective search at N=8 is filtered by |de58| = 8 valid W57 values.
For each valid W57, the remaining (W58,W59,W60) search is 2^{3N}.
Total: 8 × 2^24 = 2^27 instead of 2^32 → 32x speedup.

But combined with the carry automaton linearization, the (W58,W59,W60)
search may be solvable in polynomial time → total O(8 × N^3).

Evidence level: VERIFIED (exact computation, matches GPU laptop)
