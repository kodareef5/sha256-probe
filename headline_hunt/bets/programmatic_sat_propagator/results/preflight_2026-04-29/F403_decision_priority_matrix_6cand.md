---
date: 2026-04-30
bet: programmatic_sat_propagator
status: DECISION_PRIORITY_MATRIX_RUN
---

# F403: decision-priority matrix

## Summary

Mode: `run`.
Verdict: `matrix_completed`.
Priority spec: `headline_hunt/bets/programmatic_sat_propagator/results/preflight_2026-04-29/F397_decision_priority_specs.json`.
Conflict cap: 50000.
Runnable candidates here: 6.
Missing-input candidates here: 0.

## Compile Command

```bash
g++ -std=c++17 -O2 -I/home/yale/sha256_probe/.deps/cadical/src -I/home/yale/sha256_probe/.deps/nlohmann/include -I/opt/homebrew/include -I/usr/local/include /home/yale/sha256_probe/headline_hunt/bets/programmatic_sat_propagator/propagators/cascade_propagator.cc /home/yale/sha256_probe/.deps/cadical/build/libcadical.a -o /tmp/F399_cascade_propagator
```

## Runnable Candidates

| Candidate | VarMap | Arms |
|---|---|---:|
| `bit10_m3304caa0_fill80000000` | `headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit10_m3304caa0_fill80000000.cnf.varmap.json` | 4 |
| `bit11_m45b0a5f6_fill00000000` | `headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit11_m45b0a5f6_fill00000000.cnf.varmap.json` | 4 |
| `bit13_m4d9f691c_fill55555555` | `headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit13_m4d9f691c_fill55555555.cnf.varmap.json` | 4 |
| `bit0_m8299b36f_fill80000000` | `headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit0_m8299b36f_fill80000000.cnf.varmap.json` | 4 |
| `bit17_m427c281d_fill80000000` | `headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit17_m427c281d_fill80000000.cnf.varmap.json` | 4 |
| `bit18_m347b0144_fill00000000` | `headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit18_m347b0144_fill00000000.cnf.varmap.json` | 4 |

## Missing Inputs

| Candidate | Missing CNF | Missing VarMap |
|---|:---:|:---:|

## Compile Result

Return code: `0`.
Wall seconds: `5.604`.

## Run Results

| Candidate | Arm | Result | Return Code | Wall s | Decisions | Backtracks | cb_decide | cb_propagate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `bit10_m3304caa0_fill80000000` | `baseline_no_propagator` | 0 | 2 | 1.293 | 0 | 0 | 0 | 0 |
| `bit10_m3304caa0_fill80000000` | `existing_propagator` | 0 | 2 | 3.729 | 370215 | 58905 | 0 | 1419 |
| `bit10_m3304caa0_fill80000000` | `priority_f286_132` | 0 | 2 | 4.132 | 431302 | 55643 | 328868 | 745 |
| `bit10_m3304caa0_fill80000000` | `priority_f332_139` | 0 | 2 | 5.71 | 736413 | 57811 | 513697 | 512 |
| `bit11_m45b0a5f6_fill00000000` | `baseline_no_propagator` | 0 | 2 | 1.476 | 0 | 0 | 0 | 0 |
| `bit11_m45b0a5f6_fill00000000` | `existing_propagator` | 0 | 2 | 3.435 | 357631 | 58258 | 0 | 1105 |
| `bit11_m45b0a5f6_fill00000000` | `priority_f286_132` | 0 | 2 | 4.702 | 660567 | 56908 | 519645 | 1552 |
| `bit11_m45b0a5f6_fill00000000` | `priority_f332_139` | 0 | 2 | 4.125 | 529885 | 56293 | 409267 | 820 |
| `bit13_m4d9f691c_fill55555555` | `baseline_no_propagator` | 0 | 2 | 1.377 | 0 | 0 | 0 | 0 |
| `bit13_m4d9f691c_fill55555555` | `existing_propagator` | 0 | 2 | 3.771 | 325788 | 57875 | 0 | 1282 |
| `bit13_m4d9f691c_fill55555555` | `priority_f286_132` | 0 | 2 | 6.052 | 817067 | 58487 | 546616 | 848 |
| `bit13_m4d9f691c_fill55555555` | `priority_f332_139` | 0 | 2 | 5.917 | 788050 | 58193 | 534793 | 678 |
| `bit0_m8299b36f_fill80000000` | `baseline_no_propagator` | 0 | 2 | 1.541 | 0 | 0 | 0 | 0 |
| `bit0_m8299b36f_fill80000000` | `existing_propagator` | 0 | 2 | 3.873 | 402063 | 59122 | 0 | 993 |
| `bit0_m8299b36f_fill80000000` | `priority_f286_132` | 0 | 2 | 4.715 | 665415 | 57283 | 470221 | 1563 |
| `bit0_m8299b36f_fill80000000` | `priority_f332_139` | 0 | 2 | 4.518 | 663624 | 56944 | 529707 | 1211 |
| `bit17_m427c281d_fill80000000` | `baseline_no_propagator` | 0 | 2 | 1.438 | 0 | 0 | 0 | 0 |
| `bit17_m427c281d_fill80000000` | `existing_propagator` | 0 | 2 | 3.771 | 375263 | 57873 | 0 | 1140 |
| `bit17_m427c281d_fill80000000` | `priority_f286_132` | 0 | 2 | 4.49 | 594050 | 56509 | 440058 | 597 |
| `bit17_m427c281d_fill80000000` | `priority_f332_139` | 0 | 2 | 6.48 | 847596 | 58346 | 638962 | 777 |
| `bit18_m347b0144_fill00000000` | `baseline_no_propagator` | 0 | 2 | 1.535 | 0 | 0 | 0 | 0 |
| `bit18_m347b0144_fill00000000` | `existing_propagator` | 0 | 2 | 4.0 | 368475 | 57917 | 0 | 1140 |
| `bit18_m347b0144_fill00000000` | `priority_f286_132` | 0 | 2 | 4.282 | 477303 | 55678 | 347599 | 662 |
| `bit18_m347b0144_fill00000000` | `priority_f332_139` | 0 | 2 | 4.604 | 588049 | 56216 | 449365 | 703 |
