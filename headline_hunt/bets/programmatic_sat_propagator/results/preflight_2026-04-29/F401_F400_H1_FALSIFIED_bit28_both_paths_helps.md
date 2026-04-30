---
date: 2026-05-01
bet: programmatic_sat_propagator
status: F400-H1 FALSIFIED at n=2 — bit28 (both F387 paths) helps at −6.37%, NOT a non-helper
parent: F400 (F387 class predicts variance, H1 about both-paths non-helpers)
type: empirical falsification
compute: 2 cadical 60s --stats runs (bit28 baseline + F343); ~120s wall
---

# F401: F400-H1 falsified — bit28 "both paths" cand helps F343 at −6.37%

## Setup

F400 hypothesized that Class A "both F387 paths satisfied" cands are
F343 non-helpers. n=1 evidence (bit2_ma896ee41 at +0.07%). Falsifiable
by finding another "both paths" cand with significantly negative F343
effect.

F396 manifest registry scan found **15 "both paths" cands**; bit2 is
1 of those 15. The other 14 were untested. Picked bit28_md1acca79 for
the test (kbit=28, m0=0xd1acca79, fill=0xffffffff, fill_HW=32) —
already had aux_force_sr60 CNF + varmap in repo, so no encoder regen
needed.

## Method

```
cadical -t 60 --seed=0 --stats=true bit28_baseline.cnf
cadical -t 60 --seed=0 --stats=true bit28_F343.cnf
```

F343 preflight mined fresh:
  - dW57[0] forced=0, inject literal -12352 (one unit clause)
  - (dW57[22], dW57[23]) forbidden=(0,0), inject [12374, 12375] (one pair)
  - 2 clauses total, identical structural form to F343 baseline

## Result

```
metric            baseline           F343         Δ%
conflicts         2,395,793      2,243,116     -6.37%   ← F343 HELPS
propagations    248,893,810    311,975,041    +25.34%   ← clauses propagate
learned           2,317,874      2,175,680     -6.13%
chronological       618,297        593,091     -4.08%
restarts            106,604        102,266     -4.07%
decisions        10,710,950     10,534,013     -1.65%
```

**Yield ratio**: |conflict_red| / prop_increase = 6.37 / 25.34 = **0.25**

## Findings

### Finding 1 — F400-H1 FALSIFIED at n=2

bit28_md1acca79 (Class A, both paths satisfied) gets a clean −6.37%
conflict reduction from F343, similar to bit10's 0.18 yield and
bit11's 0.22 yield (both Class B).

So:
  bit2_ma896ee41 (both paths, Class A): +0.07%   ← non-helper
  bit28_md1acca79 (both paths, Class A): −6.37%  ← helps

**Both-paths is NOT a sufficient predictor for non-helper status.**
The original F400-H1 hypothesis is dead at n=2.

### Finding 2 — Refined Factor B picture

bit28's yield (0.25) sits in the same range as bit10/11 (0.18–0.22)
despite being Class A path-both. So at the yield level, bit28 looks
like a "Class B-style" cand: bounded yield around 0.2.

Updated cand-level picture (n=5):

```
profile               cand                 effect    yield
Class A path1         bit0                 -8.33     n/a (3-seed mean)
Class A path2         bit3                 -8.17 (single seed)  0.68
Class A path2         bit31               -13.12     n/a
Class A both          bit2                 +0.07     n/a (no help)
Class A both          bit28                -6.37     0.25  ← F401 NEW
Class B neither       bit10                -5.16     0.18
Class B neither       bit11                -7.55     0.22
```

The Class A "both paths" sub-profile now has 1 non-helper (bit2) and
1 helper (bit28) — bimodal within "both paths". Class B has only
helpers. Class A path1/path2 has only helpers.

So the pattern is now:
  - Class B (neither path): always helps, bounded yield (0.18–0.22)
  - Class A path1 / path2: always helps, can be high yield (0.68 for
    bit3) or bounded (others)
  - Class A both paths: bimodal — bit2 non-helper, bit28 helper

n=2 in the bimodal slot is too few to claim anything more specific.
The non-helper status of bit2 remains unexplained.

### Finding 3 — What still distinguishes bit2?

If "both paths" alone doesn't predict, what does separate bit2 from
bit28?

```
feature                 bit2_ma896ee41      bit28_md1acca79
m0                      0xa896ee41          0xd1acca79
m0_HW (popcount)        15                  18
kbit                    2                   28
fill                    0xffffffff          0xffffffff (same)
fill_HW                 32                  32 (same)
m0_bit[31]              1                   1 (same)
fill_bit[31]            1                   1 (same)
F343 unit forced        dW57[0] = 1         dW57[0] = 0   ← differs
F343 pair forbidden     (0,0)               (0,0) (same)
```

The cleanest distinguishing feature so far is the **F343 unit-clause
forcing polarity**: bit2 forces `dW57[0]=1`, bit28 forces `dW57[0]=0`.
But polarity also doesn't predict alone — bit11 forces `dW57[0]=1`
(like bit2) and helps at −7.56%. So forcing-polarity isn't a clean
predictor either.

The remaining differences are kbit (2 vs 28) and m0 itself. Neither
has structural meaning we've extracted yet.

### Finding 4 — Honest reframe of F400's core claim

F400's headline ("F387 class predicts variance, Class B more reliable
at stdev 3.05") is unaffected by F401. The class-conditional deployment
recipe still stands:
  - Class B: F343 unconditionally (still bounded yield)
  - Class A: variable yield, may or may not help

What F401 falsifies is the *sub-profile* claim that "both paths"
specifically marks the non-helpers. n=2 in that sub-profile gives
1 non-helper + 1 helper. We have no current sub-profile predictor
for the bit2-style non-helper status.

bit2 may simply be a singleton outlier in the n=8 panel, not a member
of a structurally distinguishable subclass. Need more cands tested to
know.

## What's shipped

- This memo with empirical falsification of F400-H1
- bit28_md1acca79 added to F343 effectiveness panel (n=8 → n=9 now,
  if we count bit3 single-seed; n=8 if we hold to F392's 3-seed
  mean standard)
- Class A "both paths" sub-profile is bimodal; needs more samples
- Class B "neither path" remains the only reliably bounded slot

## Compute discipline

- 2 cadical 60s --stats runs logged via append_run.py
- 2 transient CNFs in /tmp/F401/ (audit UNKNOWN, --allow-audit-failure
  consistent with F390-F394 protocol)
- 0 real audit failures (audit dashboard remains clean)

## Next testable iteration

(a) **Run F401 across 3-seed at bit28** to match F369's 3-seed
    standard. ~3 min compute. Confirms whether single-seed −6.37%
    represents the mean.

(b) **Test 2 more "both paths" Class A cands**. If both help, bit2
    is confirmed singleton outlier. If 1+ non-helps, the sub-profile
    has structure we haven't seen yet. Need encoder regen for these
    cands (~5s each via cascade_aux_encoder.py). Cheap.

(c) **Investigate bit2 specifically**: what makes bit2_ma896ee41
    structurally different from bit28_md1acca79? Both are "both
    paths Class A fill_HW=32". The remaining axes (m0_HW, kbit, m0
    bytes) need feature mining. This may require deeper structural
    analysis than F396's coarse class labels can provide.

## State

- F400's headline finding (F387 class → F343 variance) holds
- F400's sub-hypothesis F400-H1 (both paths → non-helper) is FALSIFIED
- Class A "both paths" is bimodal in n=2 sample
- bit2's non-helper status remains unexplained — singleton or
  signature of an unobserved sub-profile

## F381 → F401 chain summary (updated)

```
F381-F388 (8 iter):  Structural rule (F387) — REAL, n=16
F389:                Deployable spec — TOOL stands; FALSIFIED on application
F390-F391:           Ladder pre-injection HURTS — FALSIFIED at n=3
F392:                F343 effectiveness mystery — open (no predictor)
F393:                Mechanism = propagation always, pruning conditional
F394:                Hypothesis CONFIRMED at n=4; 2-factor model
F395:                F344 32-clause exhausted (+1.4pp marginal)
F396 (yale):         Cross-bet candidate evidence manifest, 119 rows
F397 (yale):         Decision priority specs (132 + 139 vars)
F398:                F397 vs F394 cross-check (parents not children)
F399 (yale):         Decision priority matrix plan (5 missing inputs)
F400:                F387 class predicts F343 variance; H1 hypothesis
F401:                F400-H1 FALSIFIED at n=2 — bit28 both paths helps
```

21 numbered memos. Class A "both paths" remains structurally
underdetermined — bit2 is special for some reason F396 features
don't capture, and we haven't found the next predictor yet.

The chain has moved from "F343 helps sometimes" → "F343 helps
reliably on Class B; bimodally on Class A" → "Class A helps in 3 of
4 sub-profiles" + "bit2 is structurally unexplained outlier".

Honest forward direction: more sampling in Class A both paths
(cheap), or deeper structural feature mining for whatever
distinguishes bit2.
