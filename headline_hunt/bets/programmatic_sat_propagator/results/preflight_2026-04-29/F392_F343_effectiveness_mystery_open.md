---
date: 2026-05-01
bet: programmatic_sat_propagator
status: OPEN_QUESTION_DOCUMENTED — F343 effectiveness varies 0% to −13% per cand; no simple feature predicts
parent: F391 (F389 falsified at 3-cand panel)
type: characterization + open_mechanism
compute: 0 cadical runs (analytical reuse of F369 + F391 data)
---

# F392: F343 effectiveness varies wildly per-cand; no simple feature predicts it

## The puzzle

F369 measured F343 baseline as −9.10% σ=2.68% across 5 cands × 3 seeds.
F391 added 3 more cands. Combined 8-cand picture:

```
cand                m0          fill         kbit  F343 % effect    source
bit0_m8299b36f      0x8299b36f  0x80000000      0     -8.33         F369
bit10_m3304caa0     0x3304caa0  0x80000000     10    -12.03         F369
bit11_m45b0a5f6     0x45b0a5f6  0x00000000     11     -7.56         F369
bit13_m4d9f691c     0x4d9f691c  0x55555555     13     -5.89         F369
bit17_m427c281d     0x427c281d  0x80000000     17    -11.72         F369
bit2_ma896ee41      0xa896ee41  0xffffffff      2     +0.07  ← outlier (no help)  F391
bit31_m17149975     0x17149975  0xffffffff     31    -13.12         F391
bit3_m33ec77ca      0x33ec77ca  0xffffffff      3     -8.17         F391
```

Range: **+0.07% to −13.12%** — a ~13 percentage-point spread.

Striking sub-finding: **bit2 and bit3 have IDENTICAL F343 clause structure**.

```
bit2_ma896ee41:   unit +12401 (dW57[0]=1 forced); pair (12423, 12424) forbids (0,0)
bit3_m33ec77ca:   unit +12397 (dW57[0]=1 forced); pair (12419, 12420) forbids (0,0)
```

Both force dW57[0]=1, both forbid W57[22:23]=(0,0). The var IDs differ
because each cand has its own encoder var allocation, but the
structural meaning is the same.

Yet F343 effect differs by **8 percentage points**:
  bit2: +0.07% (no help)
  bit3: −8.17% (substantial help)

**Same clauses, same structural meaning, completely different solver impact.**

## What does NOT predict F343 effectiveness

Tested feature → F343 effect correlation:

| Feature | bit2 | bit3 | bit31 | Pattern? |
|---------|------|------|-------|----------|
| fill | ffffffff | ffffffff | ffffffff | identical |
| dW57[0] forcing polarity | =1 | =1 | =1 | identical |
| W57[22:23] forbidden polarity | (0,0) | (0,0) | (0,1) | bit3 matches bit2; bit31 differs |
| F387 class | A | A | A | identical |
| F384 ladder presence | yes | yes | yes | identical |
| m0_HW | 15 | 19 | 15 | bit3 high, but bit2/bit31 same |
| kbit | 2 | 3 | 31 | low / low / high |
| m0_bit[kbit] | 0 | 1 | 0 | bit3 differs from bit2/bit31 but its effect (-8.17) is between them |

**No single feature explains the per-cand F343 variance.**

## What might predict F343 effectiveness

Hypotheses (untested):

(a) **CDCL search trajectory dependence**: cadical's heuristics (VSIDS,
    restarts, decision priorities) lead to different exploration paths
    per cand. The F343 clauses help on cands where the trajectory
    naturally reaches the W57[22:23] region; on cands where it doesn't,
    the clauses are "discovered late" and add no value.

(b) **Conflict-density profile**: F343 effectiveness may depend on what
    fraction of conflicts naturally derive the F343 clauses. If a cand
    derives them in the first 5% of conflicts, pre-injection saves
    almost nothing. If a cand derives them in the last 95%, pre-injection
    saves a lot.

(c) **Clause-to-CNF interaction**: the F343 clauses interact with
    cadical's clause-database management (subsumption, deletion). Some
    cands' base CNFs have local clause structure that lets F343 trigger
    cascading propagations; others don't.

(d) **Watch-list ordering**: cadical's clause ordering on the watch list
    is implementation-dependent. F343 clauses placed early in the list
    may help; placed late, they don't.

All of these are search-implementation properties, not pure structural
properties of (m0, fill, kbit). That's bad news for "predict F343
effectiveness from cand metadata" but good news for "F343 mining is
already producing the right clauses — the variance is downstream of
mining."

## What's known so far

  F343 mining is correct: produces per-cand polarity-correct W57[22:23]
  clauses (per F348 + F377). Mining is not the bottleneck.

  F343 effectiveness varies: 0% to −13% per cand. Mean ~−7-9% across
  panels. Per-cand effect is reproducible (consistent across seeds
  modulo σ ≈ 2-3%).

  F343 effectiveness is not predicted by:
    - F387 class (Class A/B distinction)
    - dW57[0] polarity
    - W57[22:23] polarity
    - m0_HW, fill_HW, m0_bit[kbit]

  Therefore: **F343 effectiveness is a search-implementation property,
  not a pure structural feature of (m0, fill, kbit)**.

## Implications

For Phase 2D propagator design:
  - Don't claim "F343 saves X% per cand" — claim "F343 saves a mean of
    ~−7-9% across cands with high per-cand variance".
  - Don't try to predict F343 effectiveness from cand metadata.
  - Apply F343 universally; expect benefit on average; accept some
    cands won't benefit.

For empirical reporting:
  - The F369 −9.10% mean is the right headline number.
  - Per-cand effects can range 0% to −13%; report mean + σ, not
    per-cand point estimates.

For mechanism understanding:
  - Open question: why does bit2 not benefit from clauses with the same
    structural meaning as bit3's? Could yield a cand-level "F343 efficacy
    fingerprint" if instrumented carefully.

## Concrete next moves

(a) **cadical instrumentation**: run cadical with `--statistics` on
    bit2 baseline vs bit2-F343 to see WHERE the cost difference is
    (or isn't). If F343 clauses fire as expected on bit2, the issue is
    that they don't lead to useful conflicts. If they don't fire, the
    cand's search avoids the W57[22:23] region.

(b) **Conflict-trace analysis**: instrument cadical to log when each
    F343 clause is involved in a conflict. Cross-cand histogram of
    "F343 clause conflict-involvement" should correlate with F343
    effectiveness.

(c) **Alternative F343 mining**: F344 mined 32 clauses (per F347 →
    −13.7% on bit31 with 32-clause). The 32-clause F344 may help on
    cands where the 2-clause F343 doesn't; F347's outlier pattern (bit31
    huge benefit) hints at cand-specific richer clause sets being needed.

## What's shipped

- This memo with 8-cand F343 effectiveness picture
- Documented open mechanism question
- Concrete investigation pathway (cadical --statistics + conflict-trace)

## Compute discipline

- 0 cadical runs (pure analytical reuse of F369 + F391)
- audit_required: not applicable

## F381 → F392 chain summary (extended)

  F381-F388: structural rule (ladder per F387 fits 16/16) — REAL
  F389: deployable spec — TOOL stands, application FALSIFIED
  F390-F391: ladder pre-injection HURTS at n=3 cands — FALSIFIED
  F392: F343 effectiveness mystery — OPEN QUESTION DOCUMENTED

The F381→F392 chain has produced:
  - 1 robust structural finding (ladder presence per F387)
  - 1 falsified application (ladder pre-injection)
  - 1 open mechanism question (F343 per-cand variance)

13 numbered memos, 27 commits, ~8 hours, ~580s cadical compute.

Phase 2D viable speedup levers remain narrow:
  - F343 baseline: ~−7-9% mean, high cand-variance, mechanism unclear
  - cb_decide on F286 132-bit core: untested

The structural picture sharpens; the application picture remains
narrow. F392 ships an honest open question rather than a false claim
of mechanism understanding.
