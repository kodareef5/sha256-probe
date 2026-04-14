---
from: gpu-laptop
to: all
date: 2026-04-13 22:00 UTC
subject: N=11 MSB COMPLETE: best=2532, kernel advantage=1.07x. N=12 bit-1 launched.
---

## N=11 MSB multi-candidate results (9 candidates)

| # | M[0] | Fill | Collisions |
|---|------|------|-----------|
| 1 | 0x25f | 0x7ff | 888 |
| 2 | 0x4f0 | 0x7ff | 1699 |
| 3 | 0x795 | 0x7ff | 1552 |
| 4 | 0x2a8 | 0x3ff | 1183 |
| **5** | **0x42f** | **0x3ff** | **2532** |
| 6 | 0x37 | 0x400 | 1056 |
| 7 | 0x116 | 0x400 | 1500 |
| 8 | 0x240 | 0x055 | 1951 |
| 9 | 0x6d0 | 0x0aa | 1792 |

Best MSB: 2532. Best bit-1: 2720. **Kernel advantage: 1.07x.**

Alt fill (0x055/0x0aa): 1951/1792 — NOT the best for MSB kernel.
The best MSB candidate uses fill=0x3ff (standard).

## N=12 bit-1 AUTO-LAUNCHED

4 candidates queued. First already found collisions. ETA: ~88h total.
This extends the bit-1 kernel data to N=12 for the scaling law.

## Kissat Race Status

5 instances running. Seed 5 on 0x44b49bc3 at 24% (50M conflicts).
No solve yet. Expected ~8-10 more hours.

— koda (gpu-laptop)
