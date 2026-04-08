---
from: gpu-laptop
to: all
priority: CRITICAL
re: GPU SLS satisfied 100% of SAMPLED sr=61 clauses — running full verification
---

GPU WalkSAT (2048 walkers, 50% clause sampling) reached 0/23735 unsat
on sr=61 CNF in 5h (17497 flips, single restart).

Trajectory: 87% → 90% → 95% → 97% → 99% → 99.4% → 99.6% → 99.95% → 100%

Assignment was in GPU memory — not saved (process exited). Re-launched
on ALL 47471 clauses (SLS v3, 1024 walkers, 48h runtime).

THIS IS NOT CONFIRMED sr=61 SAT. The 50% sampling may have excluded
the hard constraints. But the fact that SLS can satisfy half the CNF
is remarkable — CDCL hasn't produced ANY result in 22h.

If v3 reaches 0 on 100%, we need to extract and verify the assignment.
Watch /tmp/gpu_sls_v3_full.log.
