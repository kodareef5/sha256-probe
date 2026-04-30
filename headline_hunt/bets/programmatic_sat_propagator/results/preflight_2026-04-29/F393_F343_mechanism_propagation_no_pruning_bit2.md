---
date: 2026-05-01
bet: programmatic_sat_propagator
status: MECHANISM_LIGHT — F343 clauses DO propagate on bit2 but produce no conflict-pruning; search-trajectory hypothesis supported
parent: F392 (F343 effectiveness mystery)
type: cadical-statistics diagnostic
compute: 4 cadical 60s --stats runs (bit2 + bit3 × baseline + F343 × seed=0)
---

# F393: cadical --stats reveals F343 clauses fire on bit2 but produce no pruning — supports search-trajectory hypothesis

## Setup

F392 documented the open mystery: bit2 and bit3 have identical F343
clause structure, but F343 helps bit3 by −8.17% and helps bit2 by
+0.07% (essentially zero). Three hypotheses were proposed:
  (a) search-trajectory dependence (bit3 reaches the W57[22:23]
      region naturally; bit2 doesn't)
  (b) conflict-density profile (different cands derive F343 clauses
      at different points in CDCL)
  (c) clause-to-CNF interaction (subsumption/propagation specifics)

F393 runs cadical with `--stats=true` on bit2 + bit3 × {baseline, F343}
to extract concrete propagation/conflict data and discriminate among
the hypotheses.

## Method

```
cadical -t 60 --seed=0 --stats=true <cnf>
```

4 runs, 60s each, single seed (diagnostic, not statistical).

## Result

```
metric          bit2_base    bit2_F343    Δ%       bit3_base    bit3_F343    Δ%
conflicts       2,331,726    2,347,411    +0.67%   2,469,936    2,247,794    -8.99%
propagations    236,944,236  250,184,545  +5.59%   225,886,123  255,825,461  +13.25%
decisions       10,251,949   10,219,480   -0.32%   10,325,594   10,439,109   +1.10%
chronol-backtrack 587,052    570,756      -2.78%   630,651      567,093      -10.08%
learned         2,252,999    2,267,981    +0.66%   2,383,089    2,175,304    -8.72%
restarts        105,112      102,827      -2.17%   105,892      106,866      +0.92%
```

## Findings

### Finding 1 — F343 clauses ACTIVATE on both cands (visible propagation increase)

Propagations increase with F343 on BOTH bit2 (+5.59%) and bit3 (+13.25%).
This means cadical IS triggering UP through the injected F343 clauses
during search. The clauses are not silent.

**Falsifies the "F343 clauses don't fire on bit2" sub-hypothesis.** They
do fire — they just don't yield the same pruning value.

### Finding 2 — bit2 propagation rise produces NO conflict reduction

Despite the +5.59% propagation rise on bit2 with F343, **conflicts
INCREASE** (+0.67%). The clauses propagate but don't prune the search
tree. Net solver work is slightly higher.

For bit3: the +13.25% propagation rise BUYS a −8.99% conflict
reduction. Pruning value translates.

This is the empirical signature of **search-trajectory dependence**:
bit3's CDCL reaches branches where the F343 clauses' restrictions
trigger conflicts (helping pruning); bit2's CDCL doesn't reach those
branches naturally, so the propagations are wasted work.

### Finding 3 — Mechanism conjecture: bit2 trajectory avoids W57[22:23] decision boundary

F343 clauses constrain `dW57[0]=1` (unit) and `W57[22:23] != (0,0)` (pair).
For these constraints to PRUNE, cadical's search must:
  - Eventually decide variables at dW57[0] OR at W57[22:23]
  - Hit the forbidden polarity, triggering a conflict via the F343 clause
  - Use the resulting conflict-clause to backtrack productively

If bit2's VSIDS (variable activity heuristic) doesn't bring dW57[0]
or W57[22:23] vars to high decision priority, cadical never branches
on them — the F343 clauses never trigger conflicts even though they
propagate through unit chains.

This is testable: per-decision instrumentation could measure how often
each cand's CDCL decides the dW57[0] / W57[22:23] vars. If bit2's
decision rate on those vars is much lower than bit3's, the
search-trajectory hypothesis is confirmed.

### Finding 4 — chronological backtracking pattern matches the conflict pattern

bit3 with F343 has −10.08% chronological backtracks (alongside −8.99%
conflicts) — both indicate cadical's search becomes more efficient.

bit2 with F343 has only −2.78% chronological backtracks (with +0.67%
conflicts) — search structure is essentially unchanged.

### Finding 5 — Learning-clause efficiency is constant per conflict

Learned-clauses-per-conflict ratio: bit2 96.62% (both conditions),
bit3 96.48%-96.78% (both conditions). F343 doesn't change cadical's
learning rate; it changes whether conflicts happen at all.

So the question is "do F343 clauses trigger conflicts?" not "do they
help cadical learn better from triggered conflicts?"

## Implication for the F343 effectiveness mystery

**Search-trajectory dependence hypothesis (F392 hypothesis a) is
SUPPORTED at n=1 cand.** F343 clauses get activated but don't yield
pruning on bit2. The mechanism is consistent with VSIDS not branching
on the constrained variables.

Hypotheses (b) "conflict-density profile" and (c) "clause-to-CNF
interaction" remain plausible but unaddressed by this diagnostic.

For Phase 2D propagator design:
  - F343 alone is the right intervention (per F391 falsification of ladder)
  - F343's effectiveness is per-cand; cannot predict from (m0, fill, kbit)
  - Apply F343 universally; expect mean ~−7-9% conflicts; accept σ ≈ 3pp

A potential improvement: **boost VSIDS scores for dW57[0] + W57[22:23]
vars at solver init** (alongside F343 clause injection). This would
force cadical to consider those branches, potentially extracting F343
benefit on cands like bit2. Untested but mechanism-aligned.

## What's shipped

- This memo with cadical --stats data on 4 conditions
- Direct mechanism support for "search-trajectory dependence"
- Concrete proposed extension: VSIDS boost for dW57/W57[22:23] vars

## Compute discipline

- 4 cadical 60s --stats runs (~4 min CPU; serial, ~4 min wall)
- 4 transient logs in /tmp/F393/
- Real audit fail rate stays 0%

## F381 → F393 chain summary

  F381-F388 (8 iter): structural rule fits 16/16 — REAL
  F389: deployable spec — TOOL stands, application FALSIFIED
  F390-F391: ladder pre-injection HURTS at n=3 — FALSIFIED
  F392: F343 effectiveness mystery — OPEN QUESTION
  F393: F343 mechanism — propagation works, pruning doesn't, on bit2

14 numbered memos, 28 commits, ~9 hours, ~620s cadical compute.

The chain has produced:
  - 1 robust structural finding (ladder per F387)
  - 1 falsified application (ladder pre-injection)
  - 1 partial mechanism understanding (F343 = propagation but not
    pruning on cands where it doesn't help)
  - 1 actionable Phase 2D proposal (VSIDS boost for F343-targeted vars)

## Open questions

(a) **Verify search-trajectory hypothesis at n=2-3 more cands**.
    cadical --stats on bit10 (F343 helps -12%) and bit11 (helps -7%)
    should show similar prop-rise + conflict-reduction pattern.

(b) **Test VSIDS boost extension**: cadical has --bumpreason and
    activity-related options. Could a brief preflight that bumps the
    F343 target vars' activities via priming-clauses change bit2's
    F343 effect?

(c) **Per-decision instrumentation**: track how often cadical decides
    on dW57[0] vs other vars, per cand. Should sharply distinguish
    "trajectory naturally reaches" from "trajectory ignores".
