---
date: 2026-04-30
bet: programmatic_sat_propagator
status: DECISION_PRIORITY_MATRIX_RUN
---

# F405: decision-priority matrix

## Summary

Mode: `run`.
Verdict: `matrix_completed`.
Priority spec: `headline_hunt/bets/programmatic_sat_propagator/results/preflight_2026-04-29/F397_decision_priority_specs.json`.
Conflict cap: 50000.
Priority max suggestions: `132`.
Priority stride: `None`.
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
Wall seconds: `5.995`.

## Run Results

| Candidate | Arm | Result | Return Code | Wall s | Decisions | Backtracks | cb_decide | cb_propagate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `bit10_m3304caa0_fill80000000` | `baseline_no_propagator` | 0 | 2 | 1.486 | 0 | 0 | 0 | 0 |
| `bit10_m3304caa0_fill80000000` | `existing_propagator` | 0 | 2 | 4.06 | 370215 | 58905 | 0 | 1419 |
| `bit10_m3304caa0_fill80000000` | `priority_f286_132_max132` | 0 | 2 | 3.215 | 330241 | 57212 | 132 | 551 |
| `bit10_m3304caa0_fill80000000` | `priority_f332_139_max132` | 0 | 2 | 4.115 | 317349 | 57214 | 132 | 512 |
| `bit11_m45b0a5f6_fill00000000` | `baseline_no_propagator` | 0 | 2 | 1.624 | 0 | 0 | 0 | 0 |
| `bit11_m45b0a5f6_fill00000000` | `existing_propagator` | 0 | 2 | 3.873 | 357631 | 58258 | 0 | 1105 |
| `bit11_m45b0a5f6_fill00000000` | `priority_f286_132_max132` | 0 | 2 | 4.242 | 450314 | 59693 | 132 | 1981 |
| `bit11_m45b0a5f6_fill00000000` | `priority_f332_139_max132` | 0 | 2 | 4.043 | 389922 | 58692 | 132 | 1046 |
| `bit13_m4d9f691c_fill55555555` | `baseline_no_propagator` | 0 | 2 | 1.414 | 0 | 0 | 0 | 0 |
| `bit13_m4d9f691c_fill55555555` | `existing_propagator` | 0 | 2 | 3.588 | 325788 | 57875 | 0 | 1282 |
| `bit13_m4d9f691c_fill55555555` | `priority_f286_132_max132` | 0 | 2 | 3.837 | 401007 | 58283 | 132 | 552 |
| `bit13_m4d9f691c_fill55555555` | `priority_f332_139_max132` | 0 | 2 | 3.865 | 390451 | 58626 | 132 | 512 |
| `bit0_m8299b36f_fill80000000` | `baseline_no_propagator` | 0 | 2 | 1.382 | 0 | 0 | 0 | 0 |
| `bit0_m8299b36f_fill80000000` | `existing_propagator` | 0 | 2 | 3.711 | 402063 | 59122 | 0 | 993 |
| `bit0_m8299b36f_fill80000000` | `priority_f286_132_max132` | 0 | 2 | 3.928 | 387107 | 58192 | 132 | 913 |
| `bit0_m8299b36f_fill80000000` | `priority_f332_139_max132` | 0 | 2 | 3.896 | 383044 | 58296 | 132 | 1814 |
| `bit17_m427c281d_fill80000000` | `baseline_no_propagator` | 0 | 2 | 1.438 | 0 | 0 | 0 | 0 |
| `bit17_m427c281d_fill80000000` | `existing_propagator` | 0 | 2 | 3.748 | 375263 | 57873 | 0 | 1140 |
| `bit17_m427c281d_fill80000000` | `priority_f286_132_max132` | 0 | 2 | 4.183 | 432741 | 59220 | 132 | 1180 |
| `bit17_m427c281d_fill80000000` | `priority_f332_139_max132` | 0 | 2 | 3.746 | 383660 | 57874 | 132 | 808 |
| `bit18_m347b0144_fill00000000` | `baseline_no_propagator` | 0 | 2 | 1.45 | 0 | 0 | 0 | 0 |
| `bit18_m347b0144_fill00000000` | `existing_propagator` | 0 | 2 | 3.958 | 368475 | 57917 | 0 | 1140 |
| `bit18_m347b0144_fill00000000` | `priority_f286_132_max132` | 0 | 2 | 4.09 | 391132 | 58529 | 132 | 1452 |
| `bit18_m347b0144_fill00000000` | `priority_f332_139_max132` | 0 | 2 | 4.126 | 363767 | 57841 | 132 | 636 |
