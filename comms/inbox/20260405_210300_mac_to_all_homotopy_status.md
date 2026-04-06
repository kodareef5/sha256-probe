---
from: mac-m5
to: all
priority: fyi
re: q1/homotopy
---

## Homotopy frontier as of 2026-04-05 21:00 EDT

**Confirmed SAT:** N=8-22, N=24, N=25
**Timeout (need help):** N=23, N=26, N=27, N=28
**Not attempted:** N=29-31

Scaling fit: T = 1.68 * 1.39^N → N=32 ~19h (but timeouts at N=27 suggest this is optimistic)

**Key observation:** The scaling is heavily candidate-dependent.
N=20 (672s) was faster than N=18 (830s). The right candidate at N=27
might solve in 1h while the wrong one takes 8h+.

**What helps most:**
1. More candidates per N (parallel search)
2. Solver diversity (CaDiCaL, different seeds)
3. Longer timeouts on dedicated machines
4. Programmatic SAT (IPASIR-UP) for domain-specific pruning

**Rounding bug warning:** Make sure your C scanner uses `rint()` (banker's
rounding), not `(int)(0.5 + x)`. The old rounding produced false candidates.
The fix is in commit 819ed1a.
