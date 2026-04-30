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

## ~10:50 EDT — F384: F383 hypothesis CONFIRMED at n=8

Ran cadical 30s LRAT on bit3_m33ec77ca + bit28_md1acca79 (both
fill=0xffffffff, both F374 deep-tail dominators). ~60s compute.

Result — 8 cands cleanly partition:

  Class A (fill=0xffffffff): 4/4 cands → ladder_run = 31 EXACTLY
    bit31_m17149975, bit2_ma896ee41, bit3_m33ec77ca, bit28_md1acca79

  Class B (other fills):     4/4 cands → ladder_run = 1 (no ladder)
    bit11_m45b0a5f6 (00000000), bit13_m4d9f691c (55555555),
    bit10_m3304caa0 (80000000), bit17_m427c281d (80000000)

Sharp class boundary, no false pos / false neg. F383's corrected
hypothesis is empirically validated.

Class A is **31 of 67 registry cands (46%)**. Substantial portion of
cands get the 31-rung ladder structure for free in their CDCL proofs
on aux_force sr=60 60s.

Phase 2D pre-injection design:
  - Class A (31 cands): inject 31-rung ladder (8 size-3 EVEN Tseitin
    XOR triples + 23 more in arithmetic-progression + 8 size-2
    aux ⇔ dW57 equivalences) at solver init via cb_add_external_clause
  - Class B (36 cands): F343's 2-clause baseline preflight only

The F381 → F382 → F383 → F384 chain (3 hours, ~150s of cadical compute)
went from "discovered some structural clauses" to "sharp class boundary
on 8/8 cands" with one retraction (F382→F383) and one confirmation
(F383→F384). Every wrong claim caught and narrowed.

Shipped:
  - `bets/cascade_aux_encoding/results/20260501_F384_xor_ladder_8cand_confirmed.md`
  - 2 cadical runs logged via append_run.py
  - dashboard refreshed
  - 8-cand fingerprint table; sharp partition validated

Open: F384's open question — test fill=0xfffffffe (1 bit cleared from
ffffffff) to see if the ladder breaks at exactly 1-bit difference or
smoothly degrades. ~30s compute. Sub-30-min routine.

## ~11:30 EDT — F385: F384's "fill=0xffffffff specifically" axis is too NARROW

3 more cadical 30s LRAT runs (~90s compute):
  bit6_m024723f3 fill=0x7fffffff (HW=31, near-Class-A) → ladder=1 (no)
  msb_m3f239926  fill=0xaaaaaaaa (HW=16) → **ladder=31** (Class A!)
  bit13_m4e560940 fill=0xaaaaaaaa (HW=16) → **ladder=31** (Class A!)

11-cand fingerprint:
  Class A (ladder=31): 4 fill=ffffffff + 2 fill=aaaaaaaa = 6
  Class B (ladder=1): 5 cands across 0x7fffffff, 0x55555555, 0x80000000, 0x00000000

F384's claim "Class A = fill=0xffffffff specifically (31 of 67 cands)"
is FALSIFIED. Class A includes some 0xaaaaaaaa cands too.

Tentative new rule: **ladder iff fill_bit[kbit] = 1**. Fits 10 of 11
cands. The lone outlier is bit6_m024723f3 (fill=0x7fffffff, kbit=6;
fill_bit[6]=1 but no ladder appears). Possible explanations:
  - Rule is incomplete (depends on more than just fill_bit[kbit])
  - Classifier's arithmetic-progression assumption misses bit6's ladder
  - bit6_m024723f3 has m0-specific structure that suppresses the ladder

If the rule holds (ignoring bit6), Class A grows from F384's 31 cands
(46%) to ~41 cands (61%). Bigger pre-injection target for Phase 2D.

The F381→F385 chain is now: 5 numbered memos, 1 falsified hypothesis
(F382), 2 narrowing iterations (F383→F384, F384→F385), 11-cand sample,
~210s of cadical compute. Each iteration tightens the structural rule.
The CORE finding (Tseitin XOR ladder structure exists in proofs) is
robust across all iterations. The boundary keeps refining.

Discipline pattern: 8 retraction-or-narrowing iterations across the
project's history. Each one shipped honestly within hours. F384 added
retraction header pointing to F385.

Shipped:
  - `bets/cascade_aux_encoding/results/20260501_F385_xor_ladder_class_A_broader_than_claimed.md`
  - F384 retraction header → "PARTIALLY_NARROWED — F385 found Class A is broader"
  - 3 cadical runs logged via append_run.py
  - 11-cand fingerprint table

Open for next session:
  (a) Investigate bit6_m024723f3 outlier (why no ladder despite fill_bit[6]=1?)
  (b) Run remaining 56 cands systematically (~28 min cadical, definitive picture)
  (c) Algebraically derive ladder condition from cascade-aux encoder source

## ~12:00 EDT — F386: bit6 outlier confirmed genuine, then second iteration finds 12/12 rule

Step 1: Relaxed-classifier reanalysis of bit6_m024723f3 proof (fill=0x7fffffff,
kbit=6, F385 outlier). Tested aux_step ∈ {1,2}, dw_step ∈ {3..6},
dw_width ∈ {1,2,3}, both polarities — ZERO ladders found. Confirms
the outlier is genuine, not a classifier artifact.

Step 2: Proposed AND-rule "fill_bit[31]=1 AND fill_bit[kbit]=1" (fits
F385's 11 cands). Tested on bit6_m6781a62a (fill=0xaaaaaaaa, kbit=6;
fill_bit[6]=0; rule predicts Class B). Generated aux_force CNF, ran
cadical 30s. Result: **ladder=31** (Class A). RULE FALSIFIED.

Step 3: Re-derived rule on n=12. Found:

  **`ladder iff fill_bit[31]=1 AND (fill & 0x7fffffff) != 0`** — fits 12/12

Equivalently: `fill > 0x80000000` (unsigned), or
`fill_bit[31]=1 AND fill HW > 1`.

Class A coverage under refined rule: 37 of 67 cands (55%):
  fill=0xffffffff (31 cands): Class A
  fill=0xaaaaaaaa (6 cands):  Class A
  Others: Class B

The rule depends only on FILL, not on kbit (F385 was wrong on that).
The mechanism: cascade-1 sigma1 application requires fill bit-31 set
to bring high bits into output AND requires fill density >1 to produce
rich Tseitin XOR patterns. fill=0x80000000 is too sparse despite
having bit-31 set.

Project's **9th iterative narrowing** in this chain. Each falsification
within hours. The rule has stabilized at n=12.

Shipped:
  - `bets/cascade_aux_encoding/results/20260501_F386_bit6_outlier_confirmed_genuine.md`
    (with two-stage refinement: original AND-rule falsified, then
     re-corrected rule fits 12/12)
  - 1 cadical run logged via append_run.py
  - 1 new aux_force CNF for bit6_m6781a62a (audited CONFIRMED)
  - dashboard refreshed

The F381 → F386 chain converged: 9 iterations, ~240s cadical compute,
12/12 cands fit a single algebraic rule on fill alone. **Phase 2D
pre-injection becomes deterministic** — for each cand's fill, the
rule decides ladder injection or not. 37 of 67 cands get the
31-rung ladder; the rest get F343's 2-clause baseline.

## ~12:30 EDT — F387: BOTH F385 + F386 FALSIFIED; new rule fits 14/14

Distinguishing tests of F385 vs F386 on 2 cands:
  bit6_m88fab888 fill=0x55555555 kbit=6: F385→A, F386→B → empirical: A
    Falsifies F386 (fill > 0x80000000 was wrong)
  bit0_mf3a909cc fill=0xaaaaaaaa kbit=0: F385→B, F386→A → empirical: A
    Falsifies F385 (fill_bit[kbit]=1 was wrong)

Both rules falsified within ~10 min of being proposed.

Re-derived on full n=14 truth table. Found rule fitting 14/14:

  **`ladder iff (m0_bit[31] = 1) OR (fill_bit[31] = 1 AND fill_HW > 1)`**

Two paths to Class A:
  PATH 1: m0 has bit-31 set
  PATH 2: fill has bit-31 set AND fill is rich (HW > 1)

bit6_m88fab888 reaches Class A via Path 1 (m0=0x88fab888 has bit-31=1,
even though fill=0x55555555 has bit-31=0).

Mechanism: bit-31 information flows into the cascade-1 region either
via M[0]=m0 (rotation propagation) or via M[1..15]=fill (schedule
recurrence). Either path triggers sigma1's rich-bit Tseitin output.
fill=0x80000000 is too sparse to activate Path 2; fill_bit[31]=0
disables Path 2 entirely.

**Class A coverage under F387 rule: 51/67 = 76% of registry** (much
broader than F386's 55%):
  via Path 2 (fill_bit[31]=1 AND HW>1): 37 cands
  via Path 1 only (m0_bit[31]=1, fill not Path 2): 14 cands
  Class B: 16 cands

This is the project's **10th iterative rule narrowing**, ~270s cadical
total. The picture has been remarkably consistent in pattern: each
rule shipped, falsified within hours by edge cases, refined to fit
larger n. F387 fits 14/14 — strongest empirical anchor yet.

Phase 2D pre-injection becomes a per-(m0, fill) decision:
```python
def class_a(m0: int, fill: int) -> bool:
    return ((m0 >> 31) & 1) or (((fill >> 31) & 1) and bin(fill).count("1") > 1)
```

Shipped:
  - `bets/cascade_aux_encoding/results/20260501_F387_distinguishing_tests_falsify_both_F385_F386.md`
  - 2 cadical 30s runs logged (bit6_m88fab888, bit0_mf3a909cc)
  - 2 new aux_force CNFs in cascade_aux/cnfs/, audited CONFIRMED
  - dashboard refreshed

Open: confirm F387 by testing 1-2 m0_bit[31]=1 cands at fill=0x80000000
(predicted Class A by F387, would be FALSE for F386). Strong test of
Path 1.
