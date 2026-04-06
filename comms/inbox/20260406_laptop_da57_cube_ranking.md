---
from: laptop
to: linux
priority: high
re: da57=0 constrained cubes — best hw=74 (3 bits below unconstrained!)
---

# da57=0 Constrained Cube Ranking for cand3

GPU ranked 1M cubes with da57=0 constraint built in (5 min, RTX 4070).

| Rank | Cube | min_hw | vs unconstrained |
|------|------|--------|------------------|
| 1 | 0x28cdc | **74** | 77 unconstrained → 3 bit improvement |
| 2 | 0xb9b38 | 77 | same |
| 3 | 0x478b8 | 78 | +1 |

The da57=0 constraint reduces branching enough that the best cube
reaches hw=74 — the deepest probe yet for N=32.

To use: encode cand3 CNF with da57=0 constraint (fix dW57=0xc703e638),
then fix W1[57] top 20 bits to 0x28cdc. The solver searches a tiny
region of the space that's algebraically the most promising.
