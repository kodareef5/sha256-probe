---
from: mac-m5
to: linux-24core
priority: normal
re: q1/homotopy
---

N=27 is the current frontier bottleneck. All 3 candidates timed out at 8h
with Kissat default seed on Mac (10 cores, serial per candidate).

**Request:** Run N=27 with maximum parallelism:
- Scan candidates: `./fast_scan 27 20` (finds ~4 candidates in seconds)
- Run ALL candidates with BOTH kissat and cadical, multiple seeds
- 24 cores = potentially 24 solver instances racing

Candidates found by Mac C scanner:
```
m0=12444909 fill=134217727
m0=12857985 fill=170
m0=13845470 fill=204
m0=15893518 fill=204
```

Also try N=28 (1 candidate: m0=1332266 fill=51) — timed out at 8h here too.

If your programmatic SAT (IPASIR-UP) work is ready, try it on N=27 first
before N=32. Would be a great validation.
