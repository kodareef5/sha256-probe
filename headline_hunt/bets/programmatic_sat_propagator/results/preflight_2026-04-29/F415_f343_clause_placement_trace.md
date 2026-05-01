---
date: 2026-04-30
bet: programmatic_sat_propagator
status: F343_CLAUSE_PLACEMENT_TRACE
parents: F392, F413, F414
---

# F415: F343 clause-placement trace

## Summary

Conflict cap: 50000. Same two F343 clauses as F414, but inserted immediately after the `p cnf` header instead of appended at EOF.

| Candidate | Audit | Return | Wall | Decisions | Δ vs F413 | Δ vs F414 append | Backtracks | Δ backtracks vs F414 | Trace seen | First low-bit shell key |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `bit2_ma896ee41_fillffffffff` | CONFIRMED | 2 | 3.898 | 375604 | +32628 (+9.51%) | +0 (+0.00%) | 58174 | +0 (+0.00%) | 11/11 | w2_57_b1@d10245 |
| `bit24_mdc27e18c_fillffffffff` | CONFIRMED | 2 | 3.860 | 384512 | +6896 (+1.83%) | +0 (+0.00%) | 58733 | +0 (+0.00%) | 11/11 | w2_57_b1@d26274 |
| `bit28_md1acca79_fillffffffff` | CONFIRMED | 2 | 3.808 | 353260 | +2243 (+0.64%) | +0 (+0.00%) | 58050 | +0 (+0.00%) | 11/11 | w2_57_b1@d35254 |

## Injected Clauses

| Candidate | Unit | Pair forbid | DIMACS clauses |
|---|---|---|---|
| `bit2_ma896ee41_fillffffffff` | dW57[0]=1 | dW57[22:23]!=(0, 0) | `[12401]` `[12423, 12424]` |
| `bit24_mdc27e18c_fillffffffff` | dW57[0]=1 | dW57[22:23]!=(0, 1) | `[12364]` `[12386, -12387]` |
| `bit28_md1acca79_fillffffffff` | dW57[0]=0 | dW57[22:23]!=(0, 0) | `[-12352]` `[12374, 12375]` |

## First-Touch Events

### bit2_ma896ee41_fillffffffff

| Label | Var | Value | Assignment | Decisions | Backtracks |
|---|---:|---:|---:|---:|---:|
| `dW57_b0` | 12401 | 1 | 1 | 0 | 0 |
| `dW57_b23` | 12424 | 1 | 676 | 512 | 0 |
| `dW57_b22` | 12423 | 1 | 677 | 513 | 0 |
| `w1_57_b0` | 2 | 1 | 3358 | 8679 | 346 |
| `w2_57_b0` | 130 | 0 | 3359 | 8679 | 346 |
| `w2_57_b1` | 131 | 0 | 4980 | 10245 | 420 |
| `w1_57_b22` | 24 | 1 | 14489 | 28566 | 1288 |
| `w1_57_b23` | 25 | 1 | 14490 | 28567 | 1288 |
| `w2_57_b22` | 152 | 1 | 14527 | 28686 | 1288 |
| `w2_57_b23` | 153 | 0 | 14531 | 28686 | 1288 |
| `w2_58_b1` | 163 | 1 | 14535 | 28696 | 1288 |

### bit24_mdc27e18c_fillffffffff

| Label | Var | Value | Assignment | Decisions | Backtracks |
|---|---:|---:|---:|---:|---:|
| `dW57_b0` | 12364 | 1 | 1 | 0 | 0 |
| `dW57_b23` | 12387 | 1 | 676 | 510 | 0 |
| `dW57_b22` | 12386 | 1 | 677 | 510 | 0 |
| `w1_57_b0` | 2 | 0 | 11374 | 24559 | 758 |
| `w2_57_b0` | 130 | 1 | 11375 | 24559 | 758 |
| `w2_57_b1` | 131 | 1 | 12683 | 26274 | 838 |
| `w1_57_b22` | 24 | 1 | 20910 | 33235 | 1321 |
| `w1_57_b23` | 25 | 1 | 20911 | 33236 | 1321 |
| `w2_57_b22` | 152 | 0 | 20944 | 33346 | 1321 |
| `w2_57_b23` | 153 | 0 | 20946 | 33346 | 1321 |
| `w2_58_b1` | 163 | 1 | 20948 | 33359 | 1321 |

### bit28_md1acca79_fillffffffff

| Label | Var | Value | Assignment | Decisions | Backtracks |
|---|---:|---:|---:|---:|---:|
| `dW57_b0` | 12352 | 0 | 1 | 0 | 0 |
| `dW57_b23` | 12375 | 1 | 676 | 512 | 0 |
| `dW57_b22` | 12374 | 1 | 677 | 513 | 0 |
| `w1_57_b0` | 2 | 1 | 18000 | 35253 | 1335 |
| `w2_57_b0` | 130 | 1 | 18001 | 35253 | 1335 |
| `w2_57_b1` | 131 | 1 | 18003 | 35254 | 1335 |
| `w1_57_b22` | 24 | 1 | 18010 | 35275 | 1335 |
| `w1_57_b23` | 25 | 1 | 18011 | 35276 | 1335 |
| `w2_57_b22` | 152 | 1 | 18036 | 35394 | 1335 |
| `w2_57_b23` | 153 | 0 | 18037 | 35394 | 1335 |
| `w2_58_b1` | 163 | 1 | 18040 | 35406 | 1335 |

## Initial Read

F392 listed watch-list / clause ordering as a possible explanation for per-candidate F343 variance. F414 appended the F343 clauses; F415 front-loads the same clauses to test that idea without changing the clause content.

Front-loading moves the unit-clause variable `dW57_b0` from assignment index 481 to assignment index 1, but it does not move the pair-clause variables or any decision/backtrack counters versus F414. Bit2 remains worse than the no-injection F413 propagator baseline and is not rescued by clause placement.

## Verdict

Clause placement is not the missing bit2 mechanism in this programmatic propagator path. The remaining useful work is either deeper conflict-involvement instrumentation or a different decision-priority primitive than the bounded `cb_decide` nudge already tested.

## Compute Discipline

- 3 front-loaded injected CNFs audited before solver launch; all audited CONFIRMED.
- 3 solver runs appended with `append_run.py`.
- Logs: `/tmp/F415/*.stderr.log` and `/tmp/F415/*.stdout.log`.
