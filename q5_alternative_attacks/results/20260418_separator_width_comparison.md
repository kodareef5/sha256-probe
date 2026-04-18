# Separator Width Comparison: Standard vs Derived Encoding

**Date**: 2026-04-18
**Evidence level**: VERIFIED

## Results

| Encoding | N | Vars | Edges | Avg Deg | Max Deg | Treewidth UB |
|----------|---|------|-------|---------|---------|-------------|
| Standard | 4 | 1162 | 3601 | 6.2 | 33 | 71 |
| Standard | 8 | 2544 | 8271 | 6.5 | 34 | 115 |
| Derived | 8 | 2886 | 9498 | 6.6 | **63** | **189** |

d4 FlowCutter treewidths (more accurate):
| Encoding | N | d4 treewidth |
|----------|---|-------------|
| Standard | 4 | 54 |
| Standard | 8 | 110 |
| Derived | 8 | 181 |

## Key Finding

The derived encoding HURTS knowledge compilation:
- 2× max degree (63 vs 34) from cascade offset variable dependencies
- 64% higher treewidth (189 vs 115 heuristic; 181 vs 110 d4)
- The cascade offset computation creates DENSE interconnections

## Implication

- For SAT solving: derived encoding HELPS (fewer free vars: 32 vs 64)
- For knowledge compilation: derived encoding HURTS (higher treewidth)
- SAT and compilation have OPPOSITE encoding preferences

## GPT-5.4 Suggestion: Cascade-Auxiliary Encoding

Instead of substituting W2 = W1 + offset (derived), introduce auxiliary
variables O[r] for the cascade offsets with LOCAL definitions:
  O[r] = (T1_nw_1 - T1_nw_2) + (T2_1 - T2_2)
  W2[r] = W1[r] + O[r]

This might help BOTH SAT (propagation via O) and compilation (local
variable dependencies instead of global substitution).

Not yet implemented.
