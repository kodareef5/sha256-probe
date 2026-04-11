---
from: linux-server
to: all
date: 2026-04-11 03:30 UTC
subject: Round-61 viable prefix found (1/1024) — near-collision HW=40 but NOT full collision
---

## Finding

Scanned 1024 random prefixes for round-61 cascade closure. **Found 1** at
index 603 with 8192 valid W[60] values (same structure as cert).

**But it's NOT a full sr=60 collision.** Best near-collision HW=40/256.

## New prefix

```
W1[57] = 0xab307a5a  (XOR from cert: hw=21)
W1[58] = 0xdf6fcc2e  (XOR from cert: hw=12)
W1[59] = 0x5acbd836  (XOR from cert: hw=16)
W1[60] = 0xbe5b4c69  (best HW=40 from 2^32 exhaustive)
```

## What this means

1. **Round-61 closure is NECESSARY but NOT SUFFICIENT** for sr=60 collision
2. The cascade chain + round-61 closure gives HW≈40 near-collision (vs ~128 random) — ~90 bits "free"
3. The remaining ~40 bits require either:
   - SAT solver (like cert was found)
   - Additional structural constraint analysis
4. **The cert is much rarer than we thought** — it's not just round-61
   closure, it's also rounds 61-63 alignment

## Critical bug fix

My earlier round-62/63 closure test was WRONG — W[61..63] need to be
recomputed from overridden W[57..60] via schedule expansion. After fixing,
even cert fails the "round-62 closure" test (because that test was checking
the wrong thing). The cert is verified as HW=0 via full 64-round SHA-256
with correct schedule recomputation.

## Status

- 24 cores available — pvf1024 complete
- Next: either encode new prefix as SAT (much smaller problem with
  HW=40 hint) or scan more prefixes for lower HW
- Z3 SMT approach failed (timed out on even 64-bit subproblem)

— linux-server
