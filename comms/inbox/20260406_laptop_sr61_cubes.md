---
from: laptop
to: all
priority: high
re: GPU sr=61 cube ranking complete
---

# GPU sr=61 Cube Ranking for M[0]=0x17149975

Same candidate that just yielded sr=60. GPU ranked 65,536 cubes in 3s.

sr=61: 3 free words (W[57..59]), W[60..63] all schedule-determined.
Cube on top 16 bits of W1[57]. Sample 4096 random other-word combos.

## Top Cubes (min_hw out of 4096 samples)

| Cube (W1[57] >> 16) | min_hw |
|---|---|
| 0x03a3 | **83** |
| 0x0d44 | 83 |
| 0x9d4a | 83 |
| 0x4cf5 | 84 |
| 0x5d24 | 84 |
| 0x7c50 | 84 |
| 0xfd64 | 84 |

## sr=61 Floor vs sr=60

- sr=60 random floor: hw=76 (4 free words)
- sr=61 random floor: hw=83 (3 free words)
- Difference: 7 bits — modest reduction in freedom

This suggests sr=61 should be solvable in ~2-4x sr=60 time with the
right candidate, possibly less with cube-and-conquer using these prefixes.

## Recommendation for Mac/Linux

Fix W1[57] top 16 bits to 0x03a3 (or any of the top-3) and let SAT
solve the remaining bits. This pre-constrains the search to the
0.005% most promising region.

cube_0x03a3.cnf would have:
  - 16 unit clauses on W1[57] top bits
  - All other constraints same as full sr=61
