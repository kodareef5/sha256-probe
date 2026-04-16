# BDD Size Measurement: N=8 Collision Set

**Date**: 2026-04-16

## Method

Built BDD from the 260 N=8 collisions using `bdd_from_coll` with 
interleaved bit-first variable ordering (bit 0 of W57, bit 0 of W58, ..., bit 7 of W60).

## Results

- **BDD nodes: 4322** (for 260 collisions = 16.6 nodes/collision)
- Total memory: ~35 KB
- Construction time: 0.04s (from collision list)

## Per-Variable Node Count

Nodes decrease from low bits toward high bits (MSB = var 31):

| Var range | Nodes | Interpretation |
|-----------|-------|---------------|
| 0-5 (low bits) | 487-519 | Wide BDD layer — many state distinctions |
| 6-15 (middle) | 262-459 | Moderate branching |
| 16-23 | 210-260 | Narrowing |
| 24-27 | 33-159 | Fast shrinkage |
| 28-31 (high bits) | 2-16 | Very narrow — high bits mostly determined |

The MSB bits (var 28-31) encode just 16 → 8 → 4 → 2 node transitions.
This means the top 2 bits of each word are near-deterministic given
the lower bits — consistent with the MSB-kernel cascade zeroing.

## BDD Scaling Exponent (3 data points)

| N | BDD nodes | Collisions | Nodes/coll |
|---|----------:|----------:|----------:|
| 4 | 183 | 49 | 3.7 |
| 8 | 4,322 | 260 | 16.6 |
| 10 | 14,818 | 691* | 21.4 |

\* N=10 partial (691 of ~946 collisions)

3-point least-squares fit: **nodes = C × N^4.74**

Consistent with prior O(N^4.8) estimate.

## Projection to N=32

N^4.74 fit projects: **~3.4M nodes ≈ 68 MB** at N=32.

A SHA-256 sr=60 cascade collision BDD at N=32 would easily fit in RAM.

## The Construction Bottleneck

BDD SIZE is polynomial, but CONSTRUCTION is not:
- `bdd_from_coll` takes the collision LIST as input → requires prior enumeration (2^{4N})
- `bdd_incremental` and `bdd_streaming` construct from circuit definition
  but still need to traverse 2^{4N} bit-combinations

**If we had the N=32 BDD, we could enumerate all collisions in O(BDD size) = 100MB**.

The open question: is there a polynomial-time BDD construction that doesn't
require knowing collisions a priori? If yes, cascade collision finding at
N=32 is polynomial.

## Relation to Cascade Tree Linearity

Earlier finding: the cascade forward-tree has branching factor ~1 after W57.
That says: **in a SEARCH TREE**, each intermediate node leads to ~1 child.

BDD compactness says: **in a DECISION DIAGRAM**, the collision set has
~N^4.56 nodes.

Both confirm the collision set has bounded structural complexity.
Neither directly gives us a polynomial construction algorithm.

The "path to polynomial-time sr=60" requires finding a DIRECT mapping
from M[0] (or input) to collision coordinates that doesn't enumerate
the 2^{4N} candidates.

## Next Tests

- [ ] Construct BDD of N=10 collisions (once cascade_dp_fast N=10 finishes)
- [ ] Verify N^4.56 scaling with 3 data points
- [ ] Attempt incremental BDD construction at N=12 to see if polynomial
      construction is possible
