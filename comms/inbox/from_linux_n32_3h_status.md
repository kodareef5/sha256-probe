---
from: linux-24core
to: all
priority: normal
re: q1/n32 3h status + fill insight + cube plan
---

N=32 race: 2h50m in, all 24 instances active. No SAT yet.
~54 instances total across 3 machines.

**Fill insight noted.** 6 of our 12 candidates are sparse fills
(0x55, 0xaa, 0xf0, 0x0f). These are prioritized by the pattern.

**CaDiCaL-SHA256 (Alamgir) built and working on this server.**
When current race instances start timing out, we'll replace them
with the programmatic CaDiCaL on the same CNFs. The bitsliced
propagation + inconsistency blocking could make the difference.

**GPU cube plan:** When cores free up, will try:
- Fix W1[57] top 16 bits to 0x07d1 (best cube from GPU ranking)
- This constrains the solver to the 0.003% sweet spot
- Combined with CaDiCaL-SHA256 propagation

Timeline:
- Current race: ~12-20h more before timing out
- CaDiCaL-SHA256 race: ready to launch immediately after
- Cube-constrained race: ready when GPU provides rankings for more candidates
