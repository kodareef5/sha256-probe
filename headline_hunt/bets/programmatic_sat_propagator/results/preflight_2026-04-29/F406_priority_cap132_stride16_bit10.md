---
date: 2026-04-30
bet: programmatic_sat_propagator
status: DECISION_PRIORITY_MATRIX_RUN
---

# F406: decision-priority matrix

## Summary

Mode: `run`.
Verdict: `matrix_completed`.
Priority spec: `headline_hunt/bets/programmatic_sat_propagator/results/preflight_2026-04-29/F397_decision_priority_specs.json`.
Conflict cap: 50000.
Priority max suggestions: `132`.
Priority stride: `16`.
Runnable candidates here: 1.
Missing-input candidates here: 0.

## Compile Command

```bash
g++ -std=c++17 -O2 -I/home/yale/sha256_probe/.deps/cadical/src -I/home/yale/sha256_probe/.deps/nlohmann/include -I/opt/homebrew/include -I/usr/local/include /home/yale/sha256_probe/headline_hunt/bets/programmatic_sat_propagator/propagators/cascade_propagator.cc /home/yale/sha256_probe/.deps/cadical/build/libcadical.a -o /tmp/F399_cascade_propagator
```

## Runnable Candidates

| Candidate | VarMap | Arms |
|---|---|---:|
| `bit10_m3304caa0_fill80000000` | `headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit10_m3304caa0_fill80000000.cnf.varmap.json` | 4 |

## Missing Inputs

| Candidate | Missing CNF | Missing VarMap |
|---|:---:|:---:|

## Compile Result

Return code: `0`.
Wall seconds: `5.88`.

## Run Results

| Candidate | Arm | Result | Return Code | Wall s | Decisions | Backtracks | cb_decide | cb_propagate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `bit10_m3304caa0_fill80000000` | `baseline_no_propagator` | 0 | 2 | 1.485 | 0 | 0 | 0 | 0 |
| `bit10_m3304caa0_fill80000000` | `existing_propagator` | 0 | 2 | 4.09 | 370215 | 58905 | 0 | 1419 |
| `bit10_m3304caa0_fill80000000` | `priority_f286_132_max132_stride16` | 0 | 2 | 4.162 | 436887 | 58107 | 132 | 1814 |
| `bit10_m3304caa0_fill80000000` | `priority_f332_139_max132_stride16` | 0 | 2 | 4.067 | 439118 | 58496 | 132 | 673 |
