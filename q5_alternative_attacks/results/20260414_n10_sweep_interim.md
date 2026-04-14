# N=10 NEON Kernel Sweep — Interim (all-candidates)

## New Record: Bit 1 fill=0x55 = 1574

| Bit | Fill | M[0] | Collisions | Notes |
|-----|------|------|-----------|-------|
| 0 | 0x3ff | 0x0a5 | 1098 | matches GPU laptop |
| 0 | 0x00 | 0x2a4 | 1067 | |
| 0 | 0x200 | 0x02f | 780 | |
| 1 | 0x3ff | 0x1b2 | 957 | GPU laptop 1st-found |
| 1 | 0x3ff | 0x2eb | 908 | |
| 1 | 0x200 | 0x1ec | 1245 | |
| 1 | 0x55 | 0x0ab | 1005 | |
| **1** | **0x55** | **0x0f0** | **1574** | **NEW N=10 RECORD** |
| 1 | 0x55 | 0x26e | 1227 | |

Bits 2-9 still running.

The all-candidates fix reveals hidden champions. fill=0x55 at N=10 bit 1
gives 1574 — 7% above the previous N=10 best (1467 at bit 8).

Evidence level: VERIFIED (exhaustive NEON DP, 8 threads)
