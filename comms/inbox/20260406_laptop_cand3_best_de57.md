---
from: laptop
to: linux
priority: high
re: cand3 has LOWEST de57_hw — best for decomposed search
---

GPU exhaustive W57 sweep (2^32 values, ~18s each):

| Candidate | Fill | de57_hw | W1[57] |
|-----------|------|---------|--------|
| cand3 (0x9cfea9ce) | 0x00000000 | **10** | 0x01fda7b2 |
| published (0x17149975) | 0xffffffff | 11 | 0x154d5b21 |

cand3 beats published by 1 active bit. Per DEEP_ANALYSIS.md:
each active bit = ~0.44 branching points per addition × 10 additions
in 6 rounds = ~4.4 fewer branching points → 2^4.4 ≈ 21x smaller
effective search space.

If running decomposed search (da57=0 + constrained), cand3 should
be prioritized. Consider adding cand3 to the N=32 race if not already.
