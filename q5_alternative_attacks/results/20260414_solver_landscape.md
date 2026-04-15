# Solver Landscape: Complete Assessment

## Approaches Tested at N=8

| Solver | Wall-clock | vs NEON 2.1s | Branches | Key mechanism |
|--------|-----------|-------------|----------|---------------|
| NEON brute force | 2.1s | baseline | 4.3B | SIMD concrete |
| **Structural (de61)** | **0.68s** | **3.08x** | 4.3B (99.6% pruned) | Register-diff filter |
| A-path first | 0.73s | 2.9x | 4.3B (filtered) | de59 constant check |
| FACE symbolic | 45s | 2.44x (scalar) | 33.4M | GF(2) mode-branching |
| Scalar brute force | 88s | 0.024x | 4.3B | baseline scalar |

## Why Register-Diff Filters Max Out at ~3x

The cascade construction GUARANTEES that all e-path diffs at state59 are 
identical for ALL (W57,W58,W59) triples. Suffix compatibility is VACUOUS.
The only effective register-diff filter is de61=0 (1/2^N pruning on rounds 62-63).

Measured: 100% of random triples produce de59=0x8e, dg59=0xa3, dh59=0xb9.
This is because the cascade offset makes all message-diff propagation deterministic.

## Why FACE Gives 128x Branch Reduction but Only 2.44x Wall-Clock

Each GF(2) branch involves RREF operations: O(N²) per constraint addition.
At N=8 with 32 variables: ~1024 operations per branch.
Concrete evaluation: ~50 operations per config.
Overhead ratio: ~20x per branch.
Net: 128x / 20x ≈ 6x theoretical, 2.44x measured.

## The Crossover Point

At N=K: FACE branch reduction ≈ 2^K (rotation frontier savings).
GF(2) overhead: O(K²) ≈ K² per branch.
Crossover: 2^K > K² → K ≥ 10.
At N=32: estimated 2^25 branch reduction / O(128²) overhead ≈ 2000x net.

## For the Paper

The 3.08x structural solver (de61=0 + NEON) is the practical result.
The FACE symbolic framework is the theoretical contribution.
The structural theorems (Cascade Diagonal, Single DOF, Three-Filter Equivalence,
sr=61 Break) are the mathematical contribution.

The carry automaton width scaling (2^{0.76N}) bounds the true algorithmic
complexity. Achieving this bound requires carry-level reasoning (FACE/BCSDP),
not register-diff filtering.
