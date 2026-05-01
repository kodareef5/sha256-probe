---
date: 2026-05-01
bet: programmatic_sat_propagator
status: BIT24_HIGH_CLUSTER_CAP_COMPOSITION_MATRIX
parents: F422
---

# F423: bit24 high-cluster cap/composition sweep

## Setup

Conflict cap: 50000. Seeds: [0, 1, 2]. Candidate: `bit24_mdc27e18c_fillffffffff`.

F422 promoted high `actual_p1_a_57` bits `21-25` at cap64. F423 checks two questions: whether cap64 is locally optimal among cap32/cap64/cap96, and whether that high-cluster opening book composes with the F343 injected CNF.

Priority spec: `headline_hunt/bets/programmatic_sat_propagator/results/preflight_2026-04-29/F423_bit24_high_cluster_cap_composition_specs.json`.

## Mean Results

| Arm | Source | Mean decisions | Delta decisions | Mean backtracks | Delta backtracks | Mean cb_decide suggestions | Mean cb_propagate fires |
|---|---|---:|---:|---:|---:|---:|---:|
| `baseline_parent_F422` | F422 | 406585 | +0.00% | 58939 | +0.00% | 0 | 791 |
| `f343_parent_F422` | F422 | 404511 | -0.51% | 58857 | -0.14% | 0 | 743 |
| `high_21_25_cap32` | F423 | 363869 | -10.51% | 58180 | -1.29% | 32 | 1341 |
| `high_21_25_cap64_parent_F422` | F422 | 360376 | -11.37% | 57990 | -1.61% | 64 | 1298 |
| `high_21_25_cap96` | F423 | 327931 | -19.35% | 57440 | -2.54% | 96 | 1307 |
| `f343_high_21_25_cap32` | F423 | 387380 | -4.72% | 58778 | -0.27% | 32 | 1306 |
| `f343_high_21_25_cap64` | F423 | 387319 | -4.74% | 58611 | -0.56% | 64 | 1560 |
| `f343_high_21_25_cap96` | F423 | 437787 | +7.67% | 59061 | +0.21% | 96 | 1560 |

## Per-Seed Decisions

| Seed | high cap32 | high cap64 (F422) | high cap96 | F343+high cap32 | F343+high cap64 | F343+high cap96 |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | 362501 | 362338 | 358563 | 405208 | 387176 | 438275 |
| 1 | 366382 | 363171 | 358170 | 385087 | 385407 | 414703 |
| 2 | 362725 | 355619 | 267060 | 371846 | 389374 | 460383 |

## Read

Best mean decisions arm is high_21_25_cap96: 327931 (-19.35% vs inherited F422 baseline). High-cluster priority is better without F343 in this cap band.

The cap result is encouraging but not yet deployment-grade. Cap32, cap64, and cap96 are all positive on seeds 0/1, but cap96's mean is dominated by a large seed-2 drop to 267060 decisions. Treat cap96 as the new lead to replicate, not as a finished optimum.

F343 composition is negative. Even the best composition arm, `f343_high_21_25_cap64`, only reaches -4.74% versus baseline, far behind pure high-cluster cap32/cap64/cap96. The F343 clause nudge and actual-register opening book appear to interfere on bit24.

## Next Gate

Run a pure high-cluster replication around cap96: cap80/cap96/cap112 over more seeds, with no F343 composition unless the pure cap sweep remains stable.

## Compute Discipline

- 15 new F423 solver runs audited before solve and appended with `append_run.py`.
- Baseline, F343, and high cap64 controls are inherited from F422 to avoid duplicate registry rows.
- Logs: `/tmp/F423/*.stderr.log` and `/tmp/F423/*.stdout.log`.
