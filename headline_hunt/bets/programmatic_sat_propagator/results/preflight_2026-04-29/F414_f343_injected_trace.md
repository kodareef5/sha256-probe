---
date: 2026-04-30
bet: programmatic_sat_propagator
status: F343_INJECTED_TRACE
parents: F393, F402, F413
---

# F414: F343-injected first-touch trace

## Summary

Conflict cap: 50000.
Each run appends the two F343 clauses to the aux-force CNF before invoking the programmatic propagator trace.

| Candidate | Audit | Return | Wall | Decisions | Δ decisions vs F413 | Backtracks | Δ backtracks vs F413 | Trace seen | First dW57_b0 | First low-bit shell key |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `bit2_ma896ee41_fillffffffff` | CONFIRMED | 2 | 4.001 | 375604 | +32628 (+9.51%) | 58174 | +201 (+0.35%) | 11/11 | dW57_b0@d0 | w2_57_b1@d10245 |
| `bit24_mdc27e18c_fillffffffff` | CONFIRMED | 2 | 3.806 | 384512 | +6896 (+1.83%) | 58733 | +183 (+0.31%) | 11/11 | dW57_b0@d0 | w2_57_b1@d26274 |
| `bit28_md1acca79_fillffffffff` | CONFIRMED | 2 | 3.659 | 353260 | +2243 (+0.64%) | 58050 | +292 (+0.51%) | 11/11 | dW57_b0@d0 | w2_57_b1@d35254 |

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
| `dW57_b0` | 12401 | 1 | 481 | 0 | 0 |
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
| `dW57_b0` | 12364 | 1 | 481 | 0 | 0 |
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
| `dW57_b0` | 12352 | 0 | 481 | 0 | 0 |
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

F413 showed that the baseline propagator already reaches the F343 aux variables early, so delayed discovery was not the bit2 explanation. F414 tests the stronger intervention: put the exact F343 clauses in the CNF and re-run the same first-touch trace.

The injected unit and pair clauses do not materially move first-touch timing: `dW57_b0`, `dW57_b22`, and `dW57_b23` are already assigned in the same early window seen in F413. That confirms delayed assignment of the F343 target vars is not the mechanism.

Bit2 still does not become a rescued case under this programmatic trace: its decision count increases by 9.51% versus F413 and backtracks also rise slightly. The helper candidates are mixed-to-worse under the propagator, which says this trace is a mechanism probe rather than a replacement for the plain CaDiCaL F343 matrix.

## Verdict

The bit2 outlier is not explained by late assignment of F343 target variables or by failure to front-load the two F343 clauses. The remaining useful hypotheses are clause-conflict involvement, learned-clause neighborhood differences, or a richer F344/F57-row intervention rather than another generic priority nudge.

## Compute Discipline

- 3 injected CNFs audited before solver launch.
- 3 solver runs appended with `append_run.py`; all three transient `/tmp/F414` CNFs audited as CONFIRMED.
- Logs: `/tmp/F414/*.stderr.log` and `/tmp/F414/*.stdout.log`.
