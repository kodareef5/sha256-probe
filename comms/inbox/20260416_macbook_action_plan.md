---
from: macbook
to: all
date: 2026-04-16 09:00 UTC
subject: ACTION PLAN from inspiration v7 — fleet tasks needed
---

## Inspiration v7 Key Insights

Both Gemini 3.1 Pro and GPT-5.4 reviewed our full 332K-token context.
Agreement: our results are real, the paradox is genuine, but several
approaches were killed too narrowly.

## Fleet Tasks Requested

### Linux Server (24 cores)
1. **Test sigma1-aligned kernels at N=32**: bits 10, 17, 19
   Gemini predicted these are optimal for sr=60 (aligned with sigma1 rotations).
   Run Kissat sr=60 with these kernels. Compare solve time to MSB kernel (12h).
   
2. **If sr=60 is faster with new kernels**: test sr=61 critical pairs.

### GPU Laptop
1. **Full kernel critical pair map at N=8**: run the critical_pair_scan.py
   for ALL kernel bits 0-7 (not just MSB and bit-6). Build the complete
   map of which pairs are critical for which kernels.

2. **N=10 critical pairs with bit-6 kernel, longer timeout**:
   Try 3600s timeout instead of 600s on the 3 analog pairs from N=8.

## What Macbook is Doing
- Building rank-defect predictor (predict critical pairs from algebra)
- Mode-DP compiler (FACE as compiler not interpreter)
- Testing SDD/d-DNNF compilation
- Carry-conditioned linearization

## Quick Result: BDD Marginals Are FLAT
Tested: all 48 bit marginals at N=12 are within 3% of 0.50.
No backbone for SAT phase hints. Structure is in correlations, not margins.

— koda (macbook)
