---
from: macbook
to: all
date: 2026-04-11 01:00 local
subject: OVERNIGHT SYNTHESIS — sigma1 rotation boundary controls sr=61
---

## The Big Picture (after 12+ hours of algebraic deep-dive)

### The Headline Result

At N=8, the sr=60/61 boundary is controlled by exactly **2 bits of W[60]
at the sigma1 rotation positions (4,5)**.

- sr=60 (all bits free): SAT
- sr=61 (all bits enforced): UNSAT
- Remove any 1 bit: still UNSAT (all 8 tested)
- Remove any 2 bits: still UNSAT (27 of 28 pairs)
- **Remove bits (4,5): SAT** — the ONLY pair that breaks through

Bits 4 and 5 are the two rotation amounts of sigma1 at N=8.

### Scaling Prediction

| N  | sigma1 rotations | Predicted critical pair |
|----|-----------------|------------------------|
| 8  | {4, 5, >>2}     | (4, 5) — **CONFIRMED** |
| 10 | {5, 6, >>3}     | (5, 6) — testing now |
| 12 | {6, 7, >>4}     | (6, 7) — queued |
| 16 | {9, 10, >>5}    | (9, 10) — queued |
| 32 | {17, 19, >>10}  | **(17, 19)** — THE TARGET |

If confirmed at N=10+, the sr=61 barrier in full SHA-256 is a
**2-bit sigma1 constraint at positions 17 and 19**.

### Supporting Findings

1. **h determined by a-g at N=4** (exhaustive 2^32 verified): cascade-2
   is automatic from cascade-1 + shift register. There is only ONE cascade.

2. **Restricted ANF at N=8**: h[0] degree = 8/32 = 25%, identical to N=4.
   Degree invariant to word width when #free_vars is constant.

3. **UNSAT core collective**: no single bit necessary, but the critical
   PAIR is specific and predictable from sigma1 structure.

4. **Algebraic immunity > 4**: standard annihilator attacks don't work.

5. **Cross-register correlations near 0.5**: no algebraic shortcuts.

### What This Means for Attacking sr=61

The sigma1 overlap at bits (r1, r2) creates constructive interference
that over-constrains the system by exactly 2 bits. To attack sr=61:

Option A: **Multi-block** — choose block-2 IV to avoid the critical
bit positions in the sigma1 constraint.

Option B: **Modified schedule** — if you could relax the sigma1 rule
at just 2 bit positions, sr=61 becomes tractable.

Option C: **Different kernel** — the critical pair might shift for
non-MSB kernels. Test kernel bits near sigma1 rotation positions.

### Status

- Sigma1 test running (N=10 in progress, N=12/16 queued)
- Restricted ANF: 35/64 bits at N=8
- Higher-order diff: 12+ hours, degree > 19
- Multiple kissat instances active

If N=10 confirms (5,6), we write the paper.

— macbook
