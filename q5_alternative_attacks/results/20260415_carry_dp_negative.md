# Carry-State DP: Negative Result

## Finding

The carry-diff state width for ALL inputs is ~89-99% of the search space.
The carry automaton's bounded width applies ONLY to the collision subset.

## Data (N=4, search space = 65536)

| Bit | Unique carry-diff states | % of search space |
|-----|--------------------------|-------------------|
| 0 | 58903 | 89.9% |
| 1 | 65148 | 99.4% |
| 2 | 65469 | 99.9% |
| 3 | 65175 | 99.4% |

## Why This Matters

A carry-state DP that tracks ALL reachable states at each bit position
would have width ≈ 2^{4N} — identical to brute force. The carry-diff
bits are nearly INJECTIVE over the full input space.

The carry automaton's bounded width (~49 at N=4, ~260 at N=8) is a
property of the SOLUTION SET, not the SEARCH SPACE. You can verify it
after finding collisions, but you can't use it to find them efficiently.

## Root Cause: Rotation Frontier

SHA-256's Sigma functions (rotations + XOR) spread information across bit
positions. The carry at bit b depends not just on bits 0..b, but on ALL
N bits of the register (via rotations). This makes the bit-serial state
a function of the full N-bit input at every bit position.

The 42% carry-diff invariance is also a solution-set property: among
collisions, 42% of carry-diff bits are always the same. But among all
inputs, the carry-diff bits span nearly the full state space.

## Implications

1. Carry-state DP is NOT a path to polynomial-time collision finding
2. The polynomial BDD exists (O(N^4.8)) but the SEARCH is still 2^{4N}
3. The bounded carry width for collisions is structural but non-exploitable
4. Any polynomial-time algorithm must bypass the rotation frontier
   entirely, not work within the carry framework

## What Could Still Work

- SMT/bit-vector solvers that reason about carries symbolically (not enumeratively)
- SAT solvers with carry-aware branching heuristics (expose carry variables)
- Meet-in-the-middle: forward from r57, backward from r63 (collision condition)
- Multi-block attacks that avoid the rotation frontier

Evidence level: VERIFIED (exhaustive at N=4)
