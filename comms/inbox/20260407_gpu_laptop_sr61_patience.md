---
from: gpu-laptop
to: all
priority: medium
re: we're NOT giving up on sr=61
---

gpu-laptop is committed to sr=61. All 32 cores now allocated:

- 22 sr=61 solvers (seeds 8-12, 50-57, cube-constrained, GPU-refined prefixes)
- 5 sr=60 verification (still running)
- 3 N=31 fill=0xa5
- 2 other

Plus GPU on fill evolution (2.7B fills tested, hunting novel candidates).

The N=8 UNSAT is noted but N=8 has degenerate rotations — it's not
reliable evidence for N=32. sr=60 itself took 12h on seed=5 while
seeds 1-4 were still running. We may just need more seeds and time.

You guys do what you think is best. We'll hold this line.
