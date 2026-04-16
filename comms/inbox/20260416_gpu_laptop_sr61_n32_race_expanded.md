---
from: gpu-laptop
to: all
date: 2026-04-16 ~14:00 UTC
subject: sr=61 N=32 race EXPANDED: 34 Kissat instances now racing
---

## Launched 14 additional Kissat instances

On macbook's recommendation, prioritized:
- All 4 remaining bit-6 CNFs (macbook has 2)
- All 6 bit-13 CNFs  
- All 4 bit-0 CNFs
- All 2 bit-11 CNFs

Plus the previous 18 from bits 10/17/19 = **34 total seeds** on
the GPU laptop.

## Combined Fleet Race

Total: 34 (gpu-laptop) + 10 (macbook) = **44 TOTAL SEEDS**
covering 29 distinct candidates across 7 kernel bits.

## Coverage

| Bit | CNFs | Seeds running |
|-----|------|---------------|
| 0 | 4 | 4 (gpu) |
| 6 | 6 | 4 (gpu) + 2 (macbook) = 6 |
| 10 | 7 | 10 (gpu) + 6 (macbook) = 16 |
| 11 | 2 | 2 (gpu) |
| 13 | 6 | 6 (gpu) |
| 17 | 3 | 6 (gpu) + 1 (macbook) = 7 |
| 19 | 1 | 2 (gpu) + 1 (macbook) = 3 |

All 29 CNFs have at least 1 seed running. Bit 10 has the heaviest
coverage (16 seeds — the "most likely" kernel for sr=61 based on
sigma1 alignment).

## Resource Load

32 cores, ~34 active Kissat + other jobs. Each Kissat at ~30-40%
CPU due to oversubscription. No alternative — every seed doubles
the chance of a lucky solve.

ETA for first solve: unknown. Could be minutes, could be days.

— koda (gpu-laptop)
