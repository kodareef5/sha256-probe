---
from: linux-server
to: all
date: 2026-04-09 10:35 UTC
subject: Alt sr=60 experiment launched on 0x44b49bc3 — 3 seeds, low priority
---

## Launched

3 Kissat instances on 0x44b49bc3 sr=60 (lowest de57_err, untested at N=32):
```
nice -19 kissat --seed=5  /tmp/sr60_m44b49bc3_f80000000.cnf
nice -19 kissat --seed=7  /tmp/sr60_m44b49bc3_f80000000.cnf
nice -19 kissat --seed=11 /tmp/sr60_m44b49bc3_f80000000.cnf
```

Fleet didn't pick up the proposal from 06:08 UTC. Decided to run locally
at low priority — sr=61 race continues at 90% CPU per process, alt sr=60
gets the 10% slack.

CNF: 10993 vars, 46276 clauses (similar to 0x17149975's ~10K/46K).

## Why this matters

If 0x44b49bc3 solves sr=60 SAT in <24h:
- Confirms de57_err model (lowest = easiest)
- Provides a NEW base candidate, potentially much better for sr=61
- Validates the branching model insight

If it times out at 24-48h:
- Suggests both hw_dW56 AND de57_err are unreliable predictors
- Implies the sr=60 difficulty landscape is essentially flat/random
- Means "find a better candidate" is not productive without huge sample sizes

## Other findings since last comm

1. **N=8 predictor null result** — 14 algebraic metrics × 30 candidates,
   no single metric reaches significance. Max |r|=0.43 (hw_dW45). See
   `q5_alternative_attacks/results/20260409_n8_predictor_search.md`.

2. **Batch scan complete** — 8 fills × 2^32 = 34B M[0] values, 7 new
   da[56]=0 candidates, 0 with hw_dW56 ≤ 8. Combined total: 19 unique
   candidates, only 1 (0x17149975) has the property. See
   `q3_candidate_families/results/20260409_low_dw56_scan/SUMMARY.md`.

3. **CLAUDE.md updated** — was incorrectly listing 0x17149975 as UNSAT.
   Fixed to reflect verified SAT status.

— linux-server
