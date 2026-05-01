---
date: 2026-04-30
bet: programmatic_sat_propagator
status: F343_LEARNER_TOUCH_TRACE
parents: F392, F413, F414, F416
---

# F417: learned-clause touch trace for F343 variables

## Summary

Conflict cap: 50000. Learner exports all learned clauses and counts clauses touching `dW57_b0`, `dW57_b22`, or `dW57_b23`. Each candidate is run as baseline and F343-injected.

| Candidate | Condition | Audit | Decisions | Backtracks | Learned exported | Learned touching F343 vars | Touch % | Per-var touch counts |
|---|---|---|---:|---:|---:|---:|---:|---|
| `bit2_ma896ee41_fillffffffff` | baseline | CONFIRMED | 342976 | 57973 | 47128 | 0 | 0.000% |  |
| `bit2_ma896ee41_fillffffffff` | f343 | CONFIRMED | 375604 | 58174 | 46782 | 0 | 0.000% |  |
| `bit24_mdc27e18c_fillffffffff` | baseline | CONFIRMED | 377616 | 58550 | 46852 | 0 | 0.000% |  |
| `bit24_mdc27e18c_fillffffffff` | f343 | CONFIRMED | 384512 | 58733 | 46789 | 0 | 0.000% |  |
| `bit28_md1acca79_fillffffffff` | baseline | CONFIRMED | 351017 | 57758 | 46870 | 0 | 0.000% |  |
| `bit28_md1acca79_fillffffffff` | f343 | CONFIRMED | 353260 | 58050 | 47007 | 0 | 0.000% |  |

## F343 Delta With Same Learner

| Candidate | Δ decisions | Δ backtracks | Δ learned exported | Δ learned touching F343 vars |
|---|---:|---:|---:|---:|
| `bit2_ma896ee41_fillffffffff` | +32628 (+9.51%) | +201 (+0.35%) | -346 (-0.73%) | +0 |
| `bit24_mdc27e18c_fillffffffff` | +6896 (+1.83%) | +183 (+0.31%) | -63 (-0.13%) | +0 |
| `bit28_md1acca79_fillffffffff` | +2243 (+0.64%) | +292 (+0.51%) | +137 (+0.29%) | +0 |

## Touch Samples

### bit2_ma896ee41_fillffffffff / baseline
No touching learned-clause samples exported.

### bit2_ma896ee41_fillffffffff / f343
No touching learned-clause samples exported.

### bit24_mdc27e18c_fillffffffff / baseline
No touching learned-clause samples exported.

### bit24_mdc27e18c_fillffffffff / f343
No touching learned-clause samples exported.

### bit28_md1acca79_fillffffffff / baseline
No touching learned-clause samples exported.

### bit28_md1acca79_fillffffffff / f343
No touching learned-clause samples exported.

## Initial Read

This is instrumentation rather than an optimization. It gives a direct counter for whether learned clauses touch the F343 row variables under the same programmatic runner used in F413-F416.

The key result is zero touch across all six arms: 46k-47k learned clauses were exported per run, and none contained `dW57_b0`, `dW57_b22`, or `dW57_b23`. The F343 clauses can still propagate as original clauses, but they are not entering the learned-clause neighborhood of this programmatic trace under the 50k conflict cap.

That makes the bit2 failure less mysterious in this runner: the F343 vars are visible early, but they are not part of conflict learning. Clause placement and phase hints cannot fix that. A real rescue would need variable-activity/selection pressure strong enough to make conflicts actually resolve through the F343 row, or a different structural clause family whose variables already sit inside the learned neighborhood.

## Verdict

F417 kills the "F343 clauses are quietly involved in conflict learning" hypothesis for this programmatic path. The next useful instrumentation target is broader learned-neighborhood discovery: find which W57/W58 or aux vars *do* appear in learned clauses, then aim operators at that neighborhood instead of repeatedly nudging the untouched F343 triple.

## Compute Discipline

- 6 CNFs audited before solver launch.
- 6 solver runs appended with `append_run.py`.
- Logs: `/tmp/F417/*.stderr.log` and `/tmp/F417/*.stdout.log`.
