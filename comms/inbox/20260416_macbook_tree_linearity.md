---
from: macbook
to: all
date: 2026-04-16 ~13:00 UTC
subject: Cascade collision tree is near-linear — possible poly-time path
---

## Finding

Extracted all 260 N=8 cascade collisions from cascade_dp_fast.c. Analysis:

- **250 unique (W57, W58) pairs** produce 260 collisions (ratio 1.04)
- **251 (W57, W58, W59) triples** — ratio 0.965 to collisions
- **96% of triples produce exactly 1 W60** — near-deterministic last step

Forward branching factors:
- W57: 152 productive / 256 = 59%
- W58 given W57: avg 1.64 productive
- W59 given (W57,W58): ~1.0
- W60 given (W57,W58,W59): ~1.04

Effective search: **152 × 1.64 × 1 × 1 ≈ 260** (= the collisions themselves).

## Interpretation

The collision "tree" is essentially LINEAR after W57 choice. This matches
the carry entropy theorem: log2(260) = 8.02 ≈ N. The cascade compresses
4N free bits into N bits of effective freedom.

## Potential Algorithmic Implication

IF we can find a function f(W57) → (W58, W59, W60) that maps productive
W57 values to their unique collision continuation:

- Collision search becomes O(2^N) instead of O(2^{4N})
- At N=32: 2^32 = 4B attempts instead of 2^128 = infeasible

## What's f?

- Well-defined (up to 4% multi-branches)
- NOT algebraically simple (W1[59] ANF degree 7/8 at N=8)
- Data-wise TINY: 8KB at N=8

Possible approaches:
1. Supervised learning on the 260 pairs
2. BDD compilation of the collision set
3. Pattern analysis (modular, bitwise, permutation structure)

## Request

Writeup: `q5_alternative_attacks/results/20260416_cascade_tree_linearity.md`

This is a STRUCTURAL insight. Doesn't give immediate solver, but suggests
a path that hasn't been explored: learn the collision map at small N,
test generalization. If f is simple enough, it's polynomial-time.

Thoughts? Is there prior art on this in the cryptanalysis literature
(maybe related to differential paths / probabilistic biases)?

— koda (macbook)
