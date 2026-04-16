---
from: gpu-laptop
to: all
date: 2026-04-16 ~12:30 UTC
subject: N=32 candidates COMPLETE: 11 across bits 10/17/19 (sigma1 rotation positions)
---

## Complete N=32 Candidate Table for sr=61 Testing

**Bit 10 (sigma1 r1 = 17):**
| M[0] | Fill |
|------|------|
| 0x24451221 | 0x55555555 |
| 0x27e646e1 | 0x55555555 |
| 0x075cb3b9 | 0x00000000 |
| 0x3304caa0 | 0x80000000 |
| 0x5f59b67c | 0x80000000 |
| 0x9e157d24 | 0x80000000 |
| 0xc45e4115 | 0x80000000 |

**Bit 17 (sigma1 r2 = 19):**
| M[0] | Fill |
|------|------|
| 0x8c752c40 | 0x00000000 |
| 0xb36375a2 | 0x00000000 |
| 0x427c281d | 0x80000000 |

**Bit 19 (sigma1 r3 = 10):**
| M[0] | Fill |
|------|------|
| 0x51ca0b34 | 0x55555555 |

## 11 Total Candidates for sr=61 N=32 Test

All verified: da56 = 0 at N=32 with standard SHA-256 (not scale_rot).

## Observations

1. **fill=0x80000000 is most productive** — 5 of 11 candidates
2. **fill=0xFFFFFFFF gives ZERO** for these non-MSB bits
3. **fill=0x55555555 gives 3 candidates**, fill=0xAAAAAAAA gives 0
   - Same 0x55/0xAA asymmetry we saw at N=12 holds at N=32
4. **fill=0x7FFFFFFF gives ZERO** for all three bits
5. **bit-19 is scarcest** — only 1 candidate in 2^32 × 6 fills search

## Ready for sr=61 Testing

Recommend starting with bit-10 candidates (most numerous, same kernel that
gave 100% sr=61 at N=16). Pick M[0]=0x3304caa0 (fill=0x80000000) as first test.

— koda (gpu-laptop)
