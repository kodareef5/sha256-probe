# N=10 All-Candidates NEON Kernel Sweep — COMPLETE

Runtime: 538 min (9h) on 8 NEON threads

## Final Results (best per bit)

| Bit | Best | Fill | M[0] | vs 1st-found |
|-----|------|------|------|-------------|
| 0 | 1098 | 0x3ff | 0x0a5 | 1.0x |
| 1 | 1574 | 0x55 | 0x0f0 | 1.6x |
| 2 | 1474 | 0x55 | 0x061 | 2.4x |
| 3 | 1316 | 0x3ff | 0x063 | 1.0x |
| 4 | 923 | 0x55 | 0x027 | 1.0x |
| 5 | 1197 | 0xaa | 0x1f5 | 1.35x |
| 6 | 1781 | 0x55 | 0x092 | 1.67x |
| 7 | 1443 | 0x3ff | 0x1a2 | 1.0x |
| 8 | 1703 | 0x55 | 0x3e4 | 1.16x |
| **9** | **1833** | **0x1ff** | **0x19f** | **1.94x** |

## Champion: Bit 9 (MSB) = 1833 (log2 = 10.84)

The MSB kernel with fill=0x1ff and M[0]=0x19f gives 1833 collisions —
nearly 2x the first-found MSB candidate (946).

## Key Findings

1. **Candidate selection is critical**: 6/10 bits improved with multi-candidate testing
2. **fill=0x55 wins at 5 bits** (1,2,4,6,8) — alternating fill productive at N=10
3. **fill=0x1ff wins MSB** — half-fill pattern for sub-MSB-1 bit
4. **Improvement range**: 1.0x-2.4x across bits
5. **The kernel advantage is FLAT at N=10**: best/worst = 1833/923 = 2.0x (was 6.3x at N=8)

Evidence level: VERIFIED (exhaustive NEON DP, all candidates, 9h)
