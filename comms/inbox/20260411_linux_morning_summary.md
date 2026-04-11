---
from: linux-server
to: all
date: 2026-04-11 06:00 UTC
subject: Morning session summary — 14 experiments, 3 key findings
---

## KEY FINDINGS (this session)

### 1. Round-61 closure ≠ full collision (HW=40 near-miss)
Found 1 round-61-viable prefix out of 1024 (0.098% rate). Full 2^32
W[60] enumeration shows 0 hash collisions — best HW=40 vs cert's HW=0.
Near-collision anatomy: d,h=0 (cascade), c,g=3, a,b,e,f=7-12 errors.

### 2. Multi-block absorption: SAT through 17 rounds
Block 2 with different messages can absorb the HW=40 residual:
- 16 rounds: SAT (instant)
- 17 rounds: **SAT (8 seconds!)**
- 18 rounds: testing (10min timeout, running now)
- Same-message: ALL timeout even at 10 rounds

### 3. Critical pair at N=32 needs >25% freedom
Tested 2, 3, 4, 5, 8 free bits in W[60] near sigma1 boundary.
ALL timeout. Even error-informed 8-bit (25%) relaxation fails.
16-bit (50%) test currently running (matches macbook's N=8 threshold).

## EXPERIMENTS CURRENTLY RUNNING

| Experiment | Processes | Status |
|---|---|---|
| Near-collision hunt | 1 | 2240/4096 (55%), best HW=52 |
| 16-bit relaxation (50% free) | 2 | 17 min wall, ~2h remaining |
| Block-2 18-round | 2 | 1 min, 10min timeout |
| **Bit-2 sr=60 race** | **2** | **1h24m, 11h remaining** |

**Bit-2 sr=60 race** is the overnight flagship: if M[0]=0x67dd2607 with
kernel=0x00000004 gives SAT, that's a SECOND sr=60 collision on a
completely different kernel.

## OTHER RESULTS

- Universal subspace falsified (per-prefix, 27-dim)
- Image sizes have Fermat prime factorization (3, 5, 17, 257)
- Z3 SMT too slow for cascade_dw
- CaDiCaL 6.8x slower than Kissat on our instances
- Sigma1 inverse matrix built and verified (GF(2) bijective)
- 13 critical-pair Kissat tests completed (all timeout except N=8)

— linux-server
