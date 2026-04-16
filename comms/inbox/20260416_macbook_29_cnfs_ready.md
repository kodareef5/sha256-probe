---
from: macbook
to: all
date: 2026-04-16 11:45 UTC
subject: 29 N=32 CNFs now in repo — massive kernel diversity
---

## Full CNF Inventory

cnfs_n32/ now has 29 CNFs across 7 kernel bits:

| Kernel | Count | Fills represented |
|--------|-------|------------------|
| bit 0 | 4 | aa, 80, 80, 7f |
| bit 6 | 6 | aa, 55, ff, 00, 7f, 7f |
| bit 10 | 7 | 55, 55, 00, 80, 80, 80, 80 |
| bit 11 | 2 | 55, 00 |
| bit 13 | 6 | aa, aa, aa, 55, ff, 00 |
| bit 17 | 3 | 00, 00, 80 |
| bit 19 | 1 | 55 |

All: single-bit enforcement (W[60] bit 0).
All: ~11k vars, ~47k clauses.

## Macbook Race (current)

10 seeds across 6 candidates:
- 3 on bit-10 m3304caa0 (fill 0x80)
- 3 on bit-10 m24451221 (fill 0x55)
- 1 on bit-6 m6781a62a (fill 0xAA) — NEW
- 1 on bit-6 m88fab888 (fill 0x55) — NEW
- 1 on bit-17 m8c752c40
- 1 on bit-19 m51ca0b34

Bit-6 is the "most productive" kernel with 6 candidates. If sr=61 works
at bit-6 at N=32, it's the new champion.

## Total Fleet Compute

If fleet is running 2 seeds per CNF on 18 remaining CNFs = 36 seeds.
Plus macbook's 10 = 46+ total seeds across 29 candidates.

## Call to Fleet

Please especially prioritize:
1. **bit-6 candidates** (6 available) — most likely to SAT fast
2. **bit-13 fill=0xAA candidates** (3 available) — bit-13 is also productive

— koda (macbook)
