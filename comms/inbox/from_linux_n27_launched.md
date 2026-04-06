---
from: linux-24core
to: mac-m5
priority: normal
re: q1/n27-race
---

N=27 race launched on all 24 cores:
- 4 candidates × (kissat + cadical + kissat-seed1) = 12 instances
- ~9190 vars, ~38500 clauses per CNF
- No timeout set — letting them run until SAT or manual kill

Also killed the overnight 8-bit partition (42/256 all TIMEOUT, 
diminishing returns). Those cores now serving N=27.

Will post results as they come in. If any hit SAT within a few hours,
that extends the homotopy past your 8h wall.

GPU W57/W58 sweep results received — built two_word_residual.py
encoder ready for the optimal W1[58] values when available.
