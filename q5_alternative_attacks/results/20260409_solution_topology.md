# Solution Space Topology — Issue #12 Results

## Setup

N=8 sr=60, candidate m0=0xca fill=0x03 (hw_dW56=0, fast solver).
200 Kissat seeds with 15s timeout each. 95 unique solutions found.

## Results

### No clustering
| Metric | Observed | Random baseline |
|---|---|---|
| Mean Hamming distance | 31.3 | 32.0 |
| Hamming std | 4.2 | 4.0 |
| Min Hamming | 7 | ~16 |
| Max Hamming | 45 | ~48 |

The solution space is **uniformly distributed**, not clustered. The min
distance of 7 means some solutions are moderately close, but there's no
evidence of distinct islands or clusters.

### No backbone
- Fixed bits: 1 (out of 64)
- Truly free bits: 63
- Mean per-bit entropy: 0.9715 (near-maximum 1.0)

**No exploitable backbone.** Almost every bit is equally likely to be
0 or 1 across different solutions. The SAT solver can't benefit from
pre-fixing any bit values.

### Moderate SVD structure
- Rank for 90% energy: 38 of 64
- Rank for 99% energy: 56 of 64
- Top 5 singular values: 9.22, 8.59, 8.34, 8.23, 7.77

The SVD shows moderate dimensionality reduction (38/64 for 90% energy)
but NO dominant direction — the top 5 singular values are all within 20%
of each other. This is weak, diffuse structure rather than a clear
low-dimensional manifold.

## Comparison with diff-linear correlation (Issue #14)

| Analysis | Rank (90% energy) | Interpretation |
|---|---|---|
| Diff-linear correlation matrix | **34 / 256** | Strong low-rank in input→output map |
| Solution space SVD | 38 / 64 | Moderate, diffuse |

The diff-linear matrix reveals much stronger structure (34 of 256) than
the solution space itself (38 of 64). This makes sense: the diff-linear
matrix captures the FUNCTION structure (how inputs map to outputs), while
the solution topology captures the SOLUTION structure (where valid inputs
live). The function can have low-rank structure even when the solutions
are uniformly distributed.

## Implications

1. **"Search near known solutions" strategy: unlikely to help.** Solutions
   are uniformly spread, so local search around a known solution won't
   preferentially find new ones.

2. **Backbone fixing: not viable.** No bits are fixed across solutions.

3. **The difficulty is in the FUNCTION, not the SOLUTION SPACE.** The
   diff-linear rank=34 finding (Issue #14) remains the most exploitable
   structure. The solutions themselves are uniformly distributed in the
   space that satisfies those 34-dimensional constraints.

4. **Multiple solutions exist and are diverse** — 95 unique solutions from
   200 seeds indicates the solution space is large. At N=8, there's no
   uniqueness problem; at N=32, the space may be much sparser.

## Evidence level

**EVIDENCE**: 95 solutions from 200 independent Kissat seeds at N=8.
Hamming distances, backbone, entropy, and SVD are all measured directly.
May not transfer to N=32 (different rotation amounts, much larger space).
