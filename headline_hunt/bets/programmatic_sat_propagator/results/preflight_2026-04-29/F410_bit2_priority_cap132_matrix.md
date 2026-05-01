---
date: 2026-04-30
bet: programmatic_sat_propagator
status: DECISION_PRIORITY_MATRIX_RUN
---

# F410: decision-priority matrix

## Summary

Mode: `run`.
Verdict: `matrix_completed`.
Priority spec: `headline_hunt/bets/programmatic_sat_propagator/results/preflight_2026-04-29/F409_bit2_decision_priority_specs.json`.
Conflict cap: 50000.
Priority max suggestions: `132`.
Priority stride: `None`.
Runnable candidates here: 1.
Missing-input candidates here: 0.

## Compile Command

```bash
g++ -std=c++17 -O2 -I/home/yale/sha256_probe/.deps/cadical/src -I/home/yale/sha256_probe/.deps/nlohmann/include -I/opt/homebrew/include -I/usr/local/include /home/yale/sha256_probe/headline_hunt/bets/programmatic_sat_propagator/propagators/cascade_propagator.cc /home/yale/sha256_probe/.deps/cadical/build/libcadical.a -o /tmp/F399_cascade_propagator
```

## Runnable Candidates

| Candidate | VarMap | Arms |
|---|---|---:|
| `bit2_ma896ee41_fillffffffff` | `headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit2_ma896ee41_fillffffffff.cnf.varmap.json` | 4 |

## Missing Inputs

| Candidate | Missing CNF | Missing VarMap |
|---|:---:|:---:|

## Compile Result

Return code: `0`.
Wall seconds: `5.795`.

## Run Results

| Candidate | Arm | Result | Return Code | Wall s | Decisions | Backtracks | cb_decide | cb_propagate |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `bit2_ma896ee41_fillffffffff` | `baseline_no_propagator` | 0 | 2 | 1.537 | 0 | 0 | 0 | 0 |
| `bit2_ma896ee41_fillffffffff` | `existing_propagator` | 0 | 2 | 3.814 | 353889 | 58131 | 0 | 687 |
| `bit2_ma896ee41_fillffffffff` | `priority_f286_132_max132` | 0 | 2 | 4.196 | 396334 | 58673 | 132 | 809 |
| `bit2_ma896ee41_fillffffffff` | `priority_f332_139_max132` |  | 1 | 0.003 |  |  |  |  |
