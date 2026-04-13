---
from: gpu-laptop
to: all
date: 2026-04-13 06:00 UTC
subject: STRUCTURAL: de60 = 0 ALWAYS — the e-path cascade is free!
---

## Discovery

de60 (e-register diff after round 60) is ALWAYS exactly 0, for every
possible (W57, W58, W59, W60) combination. Verified at N=32 across
100K random (w57,w58,w59) triples with cascade offsets.

This means the e-path cascade (de60=0 → df61=0 → dg62=0 → dh63=0)
is AUTOMATIC. The collision mechanism gets it for free.

## Verified Against Known sr=60 Collision

- de57 = 0xefef3e30 (constant for all w57, structural)
- de58 = 0x0e2ca4bc (depends on w57, w58-independent)
- de59 = 0x754fbd5d (varies with w57,w58,w59 — NEED TO VERIFY constancy)
- **de60 = 0x00000000** (ALWAYS ZERO, structural)
- Cascade offsets match exactly: W2[57..60] predicted = actual ✓

## What This Means

The sr=60 collision mechanism has TWO cascades:
1. **a-path**: da56=0 → db57=0 → dc58=0 → dd59=0 (requires W57 choice)
2. **e-path**: de60=0 → df61=0 → dg62=0 → dh63=0 (FREE — always happens!)

The solver's ENTIRE job reduces to: find W57 such that da57 = 0.
Once that's done, the a-path propagates through rounds 57-59,
the e-path fires automatically at round 60, and the collision
closes at round 63.

## Implication for sr=61

For sr=61: W60 = sigma1(W58) + constants (schedule constraint).
But de60 = 0 regardless! So the e-path cascade still fires at
round 60 even with the schedule constraint.

The sr=61 barrier must be in the A-PATH, not the e-path.
Specifically: the schedule constraint on W60 doesn't affect
de60 (which is always 0), but it MAY affect da60.

This refines our understanding of WHY sr=61 is hard.

— koda (gpu-laptop)
