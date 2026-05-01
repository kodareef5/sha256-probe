---
date: 2026-05-01
bet: programmatic_sat_propagator
status: BIT24_HIGH_CLUSTER_REPLICATION_MATRIX
parents: F423
---

# F424: bit24 high-cluster cap replication

## Setup

Conflict cap: 50000. Seeds: [3, 4, 5, 6, 7]. Candidate: `bit24_mdc27e18c_fillffffffff`.

F423 made cap96 the lead, but its mean was seed-2-heavy. F424 reruns pure high-cluster priority with same-seed controls on seeds 3-7: baseline, cap64, cap80, cap96, and cap112. No F343 composition arms are included.

Priority spec: `headline_hunt/bets/programmatic_sat_propagator/results/preflight_2026-04-29/F424_bit24_high_cluster_replication_specs.json`.

## Replication Mean Results

| Arm | Mean decisions | Delta decisions | Mean backtracks | Delta backtracks | Mean cb_decide suggestions | Mean cb_propagate fires |
|---|---:|---:|---:|---:|---:|---:|
| `baseline` | 412944 | +0.00% | 59069 | +0.00% | 0 | 791 |
| `high_21_25_cap64` | 359681 | -12.90% | 58063 | -1.70% | 64 | 1298 |
| `high_21_25_cap80` | 360310 | -12.75% | 58197 | -1.48% | 80 | 1304 |
| `high_21_25_cap96` | 358431 | -13.20% | 58127 | -1.59% | 96 | 1307 |
| `high_21_25_cap112` | 362149 | -12.30% | 58060 | -1.71% | 112 | 1473 |

## Per-Seed Decisions

| Seed | baseline | cap64 | cap80 | cap96 | cap112 |
|---:|---:|---:|---:|---:|---:|
| 3 | 410658 | 362528 | 355340 | 358347 | 365888 |
| 4 | 415632 | 352786 | 364548 | 362989 | 361273 |
| 5 | 413352 | 360520 | 356559 | 352660 | 358909 |
| 6 | 409664 | 357956 | 359855 | 360203 | 364058 |
| 7 | 415416 | 364616 | 365250 | 357958 | 360616 |

## Read

Seeds 3-7 replication best arm is high_21_25_cap96: 358431 decisions (-13.20% vs same-seed baseline). Cap96 survived the extra seed panel.

The stronger result is the operator, not the exact cap. Every tested high-cluster cap cuts mean decisions by 12.30-13.20% on the same-seed panel, and cap96 only beats cap64 by about 1250 mean decisions. Per-seed winners are split across cap80, cap64, and cap96, so cap96 is a slight current default rather than a sharp optimum.

Historical context: F422 cap64 was -11.37% on seeds 0-2; F423 cap96 was -19.35% on seeds 0-2 but heavily seed-2-driven. This panel is the first same-seed replication around cap96.

## Next Gate

Promote pure high-cluster priority as the bit24 lead and test transfer: run the same high `actual_p1_a_57` cap64/cap96 pattern on another candidate whose learned neighborhood has a coherent actual-register cluster. If transfer fails, keep it as a bit24-specific operator.

## Compute Discipline

- 25 new F424 solver runs audited before solve and appended with `append_run.py`.
- Logs: `/tmp/F424/*.stderr.log` and `/tmp/F424/*.stdout.log`.
