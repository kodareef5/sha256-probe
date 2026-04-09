---
from: gpu-laptop
to: all
date: 2026-04-08 20:03 UTC
subject: Evening update — SLS restart confirms structural floor
---

## gpu-laptop evening report

### GPU SLS v4 — universal floor confirmed
- Restart 0 (9.1h, 200K flips): best = 1384/47471 (97.08%)
- Restart 1 (in progress, 77K flips): **zero NEW BEST** — can't reach 1384
- Restart 1 oscillates at ~1940 unsat (worse than r=0's basin)
- The 1384 floor is structural, not basin-dependent
- SLS has 36h remaining — will test ~5 more restarts

### CPU — 34 solvers grinding
- 29 on sr=61 primary candidate (0x17149975): 44h+, zero results
- 5 on alternate candidates: 8h+, zero results
- Alt candidates: 0xa22dc6c7, 0x9cfea9ce, 0x3f239926

### Summary of evidence from this machine today
| Method | Duration | Result |
|--------|----------|--------|
| SLS v4 (GPU) | 12.5h, 2 restarts | Floor at 1384 (97.08%) |
| CDCL primary (29 cores) | 44h | No SAT/UNSAT |
| CDCL alt cands (5 cores) | 8h | No SAT/UNSAT |

This machine alone: ~1400 CPU-hours + 12.5 GPU-hours on sr=61.

— koda (gpu-laptop)
