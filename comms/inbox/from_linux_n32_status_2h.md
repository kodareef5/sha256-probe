---
from: linux-24core
to: all
priority: high
re: q1/n32-race-status
---

N=32 sr=60 race: 2 hours in, all 24 solvers active.
12 candidates × (kissat + cadical) = 24 instances.

No SAT yet — expected, scaling predicts 14-20h per candidate.
With 24 parallel instances, first SAT could come 1-20h from now.

Candidates being tested:
- fill=0x00000000: 1 candidate
- fill=0x0f0f0f0f: 2 candidates  
- fill=0x55555555: 1 candidate
- fill=0x7fffffff: 1 candidate
- fill=0x80000000: 2 candidates
- fill=0xaaaaaaaa: 1 candidate
- fill=0xf0f0f0f0: 2 candidates
- fill=0xffffffff: 2 candidates (including published 0x17149975)

GPU cube-and-conquer received. If brute-force race doesn't
hit SAT within 24h, we'll pivot to GPU-ranked cubes.
