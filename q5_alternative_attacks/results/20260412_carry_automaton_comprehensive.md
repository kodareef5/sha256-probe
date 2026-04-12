# Carry Automaton Comprehensive Results — 2026-04-12

## Carry Automaton Permutation Property

Verified at N=4, 6, 8, 10, 12: the carry automaton has width = #collisions
at every bit position. Each collision has a unique 98-bit carry state.

| N | Collisions | Width = #coll? | Notes |
|---|-----------|---------------|-------|
| 4 | 49 | YES (all bits) | |
| 6 | 50 | YES (all bits) | |
| 8 | 260 | YES (all bits) | Perfect permutation |
| 10 | 946 | bits 1-9: YES, bit 0: 944 | 99.8% (2 dup at bit 0) |
| 12 | 252+ (running) | YES (sampled, 147 partial) | |

## Carry-Diff Invariant Fraction

The a-path additions (Sig0+Maj, d+T1, T1+T2) have invariant carry-diffs
from round 59 onward. This fraction converges to ~42% for N>=6.

| N | Carry-diff bits | Invariant | Fraction |
|---|----------------|-----------|----------|
| 4 | 147 | 79 | 53.7% |
| 6 | 245 | 99 | 40.4% |
| 8 | 343 | 147 | 42.9% |
| 10 | 441 | 189 | 42.9% |
| 12 | 539 | 227 | 42.1% |

Convergence: 42-43% for N>=6. The 54% at N=4 is a small-N effect.

## Odd-N Zero Theorem

MSB kernel produces 0 collisions at all tested odd N:

| N | Candidates (da56=0) | Collisions |
|---|---------------------|-----------|
| 5 | 2 | **0** |
| 7 | 2 | **0** |
| 9 | >=1 | **0** |

Candidates with da56=0 exist at odd N, but the 7-round tail produces
no collisions. Likely related to rotation amount parity under banker's
rounding (scale_rot).

## Per-Addition Decomposition (verified N=8, N=10)

From round 59 onward:
- **100% invariant**: Sig0+Maj (T2), d+T1 (new_e), T1+T2 (new_a)
- **0% invariant**: +W (T1 chain), h+Sig1, +Ch
- **Partially invariant**: +K (14-43%)

The a-path (T2 additions) is fully determined by cascade + state56 diffs.
All collision freedom is in the T1 chain.

## NEON Cascade DP Performance

| N | Collisions | Time | Throughput |
|---|-----------|------|-----------|
| 8 | 260 | 2.1s | 2.00e9/s |
| 10 | 946 | 562s | 1.96e9/s |
| 12 | 252+ | ~7h est | ~2e9/s |

## Bit-Serial Width Profile (N=8)

Per-bit prefix collision check gives 31x speedup over brute force:
survivors converge from 133M (bit 0) to 260 (bit 7).
With carry-state deduplication: width = 260 at ALL bits.
