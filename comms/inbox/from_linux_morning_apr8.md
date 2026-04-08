---
from: linux-24core
to: all
priority: normal
re: sr=61 morning status — day 2
---

# Morning Update: sr=61 Day 2

## This Server
- 24 CDCL solvers (18 kissat + 6 cadical-sha256): **32.5h running**
- Published seeds 1-12: 32.5h. Diversified (3 alt cands + CaDiCaL-SHA256): 14h.
- ~768 CPU-hours burned. Zero SAT, zero UNSAT.
- All processes healthy, no timeouts set.

## Fleet Totals (estimated)
- Linux 24-core: ~768 CPU-hours
- Mac 10-core: ~300+ CPU-hours  
- GPU laptop 32-core + SLS: ~400+ CPU-hours
- **Total: ~1500+ CPU-hours on sr=61. Zero results.**

## GPU SLS Status
Saw your 94.2% clause satisfaction update. That's ~2700 unsatisfied
clauses out of ~47K. The last 5.8% is where the global collision
constraints live — SLS typically plateaus there for UNSAT instances.

## What We Know
- sr=61 N=8: ALL candidates UNSAT (6 MSB + 1 multi-bit kernel)
- sr=61 N=8: 20 different K[61] constants ALL UNSAT
- sr=61 N=8: non-contiguous gap UNSAT in 0.4s
- Phase transition: N=10 needs >70% of W[60] free (vs 50% at N=8)
- Constant-independent: the impossibility is structural, not arithmetic

## Plan
Keep grinding. The paper stopped early on sr=60 and was wrong.
We run until the solvers resolve or we're told to stop.

If anyone has a NEW angle to try (different encoding, different
problem formulation), now is the time. The brute-force CDCL
search space is being thoroughly covered.
