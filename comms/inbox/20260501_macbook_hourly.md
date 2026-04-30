---
date: 2026-05-01
machine: macbook
status: hourly log (append-only)
---

# 2026-05-01 macbook hourly log

## ~10:15 EDT — F382 cross-cand Tseitin XOR analysis: fill-bit-31 axis distinguishes structural ladder

Continued F381's deliverable #5 unblock. Extended LRAT-proof analysis from
bit31 to bit11 + bit2 (~60s additional cadical compute). Result: **fill-bit-31
axis distinguishes 2 structural classes in cadical's CDCL proofs**:

  fill-bit-31=1 (bit31, bit2): regular aux-dW57 XOR ladder
    (aux_i, dW57_a, dW57_a+2) triples in EVEN polarity, step-5 in
    dW57 var dimension; 63-65 such triples per cand
  fill-bit-31=0 (bit11): scattered XOR triples, mixed polarity,
    only 26 dW57-touching triples

**Different axis from F377**: F377 found W57[22:23] forbidden polarity is
kbit-dependent. F382 finds aux-dW57 XOR ladder is fill-bit-31-dependent.
Both real structural axes; both contribute independently to cascade-aux
proof shape.

For Phase 2D propagator + F343 preflight: the regular ladder pre-injection
on fill-bit-31=1 cands could deliver ~+0.9% additive on top of F343's
−9.10%. For fill-bit-31=0 cands the ladder isn't there; F343 preflight
remains the right intervention.

This is real progress on user direction's "generalized learned clause" unit:
not a single universal clause but a **structural CLASS** that generalizes
across fill-bit-31=1 cands. The classification is more valuable than any
individual clause — it tells the propagator HOW to mine per-cand.

Shipped:
  - `bets/cascade_aux_encoding/results/20260501_F382_xor_ladder_cross_cand.md`
  - 2 cadical 30s runs logged via append_run.py
  - dashboard.md refreshed

Open: F382 (a) confirm with bit13_m4d9f691c (fill=55555555, bit-31=0)
to nail down the fill axis. ~1 min total. Sub-30-min routine for next
session.

`validate_registry.py`: 0 errors, 0 warnings.
