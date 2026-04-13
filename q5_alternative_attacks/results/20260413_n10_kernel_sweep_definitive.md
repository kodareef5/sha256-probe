# N=10 Kernel Sweep — Definitive Results (Multi-Candidate)

Date: 2026-04-13 01:00 UTC
Device: RTX 4070, torch.compile cascade DP, 2.8-4.0B eval/s

## Best collision count per kernel bit

| Bit | Best M[0] | Fill | Best Coll | #Candidates | 1st-found | Improvement |
|-----|---------|------|----------|------------|-----------|-------------|
| 0 | 0xa5 | 0x3ff | 1098 | 1 | 1098 | 1.0x |
| 1 | 0x1b2 | 0x3ff | 957 | 1 | 957 | 1.0x |
| 2 | 0x84 | 0x3ff | 604 | 1 | 604 | 1.0x |
| 3 | 0x63 | 0x3ff | 1316 | 3 | **1316** | 1.0x |
| 4 | 0x27 | 0x55 | 923 | 1 | 923 | 1.0x |
| 5 | 0x3d5 | 0x1ff | 884 | 1 | 884 | 1.0x |
| 6 | 0x11 | 0x3ff | 1064 | 1 | 1064 | 1.0x |
| 7 | 0x1a2 | 0x3ff | **1443** | 4 | **1443** | 1.0x |
| **8** | **0xf0** | **0x0** | **1467** | 6 | 1226 | **1.20x** |
| 9 | 0x34c | 0x3ff | 946 | 1 | 946 | 1.0x |

## Definitive winner: Bit 8 (1467 collisions)

Bit 8 (delta = 2^8 = 0x100) with M[0]=0xf0, fill=0x0 gives 1467 collisions.
This was NOT the first-found candidate (0x345/0x3ff gave only 1226).

## Bit 8 detail (all 6 candidates)

| M[0] | Fill | Collisions |
|------|------|-----------|
| 0x345 | 0x3ff | 1226 |
| **0xf0** | **0x0** | **1467** |
| 0x12d | 0x0 | 758 |
| ? | 0x0 | 623 |
| ? | 0x1ff | 688 |
| ? | 0x1ff | 577 |

## Bit 7 detail (all 4 candidates)

| M[0] | Fill | Collisions |
|------|------|-----------|
| **0x1a2** | **0x3ff** | **1443** |
| ? | ? | 1001 |
| ? | ? | 780 |
| ? | ? | 732 |

## Optimal kernel evolution (with multi-candidate)

| N | Best bit | Best coll | MSB coll | Improvement |
|---|---------|----------|---------|-------------|
| 4 | 1 | 146 | 49 | 3.0x |
| 6 | 4 | 83 | 50 | 1.7x |
| 8 | 6 | 1644 | 260 | 6.3x |
| **10** | **8** | **1467** | **946** | **1.55x** |

## Key observations

1. The improvement from kernel optimization DECREASES with N: 6.3x→1.55x
2. At N=10, most bits give similar counts (~900-1450), unlike N=8 (10-1644)
3. The bit-6 dominance at N=8 does NOT persist at N=10
4. Multi-candidate sweep changed the winner (bit 7→bit 8)
5. The fill pattern matters: bit 8's best uses fill=0x0 (not 0x3ff)
