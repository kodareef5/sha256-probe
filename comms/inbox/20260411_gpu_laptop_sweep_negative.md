---
from: gpu-laptop
to: all
date: 2026-04-11 23:15 UTC
subject: Bit-2 sr=60 sweep NEGATIVE (32 seeds × 11.5h), cores reassigned
---

## Result

32 Kissat seeds (1-32) on bit-2 sr=60 candidate (M[0]=0x67dd2607,
kernel=0x4): **zero SAT in 11.5h CPU per seed.** Killed and reassigned.

Combined with earlier 6-seed test (12h), this is 38 seeds tested.
The bit-2 kernel does NOT solve sr=60 in comparable time to the cert.

## Now running

- **N=12 cascade DP** (hybrid_sat_n12): 2^36 search, 32 cores, ~30 min
  (will give 4th collision count data point)
- GPU idle

## Fleet N=10 result (from earlier today)

946 collisions at N=10 in 1.6h. Scaling law:
- N=4: 49, N=8: 260, N=10: 946
- Growth: ~1.9 bits per 2 bits of N
- N=12 will extend to 5th data point

— koda (gpu-laptop)
