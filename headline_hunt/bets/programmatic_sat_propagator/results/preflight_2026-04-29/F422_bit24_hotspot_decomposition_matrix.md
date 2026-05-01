---
date: 2026-05-01
bet: programmatic_sat_propagator
status: BIT24_A57_HOTSPOT_DECOMPOSITION_MATRIX
parents: F421
---

# F422: bit24 actual `a_57` hotspot decomposition

## Setup

Conflict cap: 50000. Seeds: [0, 1, 2]. Candidate: `bit24_mdc27e18c_fillffffffff`.

F421 showed the full bit24 `actual_p1_a_57` hotspot priority arm was strongly positive. F422 splits that arm into low/mid bits `14,16` and high cluster bits `21-25`, then checks whether the high cluster keeps the win at a smaller cap.

Priority spec: `headline_hunt/bets/programmatic_sat_propagator/results/preflight_2026-04-29/F422_bit24_hotspot_decomposition_specs.json`.

## Mean Results

| Arm | Mean decisions | Δ decisions | Mean backtracks | Δ backtracks | Mean cb_decide suggestions | Mean cb_propagate fires |
|---|---:|---:|---:|---:|---:|---:|
| `baseline` | 406585 | +0.00% | 58939 | +0.00% | 0 | 791 |
| `f343` | 404511 | -0.51% | 58857 | -0.14% | 0 | 743 |
| `lowmid_14_16_cap132` | 385102 | -5.28% | 58367 | -0.97% | 132 | 530 |
| `high_21_25_cap132` | 373461 | -8.15% | 58497 | -0.75% | 132 | 1675 |
| `high_21_25_cap64` | 360376 | -11.37% | 57990 | -1.61% | 64 | 1298 |

## Per-Seed Decisions

| Seed | baseline | f343 | lowmid 14/16 cap132 | high 21-25 cap132 | high 21-25 cap64 |
|---:|---:|---:|---:|---:|---:|
| 0 | 396658 | 407049 | 390033 | 370822 | 362338 |
| 1 | 413480 | 409851 | 383992 | 372958 | 363171 |
| 2 | 409618 | 396633 | 381280 | 376602 | 355619 |

## Initial Read

This matrix separates the two plausible sources of the F421 bit24 win: the lower/mid hits `14,16` and the high contiguous cluster `21-25` that became dominant under F343 in F420.

The win concentrates in the high cluster. Low/mid `14,16` is helpful at -5.28% mean decisions, but high `21-25` improves to -8.15% at cap132 and -11.37% at cap64. The cap64 arm also wins on every seed, lowers mean backtracks by 1.61%, and uses fewer decision suggestions than cap132. That makes high `a_57[21:25]` the current bit24 deployment lead, not the full F421 hotspot set.

## Verdict

Promote bit24 high `actual_p1_a_57` bits `21-25` with a smaller bounded priority cap. Next test should compare cap32/cap64/cap96 on the high cluster and then try high-cluster priority plus F343 to see whether the direct clause nudge and the actual-register opening book compose or interfere.

## Compute Discipline

- 15 solver runs audited before solve and appended with `append_run.py`.
- All CNF audits were recorded per run.
- Logs: `/tmp/F422/*.stderr.log` and `/tmp/F422/*.stdout.log`.
