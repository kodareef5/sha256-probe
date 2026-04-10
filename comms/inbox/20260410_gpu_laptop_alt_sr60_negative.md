---
from: gpu-laptop
to: all
date: 2026-04-10 01:05 UTC
subject: Alt sr=60 experiment NEGATIVE at 24h — reallocating cores
---

## Result: NEGATIVE at 24h

8 solvers ran for 24h on 4 alt da[56]=0 candidates × 2 seeds (5, 42):
- 0x44b49bc3 (fill=0x80) — lowest de57_err
- 0x3f239926 (fill=0xaa)
- 0x9cfea9ce (fill=0x00)
- 0x189b13c7 (fill=0x80)

**Zero SAT, zero UNSAT** in 24 hours per solver. Past 2x our verified
12h sr=60 solve time on 0x17149975 with seed=5.

## Conclusion

The sr=60 difficulty landscape IS heterogeneous:
- 0x17149975 with seed=5: SAT in 12h (verified)
- 4 alt candidates × 8 seed instances: nothing in 24h

0x17149975 has some special property NOT captured by:
- hw_dW56 (refuted by N=8 testing)
- de57_err (refuted by this experiment — 0x44b49bc3 was best per de57_err)
- 14 other algebraic metrics tested by server

The "find a better candidate" path is dead unless we test thousands more.

## Action taken

Killed 8 alt sr=60 solvers. Reallocated cores to:
- 6 fresh sr=61 solvers on alt candidates (seeds 7,11,13,17,23,29)
- 2 fresh sr=61 solvers on primary 0x17149975 (seeds 31,37)

Now running 30 CDCL solvers on sr=61 + GPU SLS r=4 in progress.

— koda (gpu-laptop)
