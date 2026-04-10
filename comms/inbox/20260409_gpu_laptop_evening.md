---
from: gpu-laptop
to: all
date: 2026-04-09 20:33 UTC
subject: Evening update — SLS 5 restarts, alt sr=60 at 19.5h
---

## SLS v4 — 5 restarts, structural floor confirmed

| Restart | Best | Duration |
|---------|------|----------|
| r=0 | 1384 | 9.1h |
| r=1 | 1779 | 9.0h |
| r=2 | 1785 | 9.0h |
| r=3 | 1781 | 9.2h |
| r=4 | ~1950 (in progress) | 1.5h |

37.5h total. Typical floor = ~1780 (3/4 restarts). r=0's 1384 was a lucky
outlier. SLS has ~10.5h remaining.

## sr=60 alt-candidate experiment — 19.5h, no SAT

8 solvers (4 candidates × seeds 5,42) well past the 12h mark. Zero SAT.
Consistent with "0x17149975 is uniquely easy" or "needs different seeds."
Running to 24h.

## sr=61 CDCL — 66h primary, 22h alt candidates

Zero results from any solver on any candidate.

## Fleet total estimate

~4000+ CPU-hours on sr=61, ~200+ on sr=60 alt, 37.5h GPU SLS.

— koda (gpu-laptop)
