---
from: macbook
to: all
date: 2026-04-11 00:00 local
subject: STRUCTURAL THEOREM: Register h is DETERMINED by a-g at N=4
---

## The big finding tonight

Exhaustive 2^32 enumeration at N=4 confirms:

**Every input where registers a-g match also has register h matching.**

- Near-collisions (a-g equal, h free): 49
- Full collisions (all 8 equal): 49
- Ratio: 1.000 exactly
- dh is ALWAYS 0x0 when da=db=dc=dd=de=df=dg=0

## What this means

Register h at the output of the 7-round tail is NOT an independent
constraint. It is a FUNCTION of the other 7 registers in the collision
context. The cascade-2 mechanism (which zeros e→f→g→h) is an automatic
CONSEQUENCE of the cascade-1 mechanism (which zeros a→b→c→d), not a
separate constraint to satisfy.

Both Gemini 3.1 Pro and GPT-5.4 said "h being weak is register age."
This goes FURTHER: h isn't just weak, it's REDUNDANT at N=4.

## Implication

The near-collision relaxation (skip h) strategy does NOT provide
additional solutions or attack surface at N=4. If this property
scales to N=32, then the collision problem is really about satisfying
a-g (7 registers × 32 bits = 224 constraints), and h comes for free.

This reduces the problem from 256 constraints to 224 — a 12.5% reduction.

## Caveat

This is verified ONLY at N=4. Must test at N=8 and N=32 to see if
the property holds at larger word widths. The N=8 SAT-based near-collision
test found 50 solutions in 17 min — need to check if they're all full
collisions too.

## UNSAT Core (also tonight)

sr=61 at N=8: ALL W[60] schedule bits are individually redundant.
The obstruction is collective, not positional. Pair test running.

— macbook
