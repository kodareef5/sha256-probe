---
from: laptop
to: linux
priority: high 
re: GPU cube ranking for N=32 cand4 (0x3f239926, fill=0xaa)
---

# GPU Cube Ranking: N=32 Best Starting Points

Ranked 65,536 cubes (top 16 bits of W1[57]) in 8.2s on RTX 4070.
4096 random completions per cube. Candidate: 0x3f239926, fill=0xaa.

Best cubes (W1[57] prefix << 16):
  cube=0x07d1  min_hw=81
  cube=0x269d  min_hw=81
  cube=0x4a29  min_hw=82

Only 2/65536 cubes achieve hw=81. The sweet spot is 0.003% of the space.

If you want to try cube-and-conquer on this candidate:
fix W1[57] top 16 bits to 0x07d1, let SAT solve the remaining bits.
This pre-constrains the solver to the most promising region.
