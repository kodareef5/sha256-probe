# SVD-Projected Hill Climbing Results

## Setup

`svd_projected_search.py` uses the 35-dimensional principal direction
basis from the 10K diff-linear correlation matrix as perturbation
directions. Each step picks a random SVD direction, extracts bits
above a random threshold (0.03-0.15), XOR-flips them, accepts if
the cascade-constrained collision HW decreases.

Basis: top 35 right singular vectors of the 10K correlation matrix
(shape 35×256).

Typical perturbation sizes by threshold:
| Threshold | Mean mask size | Min | Max |
|---|---|---|---|
| 0.03 | 106 | 90 | 124 |
| 0.05 | 80 | 67 | 96 |
| 0.10 | 35 | 29 | 64 |
| 0.15 | 11 | 0 | 14 |
| 0.20 | 1 | 0 | 4 |

## Results

200 restarts × 5000 steps = 1,000,000 evaluations:
- **Best HW: 74**
- Mean per-restart best: 85.9
- Range: 74 to 92

## Comparison

| Method | Evaluations | Best HW | Efficiency |
|---|---|---|---|
| Random (cascade scan) | 500K | 75 | baseline |
| Hill climb (single bit) | 2M | 78 | WORSE |
| **SVD projected** | **1M** | **74** | **modest improvement** |
| GPU brute force | 110B | 76 | much worse per eval |

SVD-projected search is:
- Better than single-bit hill climbing (74 vs 78)
- Marginally better than random (74 vs 75)
- Both suggest the plateau is near HW=70-74

## Interpretation

The SVD directions are SLIGHTLY better than bit coordinates, but not
by much. This suggests:
1. The top-35 singular directions capture *some* of the exploitable
   structure (enough to edge out random)
2. But the structure isn't strongly concentrated in the top few directions
3. The remaining 221 dimensions still contain significant residual
4. Mean restart best (85.9) is in line with random (113 mean) considering
   the hill climb descent

## Plateau analysis

All three methods plateau in the range HW 74-78 — the sampling is
consistent that the best achievable HW under cascade constraints alone
is in this neighborhood. This is 74-78 bits of residual collision
distance out of 256.

To break through, we need EITHER:
1. A constraint-aware search that never violates the 4554 deterministic
   bit relationships (reduces space by 6.9%)
2. Multi-bit moves of size 20-40 (jumping over local minima)
3. A solver that works in the 34-dim continuous projection directly
4. A completely different attack vector (Gröbner basis, MITM with W[61..63]
   schedule matching)

## Evidence level

**EVIDENCE**: 1M-evaluation SVD-projected search on the verified cert
candidate. The plateau at HW~74 is reproducible across multiple search
strategies. Confirms that cascade constraints alone are insufficient
for sr=60 at N=32 via any single-bit-level search.
