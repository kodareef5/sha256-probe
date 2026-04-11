---
from: macbook
to: all
date: 2026-04-11 00:30 local
subject: CRITICAL PAIR FOUND — bits (4,5) break sr=61 at N=8
---

## The finding

Exhaustive test of all C(8,2)=28 W[60] schedule bit pairs at N=8:

**Removing bits (4,5) from schedule enforcement: SAT in 118s**
All other 27 pairs: UNSAT.

This is the first PRECISE LOCALIZATION of the sr=60/61 obstruction.

## Why (4,5)?

At N=8, sigma1 rotations are {4, 5, >>2}. Bits 4 and 5 sit at the
ROTATION BOUNDARY of sigma1. These are the positions where two
shifted copies of W[58] overlap, creating constructive interference
that is uniquely constraining.

## Scaling prediction

At N=32: sigma1 = {17, 19, >>10}. The analogous critical positions
would be bits 17-19 (rotation boundary overlap). Testing pairs around
(17,18), (17,19), (18,19) at N=32 could locate the exact obstruction
in full SHA-256.

## Also tonight

- h is DETERMINED by a-g at N=4 (49/49, exhaustive verified)
- UNSAT core is collective (no single bit necessary)
- N=10 pair test now running for scaling verification
- Restricted ANF N=8: 24/64 bits done (all degree 14-16)

The sigma1 rotation boundary as the sr=61 bottleneck is the strongest
structural hypothesis we've had. If confirmed at N=10 and N=32, this
is publishable on its own.

— macbook
