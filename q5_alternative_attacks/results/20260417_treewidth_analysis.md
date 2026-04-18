# Treewidth Analysis of sr=60 CNF

**Date**: 2026-04-17
**Evidence level**: EVIDENCE (heuristic upper bound)

## Results

N=4 CNF (1162 vars, 4828 clauses):
- Primal graph: 3601 edges, avg degree 6.2, max degree 33
- **Treewidth upper bound (min-degree heuristic): 71**

N=8 CNF (2544 vars, 10656 clauses):
- Primal graph: 8271 edges, avg degree 6.5, max degree 34
- Density: 0.26% (very sparse)

## Interpretation

Treewidth ~71 at N=4 means d4 works in O(2^71) worst case.
This explains why d4 takes 39 seconds at N=4 (not milliseconds).
At N=8, treewidth is likely similar (graph structure is SHA-256
round function, not word width dependent), explaining d4's multi-hour runtime.

The derived encoding (32 vs 64 free vars at N=8) might reduce
effective treewidth by removing variable dependencies. Test running.

## Key Finding

The graph density is very low (0.26-0.53%) and avg degree is ~6.
This suggests the CNF has significant decomposable structure that
d4 exploits — but the treewidth is still O(50-100) due to the
rotation frontier creating long-range dependencies.

## Comparison with d4 Performance

| N | Treewidth UB | d4 time | Expected O(2^tw) |
|---|-------------|---------|------------------|
| 4 | 71 | 39s | 2^71 ≈ too high |
| 8 | ~71-100? | ~5h+ | Would predict days |

The mismatch suggests d4's CDCL + component caching is much smarter
than raw treewidth would suggest. The component caching decomposes
the problem into smaller pieces with lower local treewidth.
