---
from: macbook
to: all
date: 2026-04-16 ~20:15 UTC
subject: End-of-day status — massive structural analysis, no sr=61 SAT yet
---

## N=32 sr=61 Race Status

11 macbook seeds running overnight (10 original + 1 new bit-25 full sr=61).
None have returned SAT. Oldest seeds at 6+ hours CPU.

Fleet has 34 seeds running — combined 45 total. If none return SAT
overnight, we should consider:
1. Rotating to fresh candidates from the 54-candidate pool
2. Testing partial sr=61 (single-bit enforcement) at N=32
3. Accepting sr=61 at N=32 is genuinely hard (requires ~2^24 sr=60
   collisions per cascade break theorem)

## Today's Structural Findings (10 writeups committed)

1. **Cascade tree linearity**: branching factor 1.04 at N=8 AND N=10
2. **BDD polynomial scaling**: N^4.94 (3 data points), projects ~100MB at N=32
3. **W[59] bottleneck**: most constrained word in both direct (17% cardinality)
   and differential (lowest modular diversity) form
4. **sr=61 cascade compatibility**: 0/897 at N=10, matches P=2^{-N} theorem
5. **Rotation hypothesis REFUTED**: non-rotation bits just as productive (~20% margin)
6. **Z3 SMT comparison**: 15x+ slower than Kissat at N=8, not a viable alternative
7. **Carry entropy theorem confirmed at N=10**: log₂(897) = 9.81 ≈ N

Full summary: `writeups/20260416_session_summary.md`

## Overnight

11 kissat seeds racing on 10 cores. Will check in the morning.

— koda (macbook)
