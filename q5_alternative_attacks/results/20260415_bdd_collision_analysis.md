# BDD Analysis of Collision Function at N=4

The collision function f(W57,W58,W59,W60) = 1 iff collision.
16 Boolean variables, 49 SAT entries out of 65536.

## BDD Size

| Variable ordering | Nodes | vs random |
|-------------------|-------|-----------|
| Natural (word bits) | 188 | 174x smaller |
| **Interleaved (bit-first)** | **183** | **179x smaller** |
| Reverse | 218 | 150x smaller |
| Random function (expected) | ~32768 | baseline |

## Significance

The collision function has MASSIVE structure. 183 BDD nodes encode
all information to find 49 collisions. This is 358x fewer nodes
than truth table entries (65536).

The bit-first (interleaved) ordering is slightly better, consistent
with carry structure being bit-local.

## Scaling Question

If BDD size scales polynomially with N: polynomial-time collision finding.
BDD construction from truth table is exponential — need incremental build.

Evidence level: VERIFIED (exhaustive truth table at N=4)
