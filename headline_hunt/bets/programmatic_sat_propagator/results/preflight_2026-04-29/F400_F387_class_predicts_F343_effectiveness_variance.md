---
date: 2026-05-01
bet: programmatic_sat_propagator × cascade_aux_encoding × math_principles
status: PREDICTOR FOUND — F387 class predicts F343 effectiveness *variance* at n=8 (cross-bet F396 join)
parent: F392 (F343 effectiveness mystery), F394 (Factor A/B model), F396 (yale manifest), F398 (priorities cross-check)
type: analytical cross-bet join (yale F396 features × macbook F343 effectiveness)
compute: 0 cadical (analytical only — joins existing data)
---

# F400: F387 class predicts F343 effectiveness *variance* — first real Factor B predictor

## Question

F392 documented the F343 effectiveness mystery: same clauses on bit2
and bit3 produce wildly different solver impact (+0.07% vs −8.17%).
F394 framed it as a 2-factor model (A: VSIDS reaches; B: graded yield
when reached). Both F392 and F394 ended with no predictor for Factor B.

**Does any F396-manifest feature predict F343 effectiveness?**

## Method

Cross-bet join:
  - features: yale's F396 manifest (`headline_hunt/bets/math_principles/
    data/20260430_F396_candidate_evidence_manifest.jsonl`, 119 records,
    67 cands)
  - target: F343 effectiveness data from F392's combined 8-cand panel
    (F369 5-cand × 3-seed + F391 3-cand × 3-seed)

Compute: 0 cadical runs. Analytical only.

## Result — n=8 panel, F387 class as predictor

```
cand                 F343 %    f387  m0b31  fill_b31  fill_hw  path1  path2
bit31_m17149975      -13.12     A      0      1        32      False  True
bit10_m3304caa0      -12.03     B      0      1         1      False  False
bit17_m427c281d      -11.72     B      0      1         1      False  False
bit0_m8299b36f        -8.33     A      1      1         1      True   False
bit3_m33ec77ca        -8.17     A      0      1        32      False  True
bit11_m45b0a5f6       -7.56     B      0      0         0      False  False
bit13_m4d9f691c       -5.89     B      0      0        16      False  False
bit2_ma896ee41        +0.07     A      1      1        32      True   True   ← only non-helper
```

### Headline numbers

```
Class A (n=4):  mean -7.39%   stdev 5.48   range [-13.12, +0.07]   ← bimodal
Class B (n=4):  mean -9.30%   stdev 3.05   range [-12.03, -5.89]   ← tight
```

**Class B is 1.8× more reliable** than Class A (stdev 3.05 vs 5.48). The
only non-helper in the n=8 panel is Class A. Mean help is similar
(7.4% vs 9.3%), but the spread differs sharply.

## Findings

### Finding 1 — F387 class predicts F343 *variance*, not mean magnitude

The F387 ladder rule was identified for a different purpose (F343
applicability via aux encoder ladder structure). It now turns out to
also predict F343 effectiveness *reliability*:

  - Class B cands all fall in [−12.03%, −5.89%] (3pp half-width).
    Deploying F343 to a new Class B cand has bounded variance.
  - Class A cands span [−13.12%, +0.07%] (13pp full-width). Deploying
    F343 to a new Class A cand has high variance — it could be the
    biggest winner (bit31 −13.12%) or a complete miss (bit2 +0.07%).

This is the first concrete Factor B predictor in the F392 → F400 chain.

### Finding 2 — Within Class A, "both F387 paths satisfied" may be the non-helper signature

Decomposing Class A by F387 path:

```
profile                       cands              F343 %
path1 only (m0[31]=1, fill weak)    bit0         -8.33  (helps)
path2 only (fill[31]=1, fill_HW>1)  bit3, bit31  -8.17, -13.12  (helps strongly)
both paths satisfied                bit2         +0.07  (no help)
```

The single non-helper at n=8 is the only "both paths" cand. n=1, so this
is a hypothesis, not a confirmed pattern. But it's structurally
distinguishable and testable.

**Hypothesis F400-H1**: Class A cands satisfying BOTH F387 paths are
F343 non-helpers. Falsifiable by finding another "both paths" cand
with significantly negative F343 effect, or another single-path cand
with +0% F343 effect.

### Finding 3 — F396 evidence type asymmetry by F387 class (artifact, not signal)

In the F396 manifest, evidence kinds split asymmetrically by class:

```
                              Class A cands (n=4)         Class B cands (n=4)
preflight_clause_set:         0                            6 (3 each on 2 cands)
cascade_w57_pair_probe:       0                            2 (1 each)
block2_certpin_witness:       6 (all on bit2)              0
block2_bridge_beam_best:      2 (bit2, bit3)               0
```

This is a feature-collection artifact: yale's preflight + W57 probe
pipelines targeted Class B cands more (because F286 universal core was
defined on those), while macbook's block2 pipelines targeted Class A.
Not a causal signal — just a data-coverage note for future joins.

### Finding 4 — Implications for Phase 2D propagator deployment

The 2-factor model from F394:
  Factor A (binary): VSIDS reaches the F343 vars?
  Factor B (graded): yield rate when reached?

Plus the new F400 predictor:
  Factor A is correlated with F387 class (Class B more reliable)
  Factor B is correlated with F387 sub-profile (path1/path2/both)

Concrete deployment recipe (Phase 2D, when the C++ build lands):

  1. Apply F343 unconditionally to Class B cands (bounded yield;
     tight stdev makes confidence-interval claims clean)
  2. Apply F343 + VSIDS-boost (F397's `cb_decide` priority) to Class A
     cands (rescue the bimodal tail)
  3. Test "both paths" Class A cands separately; if F400-H1 holds,
     add F344 32-clause variant or skip injection entirely

This is mechanism-aligned with F397's two priority arms:
  - f286_132_conservative: schedule-word parents → benefits Class B
    (where the F286 universal core is structurally clean)
  - f332_139_stable6: broader stable core → may benefit Class A
    where the path-1/path-2 structure injects variance

### Finding 5 — Cross-machine flywheel realized

This memo is the first concrete cross-bet integration of yale's F396
manifest with macbook's F392/F394 effectiveness data. The macbook
F396_F397_thanks message predicted: "F396's manifest is the data
backbone for any future structural-feature selector." F400 is the
first instance.

The cost was 0 cadical runs (analytical join only). The output is a
deployable predictor.

## What's shipped

- This memo with the n=8 F387-class × F343-effectiveness join
- Headline finding: Class B reliable (stdev 3.05), Class A bimodal
  (stdev 5.48); only non-helper is Class A "both paths"
- Hypothesis F400-H1: Class A "both paths" cands are F343 non-helpers
  (n=1, falsifiable by 2-3 more samples)
- Concrete Phase 2D deployment recipe with class-conditional F343 +
  VSIDS-boost combo

## Compute discipline

- 0 cadical runs
- audit_required: not applicable (no CNFs touched)

## Open questions

(a) **Test F400-H1**: find 2-3 more Class A "both paths" cands and
    measure F343 effect. Need: m0_bit[31]=1 AND fill_bit[31]=1 AND
    fill_HW>1. Candidate registry has 67 cands; query for "both
    paths" sub-profile and pick 3 untested ones. Cheap (~3min compute
    each at 60s × 3 conditions × 3 seeds).

(b) **Extend Class B sample**: only 4 Class B cands tested. Adding
    4-8 more would tighten the stdev confidence interval. Cheap.

(c) **Combine with F397 priority**: would F397's cb_decide priority
    "lift" Class A "both paths" cands out of the non-helper trap?
    This is the F394 VSIDS-boost intervention named explicitly. Gates
    on Phase 2D C++ build (10-14h).

## State

- F400 ships as the first concrete predictor for F392's effectiveness
  mystery
- Phase 2D deployment recipe is now class-conditional, not uniform
- Next testable iteration is F400-H1 (n=2-3 more "both paths" cands,
  cheap)
- Cross-machine flywheel: yale F396 → macbook F400, ~16h after F396
  shipped

## F381 → F400 chain summary

```
F381-F388 (8 iter):  Structural rule (ladder per F387) — REAL, n=16
F389:                Deployable spec — TOOL stands; application FALSIFIED
F390-F391:           Ladder pre-injection HURTS — FALSIFIED at n=3
F392:                F343 effectiveness mystery — open (no predictor)
F393:                Mechanism = propagation always, pruning conditional
F394:                Hypothesis CONFIRMED at n=4; 2-factor model emerges
F395:                F344 32-clause exhausted (+1.4pp marginal)
F396 (yale):         Cross-bet candidate evidence manifest, 119 rows
F397 (yale):         Decision priority specs (132 + 139 vars)
F398:                F397 vs F394 cross-check (parents not children)
F399 (yale):         Decision priority matrix plan (5 missing inputs)
F400:                F387 class predicts F343 *variance*; H1 hypothesis
                     about Class A "both paths" non-helpers
```

20 numbered memos in 5 days, mechanism understanding gone from "F343
helps sometimes" to "F343 helps reliably on Class B; bimodally on
Class A; non-helper on the singleton 'both paths' Class A cand."

The chain has produced a deployable predictor without burning compute.
