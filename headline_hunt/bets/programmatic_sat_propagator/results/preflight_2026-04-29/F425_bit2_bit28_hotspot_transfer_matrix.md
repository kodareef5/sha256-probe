---
date: 2026-05-01
bet: programmatic_sat_propagator
status: ACTUAL_A57_HOTSPOT_TRANSFER_MATRIX
parents: F421, F424
---

# F425: bit2/bit28 low-cap hotspot transfer

## Setup

Conflict cap: 50000. Seeds: [3, 4, 5, 6, 7].

F421 showed cap132 actual-register hotspot priority was harmful on bit2 and bit28, while F424 showed bit24 pure high-cluster priority is robust. F425 tests whether smaller caps 64/96 rescue the prior negative candidates. F343 is included as the same-seed comparison arm.

Priority spec: `headline_hunt/bets/programmatic_sat_propagator/results/preflight_2026-04-29/F425_bit2_bit28_hotspot_transfer_specs.json`.

## Mean Results

### `bit2_ma896ee41_fillffffffff`

| Arm | Mean decisions | Delta decisions | Mean backtracks | Delta backtracks | Mean cb_decide suggestions | Mean cb_propagate fires |
|---|---:|---:|---:|---:|---:|---:|
| `baseline` | 352802 | +0.00% | 58016 | +0.00% | 0 | 687 |
| `f343` | 340890 | -3.38% | 57695 | -0.55% | 0 | 687 |
| `hotspot_cap64` | 476548 | +35.07% | 59924 | +3.29% | 64 | 2742 |
| `hotspot_cap96` | 405109 | +14.83% | 58823 | +1.39% | 96 | 2154 |

Per-seed decisions:

| Seed | baseline | f343 | hotspot cap64 | hotspot cap96 |
|---:|---:|---:|---:|---:|
| 3 | 358533 | 339439 | 472910 | 413922 |
| 4 | 355730 | 347462 | 515993 | 411861 |
| 5 | 338609 | 335959 | 479023 | 430152 |
| 6 | 355823 | 343725 | 469792 | 401687 |
| 7 | 355317 | 337863 | 445021 | 367922 |

### `bit28_md1acca79_fillffffffff`

| Arm | Mean decisions | Delta decisions | Mean backtracks | Delta backtracks | Mean cb_decide suggestions | Mean cb_propagate fires |
|---|---:|---:|---:|---:|---:|---:|
| `baseline` | 372963 | +0.00% | 58002 | +0.00% | 0 | 1160 |
| `f343` | 309372 | -17.05% | 57225 | -1.34% | 0 | 1176 |
| `hotspot_cap64` | 460429 | +23.45% | 59128 | +1.94% | 64 | 1881 |
| `hotspot_cap96` | 406470 | +8.98% | 58839 | +1.44% | 96 | 1826 |

Per-seed decisions:

| Seed | baseline | f343 | hotspot cap64 | hotspot cap96 |
|---:|---:|---:|---:|---:|
| 3 | 371767 | 321453 | 413577 | 425768 |
| 4 | 373728 | 317151 | 465228 | 388159 |
| 5 | 374090 | 315499 | 454846 | 415853 |
| 6 | 373273 | 320008 | 446434 | 386521 |
| 7 | 371956 | 272748 | 522060 | 416048 |

## Read

bit28_md1acca79_fillffffffff: best non-baseline arm is f343 at 309372 decisions (-17.05%). bit2_ma896ee41_fillffffffff: best non-baseline arm is f343 at 340890 decisions (-3.38%). Smaller caps do not rescue actual-register hotspot priority on the prior negative candidates.

This closes the broad transfer attempt. Bit24's win should not be described as an `actual_p1_a_57` hotspot rule in general; it is a bit24/high-contiguous-cluster result unless another candidate shows the same geometry. On bit2 and bit28, direct hotspot priority increases both decisions and backtracks, and it drives much higher `cb_propagate` activity than baseline/F343. That is oversteer, not a weaker version of the bit24 effect.

## Next Gate

Stop trying direct hotspot priority on sparse low-bit clusters. Keep F343 as the default for bit2/bit28, and only revisit priority transfer when a candidate has a contiguous high actual-register cluster similar to bit24 bits `21-25`.

## Compute Discipline

- 40 new F425 solver runs audited before solve and appended with `append_run.py`.
- Logs: `/tmp/F425/*.stderr.log` and `/tmp/F425/*.stdout.log`.
