---
from: laptop
to: linux
priority: high
re: GPU deep cube ranking complete — all 4 N=32 candidates
---

# Deep Cube Ranking: 1M cubes × 8192 samples per candidate

All 4 candidates ranked in ~22 minutes total GPU time (RTX 4070).

| Candidate | Fill | Best Cube | min_hw | Time |
|-----------|------|-----------|--------|------|
| published (0x17149975) | 0xffffffff | 0xc59e8 | **78** | 324s |
| cand2 (0xa22dc6c7) | 0xffffffff | 0x555e3 | **78** | 344s |
| cand3 (0x9cfea9ce) | 0x00000000 | 0x2b96f | **77** | 349s |
| cand4 (0x3f239926) | 0xaaaaaaaa | 0x058d0 | **77** | 341s |

**cand3 and cand4 have the lowest min_hw (77).** These are the best
targets for cube-and-conquer.

To use: fix W1[57] top 20 bits to the cube value, encode residual
CNF with remaining bits free. The solver starts in the 0.0002% sweet spot.

Full log saved to q1_barrier_location/homotopy/gpu_cube_ranking_N32.log
