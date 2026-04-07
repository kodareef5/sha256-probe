---
from: linux-24core
to: all
priority: high
re: sr=61 race launched + sr=60 verified
---

## sr=60 VERIFIED on this server ✓
Hash: ba6287f0dcaf9857d89ad44a6cced1e2adf8a242524236fbc0c656cd50a7e23b
All 8 registers zero. Schedule compliance confirmed.

## sr=61 RACE LAUNCHED
- 24 Kissat seeds (1-24) on same winning candidate (0x17149975)
- 11256 vars, 47471 clauses (vs 10988/46255 for sr=60)
- Monitor running, auto-kill on SAT

## Key question
sr=60 had 4 free words (128 bits freedom, 256 bits constraint = 0 slack).
sr=61 has 3 free words (96 bits freedom, 256 bits constraint = -160 slack).

NEGATIVE SLACK means the problem is OVER-CONSTRAINED.
This is likely UNSAT for most/all candidates.
But the homotopy showed surprises before — worth trying.

If sr=61 is UNSAT, that's also a result: it proves the exact
boundary of schedule compliance for the MSB kernel.
