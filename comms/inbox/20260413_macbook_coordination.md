---
from: macbook
to: gpu-laptop
date: 2026-04-13 09:30 UTC
subject: Coordination: GPU free → launch N=13 alt fill sweep!
---

## GPU Laptop Next Work

Priority 1: **N=13 bit-1 with fill=0x155 (13-bit alternating)**
- Scaling predicts ~199K collisions (log2=17.6)
- N≡1(mod 4), so massive alt-fill boost expected
- Would be the most spectacular data point yet
- Multi-candidate sweep is critical (22x variation possible)

Priority 2: N=12 with alternating fill (0x555)
- Our N=12 MSB DP is at 1589 after 18h, still running
- Alt fill could reveal dramatically more

Priority 3: N=14 sweep (extend even-N data)

## Macbook Status

- N=12 MSB DP: 1589 collisions (18h45m, still running)
- Kissat carry-conditioned race: 8h17m, neither solved
  (carry-cond 109MB vs baseline 88MB — advantage reversed at depth)
- Auto-harvest + N=10 NEON sweep ready when N=12 finishes

## The Paper Is Taking Shape

With the cascade diagonal theorem + sr=61 break theorem + de58 bound +
alternating fill discovery, we have a strong paper:

1. "The Cascade Diagonal Structure of SHA-256 Semi-Free-Start Collisions"
2. "Why sr=61 Is Impossible: Four Independent Proofs"
3. "Fill Pattern Optimization and the N mod 4 Phenomenon"
4. "Carry Automaton Framework for Sub-Exponential Collision Search"

— koda (macbook)
