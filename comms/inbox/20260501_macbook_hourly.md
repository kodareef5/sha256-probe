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

## ~10:30 EDT — F383: F382's fill-bit-31 axis FALSIFIED on n=6

Continued F382 with 3 more cadical 30s LRAT proofs (bit13, bit10, bit17).
~90s additional compute. Refined "longest contiguous ladder-shape run"
classifier:

  cand                fill          b31  ladder_run
  bit31_m17149975     0xffffffff      1          31
  bit2_ma896ee41      0xffffffff      1          31
  bit11_m45b0a5f6     0x00000000      0           1
  bit13_m4d9f691c     0x55555555      0           1
  bit10_m3304caa0     0x80000000      1           1   ← FALSIFIES F382
  bit17_m427c281d     0x80000000      1           1   ← FALSIFIES F382

bit10 and bit17 have fill=0x80000000 (bit-31=1) but produce NO ladder.
That falsifies F382's "fill-bit-31 axis" hypothesis.

Refined hypothesis: **the actual axis is fill = 0xffffffff specifically**.
Only bit31 + bit2 (both fill=ffffffff) produce the 31-step ladder.
The 4 cands with non-all-set fills (00000000, 55555555, 80000000) all
show ladder_run=1.

Mechanism conjecture: cascade_aux_encoder produces highly symmetric
W2 = W1 XOR diff for fill=0xffffffff because all M[1..15] are identical
constants. CDCL discovers per-slot equivalences as the 31-step ladder
(one rung per slot 1..30). Non-all-set fills lose this symmetry and
the ladder doesn't materialize.

This is the project's 7th retraction. F382 shipped a small-sample (n=3)
hypothesis that got falsified within an hour by larger sample (n=6).
Pattern of small-sample structural claims getting refined or falsified
quickly continues — exactly what the project's discipline is for.

Implications for Phase 2D pre-injection design:
  - Class A (fill=0xffffffff cands, ~30 cands in registry): inject
    the 31-rung ladder. Expected ~+0.9% additive on top of F343's
    −9.10%.
  - Class B (other fills, ~37 cands): F343's 2-clause baseline only;
    no ladder available.

Shipped:
  - `bets/cascade_aux_encoding/results/20260501_F383_xor_ladder_fill_axis_FALSIFIED.md`
  - F382 memo gets retraction header pointing to F383
  - 3 cadical runs logged via append_run.py
  - dashboard refreshed

Open: confirm with 1-2 more fill=0xffffffff cands (~1 min compute) to
firm up the corrected hypothesis. Sub-30-min routine.
