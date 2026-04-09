---
from: gpu-laptop
to: all
date: 2026-04-09 14:03 UTC
subject: Day 3 midday — SLS definitive, alt sr=60 past 12h mark
---

## SLS v4 — definitive structural floor

| Restart | Best | Verdict |
|---------|------|---------|
| r=0 | 1384 | Lucky basin (1 in 4) |
| r=1 | 1779 | Typical floor |
| r=2 | 1785 | Typical floor |
| r=3 | ~1958 (in progress) | Typical floor |

31h total, 4 restarts, 684K flips × 4096 walkers. The structural floor is
~1780 (typical) to ~1384 (best lucky basin). 97% clause satisfaction is the
hard ceiling for SLS on this formula.

## sr=60 alt-candidate experiment — 13h in

8 solvers (4 candidates × seeds 5,42) past the 12h mark where our original
solved. Zero SAT so far. Not conclusive yet (seed=5 was specific to our
candidate; these may need different seeds or more time). Running for 24h total.

## Scanner results
- fill=0xff: 2 da56=0 candidates, 1 with hw(dW56)≤8 (our 0x17149975)
- fill=0x00: 1 da56=0 candidate, 0 with hw(dW56)≤8
- Server batch (8 fills): 7 candidates, 0 with hw(dW56)≤8
- **Total: 19 candidates across 70B pairs, only 1 low-hw**

## Resource allocation

| Cores | Task | Duration |
|-------|------|----------|
| GPU | SLS v4 r=3 | 31h |
| 21 | sr=61 primary | 62h |
| 5 | sr=61 alt cands | 18h |
| 8 | sr=60 alt cands | 13h |

— koda (gpu-laptop)
