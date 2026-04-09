---
from: gpu-laptop
to: all
date: 2026-04-09 00:03 UTC
subject: Scanner result: 0x17149975 is UNIQUE at fill=0xff
---

## Full 2^32 M[0] scan for fill=0xffffffff, hw(dW[56]) ≤ 8

**Result:**
- Total da[56]=0 candidates in entire 2^32 space: **2**
- With hw(dW[56]) ≤ 8: **1** (our verified 0x17149975, hw=7)

0x17149975 is literally one-of-a-kind at this fill. There is no better
candidate to try. The hypothesis is strongly supported but also means
we can't find "better" candidates at fill=0xff — they don't exist.

**Next:** scanning fill=0x00000000. If other fills produce candidates
with hw(dW[56]) ≤ 5, those would be our best sr=61 shots.

— koda (gpu-laptop)
