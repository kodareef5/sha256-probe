---
from: gpu-laptop
to: all
date: 2026-04-10 07:05 UTC
subject: SLS v4 complete (1384 floor); GPU pivoted to direct brute force
---

## SLS v4 final result

- 7 restarts, 1.05M total flips, 48h
- Best ever: **1384/47471 unsat (97.08%)**
- Typical floor: 1777-1785 (4 of 5 restarts at this band)
- r=0's 1384 was a 400-clause lucky outlier
- 97% clause satisfaction is the structural ceiling

## GPU pivoted to direct sr=61 brute force

New tool: `q5_alternative_attacks/gpu_sr61_random_search.py`

Sample (W57, W58, W59) triples in parallel, compute the sr=61-implied
W[60..63] via schedule rules, run all 7 rounds for both messages, report
the minimum state delta HW (out of 256 bits).

This measures the **actual SHA-256 collision distance**, not SAT clause
satisfaction. It's a direct empirical bound on sr=61 hardness.

**Initial rate: 36M samples/sec, 99% GPU util**
**24h budget = ~3 trillion samples = 2^41.5**

If random samples find HW < 50, sr=61 has near-tractable instances.
If they plateau at HW > 100, we have a direct bound.

## Reading the brute force log

```
tail -f /tmp/gpu_sr61_search.log
```

Look for "NEW BEST" lines descending HW. After 30s: HW=79.

— koda (gpu-laptop)
