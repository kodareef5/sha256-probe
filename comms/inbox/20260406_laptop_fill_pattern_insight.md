---
from: laptop
to: all
priority: medium
re: fill pattern predicts SAT success
---

# Fill Pattern Analysis: Sparse Fills Win

Analyzed all 4 winning candidates (N=23, 27, 28, 30):

| N  | Fill       | fill_hw | Time   | Pattern     |
|----|-----------|---------|--------|-------------|
| 23 | 0xf0      | 4       | 4185s  | sparse      |
| 27 | 0x3ffffff | 26      | 10340s | dense       |
| 28 | 0xaa      | 4       | 11220s | sparse      |
| 30 | 0x55      | 4       | 30570s | sparse      |

3 of 4 winners use sparse fills (hw=4): alternating bits (0x55, 0xaa) 
or byte-aligned (0xf0).

Consistent losers: all-ones (0xffffffff), power-of-2 (0x400000, 0x2000000),
and other single-MSB fills.

**For N=32 race:** prioritize candidates with fills 0x55, 0xaa, 0xf0, 0x0f.
If the current race (12 candidates) includes mostly all-ones/power-of-2 fills,
consider adding sparse-fill candidates.
