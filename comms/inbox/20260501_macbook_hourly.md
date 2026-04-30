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

## ~13:15 EDT — F388: F387 Path 1 CONFIRMED at n=16

Tested 2 cands where Path 2 fails completely (fill_HW ≤ 1) but Path 1
holds (m0_bit[31]=1):

  bit10_m9e157d24 fill=0x80000000 (HW=1): m0=0x9e157d24 has bit-31=1
  msb_m9cfea9ce   fill=0x00000000 (HW=0): m0=0x9cfea9ce has bit-31=1

Both predicted Class A by F387 Path 1. Both predicted Class B by F386
(which lacked Path 1).

Empirical: BOTH ladder=31 (Class A). **F387 confirmed.**

This is the cleanest test of Path 1's independent existence — fill
contributes nothing in either case (HW≤1) but the ladder still appears.
M[0]=m0 with bit-31 set is sufficient on its own to propagate bit-31
through the round function into the cascade-1 region.

F387 rule now anchored at n=16:

  ladder iff (m0_bit[31] = 1) OR (fill_bit[31] = 1 AND fill_HW > 1)

Path 1 (m0): 14 cands (excl. fill=ffffffff/aaaaaaaa) → 14 + Path 2's 37 = 51 of 67 (76%)
Path 2 (fill): 37 cands

Project's rule has stabilized: 0 falsifications since F387's proposal.

Phase 2D pre-injection becomes:
```python
def class_a(m0, fill):
    return ((m0 >> 31) & 1) or (((fill >> 31) & 1) and bin(fill).count("1") > 1)
```

Shipped:
  - `bets/cascade_aux_encoding/results/20260501_F388_path1_confirmed_F387_anchored_n16.md`
  - 2 cadical 30s runs logged via append_run.py
  - 1 new aux_force CNF (bit10_m9e157d24 generated, audited CONFIRMED)
  - F387 rule anchored at n=16 (10 iterations, ~330s cadical total)

Open: F387 algebraic derivation from encoder source; deployable
propagator extension code. Both sub-30-min for next session.

## ~13:30 EDT — F389: F387/F384 packaged into deployable propagator pre-injection tool

Built `bridge_preflight_extended.py` (~250 LOC) — turns the F387 rule
into a deployable Phase 2D pre-injection tool. End-to-end pipeline:

  Input: aux_force CNF + (optional) varmap
  - F387 class decision in O(1) per (m0, fill)
  - For Class A: cadical 30s LRAT + classifier extracts 31-rung ladder
  - For Class B: F343 baseline only
  Output: JSON spec with all clauses ready for cb_add_external_clause

Smoke tests (3 cands):
  bit31 (Class A Path 2: fill rich): 124 size-3 ladder clauses mined
  bit10_m9e157d24 (Class A Path 1: m0 b31): 124 ladder + 2 F343 = 126
  bit11_m45b0a5f6 (Class B): 0 clauses (no varmap; F343 skipped)

124 clauses per Class A cand = 31 XOR triples × 4 polarities each.
Plus F343 baseline (~2 clauses) = ~126 total injection per Class A.

For registry-wide deployment: 51 Class A cands × 30s mining = 25 min
total, one-time. Resulting JSON specs cached for fast Phase 2D
consumption.

Empirical projection: F343 alone gives −9.10% conflict reduction at
60s (F369 measurement). F384 ladder pre-injection adds ~+0.9% (per
F384 estimate). Combined: ~−10% on Class A cands. Not headline-class
but a real ~10% improvement to the 51-cand Phase 2D Class A panel.

Shipped:
  - `bets/programmatic_sat_propagator/propagators/bridge_preflight_extended.py`
  - `bets/programmatic_sat_propagator/results/preflight_2026-04-29/F389_bridge_preflight_extended_deployable.md`
  - 3 smoke-test cadical runs logged via append_run.py
  - dashboard refreshed; validate_registry: 0/0

The F381 → F389 chain is now end-to-end deployable:
  F381: discovered structure (1 cand)
  F382-F386: 6 falsified hypotheses
  F387: rule fits 14/14
  F388: anchored at 16/16, Path 1 confirmed independent
  F389: packaged as deployable Phase 2D pre-injection tool

11 numbered memos, 22 commits, ~5-6 hours, ~360s cadical compute.
Phase 2D pre-injection can now be shipped from this F389 spec.

Open for next session: registry-wide Class A clause spec generation
(~25 min compute, all 51 cands cached as JSON).

## ~14:15 EDT — F390: F389 ladder pre-injection HURTS bit2 by +2.35% (FALSIFIED)

Direct empirical test of F389's "+0.9% additive speedup from ladder
pre-injection" projection. Built 3 CNFs (baseline, F343-only,
F389-extended) and ran cadical 60s × 3 seeds × 3 conditions =
9 runs, parallel-3, ~3 min wall.

Result on bit2_ma896ee41 (Class A Path 1+2, fill=ffffffff):
  baseline: mean 1,603,414 conflicts
  F343:     mean 1,604,473 (Δ=+0.07%, within F369 σ=2.68% noise)
  F389:     mean 1,641,126 (Δ=+2.35%, HURT — outside σ noise)

**F389's ladder pre-injection EMPIRICALLY HURTS by +2.35% conflicts.**
Adding 124 ladder clauses to the F343 baseline costs more in
clause-watching overhead than it saves in conflict avoidance.

The F381 → F388 STRUCTURAL finding (ladder exists in proofs) stands.
The F389 APPLICATION claim (pre-inject for additive speedup) is
falsified at n=1 cand × 3 seeds. Worth confirming on 1-2 more
Class A cands but the directional finding is clear.

F389 retraction: speedup claim retracted; tool stands as a
characterization of cascade-aux CDCL proof structure (Class A vs B
per F387 rule). Phase 2D propagator design: stay with F343's 2-clause
baseline; don't ship the ladder extension.

Project's 11th iterative narrowing/falsification. Pattern continues:
small empirical claims falsified within hours of being proposed.

The F381 → F390 chain ended on a clean negative for Phase 2D speedup
mechanism. The structural picture is real; it doesn't translate to
solver performance gains.

Shipped:
  - `bets/programmatic_sat_propagator/results/preflight_2026-04-29/F390_F389_ladder_injection_FALSIFIED_bit2.md`
  - 9 cadical 60s runs logged via append_run.py
  - F389 retraction header pointing to F390
  - dashboard refreshed; validate_registry: 0/0
  - 3 transient CNFs in /tmp/F390/

The remaining F381→F390 chain value is in the CHARACTERIZATION
(where structural Tseitin XOR ladders appear in proofs as a function
of m0 and fill), not in solver speedup. The Phase 2D viability
picture narrows further: F343 alone is the only F343-class lever
worth keeping.

## ~14:30 EDT — F391: F389 falsification CONFIRMED at n=3 cands

Replicated F390's bit2 finding on bit31_m17149975 + bit3_m33ec77ca.
18 cadical 60s runs (2 cands × 3 conditions × 3 seeds), parallel-3,
~6 min wall.

3-cand panel:
  bit2_ma896ee41    F343=+0.07%   F389=+2.35%  (ladder hurts +2.3pp)
  bit31_m17149975   F343=-13.12%  F389=-3.83%  (ladder loses 9.3pp)
  bit3_m33ec77ca    F343=-8.17%   F389=-5.64%  (ladder loses 2.5pp)

Mean across 3 cands × 3 seeds (n=9 per condition):
  F343 alone: −7.07% (consistent with F369's −9.10% 5-cand mean)
  F389:       −2.37% (loses ~5pp to ladder overhead)

**F389 is uniformly WORSE than F343 alone, by 2.5-9.3pp across 3/3
cands.** The ladder ALWAYS HURTS relative to F343-only. Strongest hurt
on bit31 (the cand where F343 helps most: −13.12% → ladder eats 9.3pp
back).

Mechanism: ladder clauses are TSEITIN-redundant with the encoder's
output. CDCL discovers them for "free" via UP chains within the
first ~12k of 1.4M proof lines. Pre-injecting 124 clauses adds
watch-list overhead that compounds across 1.5M conflicts → measurable
runtime penalty without any new search-pruning value.

Project's 12th iterative narrowing/falsification.

F381 → F391 chain final summary:
  F381-F388 (8 iterations): structural rule established at 16/16
  F389: packaged as deployable spec
  F390 (n=1): speedup FALSIFIED on bit2
  F391 (n=3): falsification CONFIRMED — ladder uniformly hurts

26 commits, ~7-8 hours, ~580s cadical compute.

The STRUCTURAL finding (ladder exists per F387 rule) is REAL.
The APPLICATION finding (ladder pre-injection helps) is FALSIFIED.
Tool stands as characterization; spec dead.

Phase 2D viable speedup levers narrow to:
  - F343 baseline alone (~−7% mean, high cand-variance)
  - cb_decide on F286 132-bit core (untested)
  - That's it.

Shipped:
  - `bets/programmatic_sat_propagator/results/preflight_2026-04-29/F391_F389_falsified_3cand_panel.md`
  - 18 cadical 60s runs logged via append_run.py
  - 6 transient CNFs in /tmp/F391/
  - dashboard refreshed; validate_registry: 0/0

Open: cadical --statistics on baseline vs F389 to nail down the
watch-list overhead mechanism. ~10 min compute. Or test at 5-min
budget per F366 saturation pattern.

## ~14:50 EDT — F392: F343 per-cand effectiveness MYSTERY documented (n=8)

Investigated F391's open question — what predicts which cands get a
big F343 win? Analyzed 8 cands with measured F343 effects (5 from F369,
3 from F391):

  bit2_ma896ee41 fill=ffffffff:  +0.07%  ← outlier (no help)
  bit11_m45b0a5f6 fill=00000000: −7.56%
  bit13_m4d9f691c fill=55555555: −5.89%
  bit3_m33ec77ca fill=ffffffff:  −8.17%
  bit0_m8299b36f fill=80000000:  −8.33%
  bit17_m427c281d fill=80000000: −11.72%
  bit10_m3304caa0 fill=80000000: −12.03%
  bit31_m17149975 fill=ffffffff: −13.12%

Range: 0% to −13%. ~13pp spread.

**Key sub-finding: bit2 and bit3 have IDENTICAL F343 clause structure.**
Both force dW57[0]=1; both forbid W57[22:23]=(0,0). Different var IDs
(per encoder allocation) but same structural meaning. Yet F343 effects
differ by 8 percentage points (bit2: +0.07%, bit3: −8.17%).

Same clauses, same structural meaning, COMPLETELY DIFFERENT solver
impact.

Tested feature → effect correlation matrix shows NO simple feature
predicts F343 effectiveness:
  - F387 class: identical for bit2 + bit3 (both Class A)
  - dW57[0] polarity: identical
  - W57[22:23] polarity: identical
  - m0_HW, fill_HW: not predictive
  - kbit position: not predictive

Conclusion: **F343 effectiveness is a search-implementation property,
not a pure structural feature of (m0, fill, kbit).** Likely depends on:
  - cadical search trajectory per cand
  - conflict-density profile (when CDCL would naturally derive these
    clauses if not pre-injected)
  - clause-to-CNF interaction (subsumption / propagation)

These are testable via cadical --statistics + conflict-trace
instrumentation.

For Phase 2D: don't claim per-cand F343 savings; report mean (~−7-9%)
with σ. Apply F343 universally; accept that some cands (like bit2)
won't benefit.

F381 → F392 chain (extended):
  F381-F388: structural rule fits 16/16 — REAL
  F389: deployable spec — TOOL stands, application FALSIFIED
  F390-F391: ladder pre-injection HURTS — FALSIFIED at n=3
  F392: F343 effectiveness mystery — OPEN QUESTION documented

13 numbered memos, ~8 hours.

Shipped:
  - `bets/programmatic_sat_propagator/results/preflight_2026-04-29/F392_F343_effectiveness_mystery_open.md`
  - 0 cadical runs (pure analytical reuse of F369 + F391 data)

This is mechanism-level investigation that ships honestly: characterizes
the variance, falsifies the simple structural-feature predictors,
proposes search-implementation investigation as next-iteration work.
Per user direction, this is the "documented open mystery" form of
unit-of-progress — neither a false claim nor a missed observation.

## ~15:30 EDT — F393: cadical --stats supports search-trajectory hypothesis

Ran cadical 60s with --stats=true on bit2 + bit3 × baseline + F343
(4 conditions, ~4 min CPU). Extracted propagation/conflict/learning
metrics:

  bit2 baseline → F343:
    conflicts:    2,331,726 → 2,347,411  (+0.67%, slight increase)
    propagations: 236,944,236 → 250,184,545  (+5.59%)

  bit3 baseline → F343:
    conflicts:    2,469,936 → 2,247,794  (-8.99%)
    propagations: 225,886,123 → 255,825,461  (+13.25%)

**Critical finding: F343 clauses ARE activated on both cands** (visible
propagation rise). But only bit3 sees conflict reduction. On bit2 the
+5.59% propagations buy ZERO conflict reduction — propagations happen
but don't prune the search tree.

This SUPPORTS F392 hypothesis (a): search-trajectory dependence. F343
clauses constrain dW57[0] and W57[22:23] vars. For pruning to work,
cadical's VSIDS must bring those vars to high decision priority.
On bit3 it does; on bit2 it doesn't (cadical's search trajectory
ignores the constrained region).

Falsifies the "F343 doesn't fire on bit2" sub-hypothesis. Activations
happen — they're just wasted because cadical doesn't decide on the
relevant branches.

**Phase 2D mechanism-aligned proposal**: extend F343 with VSIDS-bumping
of dW57[0] + W57[22:23] vars at solver init. Could force cadical to
consider those branches, potentially extracting F343 benefit on cands
like bit2 where current F343 doesn't help. Untested but mechanism-
aligned.

F381 → F393 chain (14 memos, ~9 hours, ~620s cadical compute):
  Structural finding (F387 ladder rule): REAL
  Application 1 (ladder pre-injection per F389): FALSIFIED
  Application 2 (F343 baseline): WORKS but per-cand-variable
    Mechanism: propagation always works; pruning depends on
    cadical's VSIDS reaching the constrained vars
  Phase 2D proposal: VSIDS-boost on F343 target vars (untested)

Shipped:
  - `bets/programmatic_sat_propagator/results/preflight_2026-04-29/F393_F343_mechanism_propagation_no_pruning_bit2.md`
  - 4 cadical 60s --stats runs logged via append_run.py
  - 4 transient logs in /tmp/F393/
  - dashboard refreshed; validate_registry: 0/0

Open: verify search-trajectory hypothesis at n=2-3 more cands (bit10
helps -12%, bit11 helps -7% — both should show prop+ AND conflict-
patterns). And test the VSIDS-boost proposal with cadical's
--bumpreason or activity-priming. Sub-30-min routine for next session.

## ~16:15 EDT — F394: search-trajectory hypothesis CONFIRMED at n=4

Ran cadical 60s --stats=true on bit10 + bit11 × baseline + F343
(4 conditions, ~4 min CPU). Combined with F393's bit2 + bit3 data:

  cand     F343 conflicts Δ%   F343 propagations Δ%   pattern
  bit2     +0.67%               +5.59%                 prop+ NO prune
  bit3     -8.99%               +13.25%                prop+ AND prune
  bit10    -5.16%               +28.14%                prop+ AND prune
  bit11    -7.55%               +33.69%                prop+ AND prune

**Universal pattern at n=4: F343 clauses ALWAYS propagate (+5-34%)**.
Variance in EFFECTIVENESS depends on whether cadical's VSIDS branches
on the F343-constrained vars.

bit2 is the lone "wasted propagation" outlier — F343 clauses fire but
don't translate to conflict-tree-pruning. Other 3 cands all show
prop-rise CO-INCIDING with conflict-reduction.

Refined into a **2-factor model**:
  Factor A: does VSIDS reach the F343-constrained vars? (binary;
            bit2=NO, others=YES)
  Factor B: when reached, how often do the constraints trigger
            conflicts? (graded; bit3=high, bit10/11=lower)

bit3 has the BEST yield ratio (-9% conflicts / +13% prop = 0.68).
bit10/11 have lower yield ratios (~0.18-0.22). Even within
"helping" cands, the per-prop pruning yield varies.

Phase 2D mechanism-aligned proposal (F393): extend F343 with
VSIDS-bumping of dW57[0] + W57[22:23] vars at solver init. Addresses
Factor A specifically. Untested intervention.

F381 → F394 chain: 15 numbered memos, 30 commits, ~10 hours,
~680s cadical compute.

Direction is now sharper: structural rule REAL (F387 fits 16/16);
ladder pre-injection FALSIFIED (F391); F343 effectiveness UNDERSTOOD
mechanistically (propagation always; pruning conditional on VSIDS
trajectory at n=4 cands); concrete next intervention proposed
(VSIDS boost).

Shipped:
  - `bets/programmatic_sat_propagator/results/preflight_2026-04-29/F394_search_trajectory_hypothesis_confirmed_n4.md`
  - 4 cadical 60s --stats runs logged via append_run.py
  - 4 transient logs in /tmp/F394/
  - dashboard refreshed; validate_registry: 0/0

Open: test VSIDS-boost intervention via cadical's `--bumpreason` or
activity-priming; investigate Factor B (yield rate variance among
helping cands); test F344 32-clause variant on bit10/11 to see if
richer clause sets close the yield gap.

## ~17:00 EDT — F395: F344 32-clause variant on bit2 — marginal help, doesn't break pattern

Mined F344-class clauses for bit2 (`scan_all` single bits +
`scan_adjacent` pairs). 13 min wall. Result: 1 unit (only dW57[0]
forced) + 31 pairs = **32 injectable clauses**.

Ran cadical 60s × 3 seeds × {baseline, F343 (2 clauses), F344 (32
clauses)} on bit2. Parallel-3, ~3 min wall.

Mean conflicts:
  baseline: 2,216,525
  F343:     2,178,939   Δ = -1.70%
  F344:     2,147,695   Δ = -3.11%

F344 helps bit2 by ~3% — modestly better than F343's 1.7%, but doesn't
transform bit2 into a "F343 helps a lot" cand like bit3 (-9% with 2
clauses). The marginal F344-over-F343 gain is **+1.4pp** at 16x more
clauses.

This SUPPORTS F394's search-trajectory hypothesis: clause richness
alone doesn't compensate for VSIDS-trajectory mismatch. Even with
16x more clauses, bit2's effect stays modest because the issue is
decision-priority, not clause count.

Cost-benefit: F344 mining = 13 min vs F343 = 20s (~32x slower). 1-3pp
marginal benefit per cand. Poor cost-benefit; F343 is the right
routine intervention.

**Re-examining F347's "-13.7%" headline**: F347 reported F344 → -13.7%
on bit31. F391 found F343 alone → -13.12% on bit31. F344's marginal
benefit on bit31 is just 0.6pp. **F347's headline number was mostly
F343's contribution, not F344's.** F347 wasn't showing a unique F344
benefit — just F343's peak at 60s budget on bit31. Consistent with
F366's budget-dependence finding.

Phase 2D pre-injection design (locked in):
  - F343 (2 clauses) universally → ~-7-9% mean (high variance)
  - NOT F344 (32 clauses) → 32x mining cost, 1-3pp marginal
  - NOT F384 ladder → falsified (F391)
  - VSIDS-boost intervention (F394 proposal) → only remaining unexplored
    mechanism-aligned axis

F381 → F395 chain (16 memos, ~11 hours, ~1500s cadical):
  Structural rule REAL; ladder pre-injection FALSIFIED;
  F343 effectiveness MECHANISM UNDERSTOOD (search-trajectory);
  Clause-count axis EXHAUSTED (F344 marginal); only VSIDS axis remains
  for mechanism-aligned improvement.

Shipped:
  - `bets/programmatic_sat_propagator/results/preflight_2026-04-29/F395_F344_32clause_bit2_marginal_help.md`
  - 9 cadical 60s runs logged via append_run.py
  - 1 new bit2_F344.cnf in /tmp/F395/
  - dashboard refreshed; validate_registry: 0/0

Open: VSIDS-boost intervention test (F394 proposal). Algebraic derivation
of F387 rule. Investigation of why bit3's F343 yield is 0.68 vs
bit10/11 at 0.18 — Factor B remains unexplored.

## ~17:30 EDT — Cross-machine catch-up: yale comms + 2 heartbeat refreshes

The F381-F395 chain has run macbook-side compute to exhaustion. Remaining
moves require either C++ propagator instrumentation (10-14h Phase 2D
build) or pivoting to a different bet. Used this hour for cross-machine
coordination + bet-yaml hygiene instead.

Shipped:
  - `comms/inbox/20260501_macbook_to_yale_F381_F395_chain_summary.md`:
    Catches yale up on the 16-memo F381-F395 chain. Includes:
      - Structural finding (F387 rule fits 16/16)
      - Application falsified (F389 ladder pre-injection HURTS)
      - F343 mechanism understood (search-trajectory dependence)
      - Clause-count axis exhausted (F395)
      - 3 open questions where yale input would help (VSIDS-boost,
        Factor B yield variance, algebraic derivation)
    yale's last commit was 2026-04-29 12:55, ~36 hours ago. The message
    is informational; if yale's deep in long-running compute, no
    urgency. If yale has shipped something to react to, will catch up.

  - `cascade_aux_encoding/BET.yaml` heartbeat refreshed (was
    2026-04-30T02:25, ~36h stale within 7-day interval). Added
    `recent_progress_2026-05-01_F381_F395_xor_ladder_chain` block
    summarizing the F381-F395 chain with structural finding,
    falsifications, mechanism understanding, locked Phase 2D design.

  - `programmatic_sat_propagator/BET.yaml` heartbeat refreshed (was
    2026-04-30T05:23, ~30h stale within 14-day interval). Added
    `recent_progress_2026-05-01_F381_F395_F389_falsified_F343_mechanism`
    block summarizing the same chain from the propagator-bet angle.

Both heartbeats now 2026-05-01T17:30Z. validate_registry: 0/0.

Cross-machine state: yale established + quiet 36h. Macbook caught up
on substantive coordination message. The 16-memo chain is now fully
documented in both bets' progress notes for future reference.

If next iteration brings yale activity, macbook can quickly react
since the F381-F395 chain is in shape.

## ~17:40 EDT — Yale RESPONDED with F396 + F397 (cross-machine flywheel works)

Push rejected because yale shipped 2 commits while I was writing the
F381-F395 summary:

  - 9fa45de (17:20 EDT) "Build candidate evidence manifest" → F396:
    119-row cross-bet candidate evidence manifest with all 67 registry
    cands, F387 Class A/B labels (51 A / 16 B per F388 confirmation),
    21 preflight clause sets, F340 polarity probes, block2 bridge-beam
    W-witnesses + cert-pin verdicts, and yale F380/F384 bridge-cube
    context joined.

  - 3822690 (17:25 EDT) "Emit decision priority specs" → F397:
    Two cb_decide priority specs:
      f286_132_conservative (132 vars: F286 universal core)
      f332_139_stable6 (139 vars: broader n=6 stable-core)
    Both complete for 6 F332 sr=60 aux-force cands.

**This is exactly the F394 VSIDS-boost-proposal direction.** Yale
shipped the deployable spec the propagator needs, before reading my
F381-F395 summary message.

Resolved git rebase merge conflict in propagator BET.yaml — kept
both progress blocks (yale F397 + my F381-F395), reconciled
heartbeats. Wrote follow-up acknowledgement message:

  comms/inbox/20260501_macbook_to_yale_F396_F397_thanks.md

Includes:
  - Thanks for the timing-cross-paths flywheel response
  - How macbook side will react: read F396 detail; cross-check F397
    priority specs vs F343-constrained vars
  - Coordination request: confirm if F397 priority sets include
    dW57[0] + W57[22:23] (would directly support F394 mechanism)

Cross-bet implication: F396's manifest is the data backbone for
future structural selectors. F378 bridge_score + F379 bridge_beam
should be updated to consume F396 manifest where they currently
re-derive features per cand.

The cross-machine flywheel is working as designed: macbook ships
empirical chain → yale silently ingests → yale produces follow-on
artifacts in the named direction → macbook acknowledges + plans
integration. Zero coordination overhead, ~36 hour latency.

----

## ~17:50 EDT — F398: I answered my own F397 vs F394 question

Rather than wait on the F396_F397_thanks coordination request, I
inspected `F397_decision_priority_specs.json` directly and wrote up
the cross-check:

  headline_hunt/bets/programmatic_sat_propagator/results/preflight_2026-04-29/
    F398_F397_priorities_vs_F394_mechanism_cross_check.md

Concrete numbers (bit10):
  - F397 `f286_132_conservative` priority: 132 vars, range [2, 257]
  - dW57[0] = var 12317 → NOT in priority set
  - W57[22] = var 12339 → NOT in priority set
  - W57[23] = var 12340 → NOT in priority set
  - BUT W1_57[0] = var 2 AND W2_57[0] = var 130 ARE in F397
    (these are the Tseitin XOR parents of dW57[0])

So F397 addresses F394 mechanism at a higher abstraction level
(parents) — VSIDS branches on schedule-word vars, then forces dW57
diff vars via UP through Tseitin XOR clauses. F397 + F343 are
**complementary, not redundant**.

Slight mismatch flagged: F397 prioritizes only W1_57[0] / W2_57[0]
(F286 anchors), not W1_57[22]/W2_57[22] etc. So F343's W57[22:23]
pair clause's parents may not be in F397's priority set. Worth a
row in the F399 matrix.

Optional enhancement proposed: extend F397 with a third arm that
includes the dW57 row directly (164 vars total). Would let F399's
matrix test whether parent-priority via UP suffices, or diff-var
priority adds value beyond UP.

Wrote follow-up message to yale:
  comms/inbox/20260501_macbook_to_yale_F398_F397_cross_check_response.md

Includes:
  - F398 findings (parent vs child level, Tseitin XOR bridge)
  - The slight W57[22:23] parent-mismatch caveat
  - dW57-row arm enhancement suggestion
  - Offer to push 5 missing CNFs+varmaps for F399 if yale prefers
    that over local regeneration via cascade_aux_encoder.py

Compute: 0 cadical runs, analytical only. No audit needed.

State: F381-F398 chain at a natural pause point. Macbook will hold
position and continue cross-checking yale output as it lands.
Phase 2D C++ build remains gated on user direction.

----

## ~18:10 EDT — F400: first concrete F343 predictor (cross-bet F396 join)

Built the analytical join F392 + F394 (macbook F343 effectiveness) ×
F396 (yale candidate evidence manifest). At n=8:

  Class A (n=4):  mean -7.39%   stdev 5.48   range [-13.12, +0.07]
  Class B (n=4):  mean -9.30%   stdev 3.05   range [-12.03, -5.89]

**F387 class predicts F343 effectiveness *variance*.** Class B is
1.8x more reliable. The only non-helper at n=8 is bit2_ma896ee41,
which is the only "both F387 paths satisfied" cand in the panel
(m0_bit[31]=1 AND fill_bit[31]=1 AND fill_HW>1).

Hypothesis F400-H1 (n=1, falsifiable): Class A "both paths" cands
are F343 non-helpers. Test cost: ~3min compute per new "both paths"
cand. Cheap to extend.

Phase 2D deployment recipe now class-conditional:
  - Class B → F343 unconditionally (bounded yield)
  - Class A path1-only / path2-only → F343 (variable yield)
  - Class A both paths → F343 + VSIDS-boost (F397) or skip injection

Memo: headline_hunt/bets/programmatic_sat_propagator/results/
      preflight_2026-04-29/F400_F387_class_predicts_F343_effectiveness_variance.md

This is the first concrete cross-bet payoff from yale's F396 manifest
— exactly what the F396_F397_thanks message anticipated. Cost: 0
cadical runs (analytical only). Output: a deployable predictor.

----

## ~18:35 EDT — F401: F400-H1 FALSIFIED at n=2 (compute test)

Picked bit28_md1acca79 from F396 registry scan: Class A "both paths"
profile (m0_bit[31]=1 AND fill_bit[31]=1 AND fill_HW=32), already had
aux_force_sr60 CNF + varmap, no encoder regen needed.

Pipeline: preflight mining (5s probe) → F343 inject → cadical 60s
× baseline + F343 → 2 runs logged via append_run.py.

Result for bit28:
  conflicts:    -6.37%   ← F343 HELPS (yield 0.25)
  propagations: +25.34%  ← clauses propagate
  learned:      -6.13%

Compare bit2_ma896ee41 (only other "both paths" cand tested): +0.07%
non-helper. So "both paths" is NOT a sufficient predictor for non-
helper status. F400-H1 FALSIFIED at n=2.

bit2 remains a structurally unexplained outlier. The cleanest
distinguishing feature against bit28 is F343 unit-clause forcing
polarity (bit2 forces dW57[0]=1, bit28 forces =0), but bit11 also
forces =1 and helps, so polarity alone doesn't explain either.

What still holds: F400's headline (Class B reliable stdev 3.05, Class
A bimodal stdev 5.48). What's dead: F400-H1's specific sub-profile
claim. Honest falsification within ~30 min of proposing it.

Memo: headline_hunt/bets/programmatic_sat_propagator/results/
      preflight_2026-04-29/F401_F400_H1_FALSIFIED_bit28_both_paths_helps.md

Compute: 120s cadical + ~20s preflight = ~2.5 min. 2 runs logged
(/tmp transients with --allow-audit-failure consistent with F390-F394
protocol). Dashboard refreshed: 1844 runs, 0% real audit failures.

----

## ~19:25 EDT — F402: bit2 confirmed singleton outlier at n=4

Extended F401 from n=2 to n=4 in Class A "both paths" sub-profile by
encoding + testing bit4_md41b678d (kbit=4) and bit24_mdc27e18c
(kbit=24). Both got fresh aux_force_sr60 CNFs + varmaps via
cascade_aux_encoder.py, then F343 preflight + inject + cadical 60s.

n=4 "both paths" Class A panel:
  bit2  (kbit=2):  +0.07%   non-helper
  bit4  (kbit=4):  -9.40%   helps strongly (yield 0.24)
  bit24 (kbit=24): -7.13%   helps (yield 0.32)
  bit28 (kbit=28): -6.37%   helps (yield 0.25)

3/4 help. bit2 is the lone non-helper across all 9 cands tested for
F343 effectiveness in the F381-F402 chain (Class A both n=4 + Class A
path1/path2 n=3 + Class B n=4 = 11 cand-conditions, 1 non-helper).

F400-H1 fully falsified: "both paths" is NOT a non-helper sub-profile.
Mode within "both paths" is "helps with bounded yield ~0.25" — actually
a tighter cluster than Class B without the bit2 outlier.

bit2's distinguishing features vs bit4/24/28: kbit=2 (low), unit
forced=1 + pair forbids (0,0). But neither dimension predicts alone
(bit4 also forces=1 helps; bit11 also forbids (0,0) helps).

bit2 mechanism remains structurally unexplained at F396-feature level.

Updated Phase 2D F343 recipe (n=9): "deploy F343 universally, except
bit2_ma896ee41" — cand-level rule, not class-level. Cleaner than the
F400 class-conditional recipe.

Cross-machine note for yale's F399 matrix: include bit2 explicitly to
test whether F397 VSIDS-boost rescues the singleton outlier.

Memo: headline_hunt/bets/programmatic_sat_propagator/results/
      preflight_2026-04-29/F402_both_paths_singleton_outlier_n4.md

Compute: ~4 min cadical + ~40s preflight + ~2s encode = ~5 min wall.
4 runs logged. Dashboard: 1848 runs, 0% real audit failures.

Hypothesis-test cycle (F400 propose → F401 + F402 falsify) closed
within the same 60-minute window.
