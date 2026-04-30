---
date: 2026-04-30
bet: programmatic_sat_propagator
status: DECISION_PRIORITY_MATRIX_PLAN
---

# F399: decision-priority matrix plan

## Summary

Mode: `dry_run`.
Priority spec: `headline_hunt/bets/programmatic_sat_propagator/results/preflight_2026-04-29/F397_decision_priority_specs.json`.
Conflict cap: 50000.
Runnable candidates here: 1.
Missing-input candidates here: 5.

## Compile Command

```bash
g++ -std=c++17 -O2 -I/opt/homebrew/include -I/usr/local/include -L/opt/homebrew/lib -L/usr/local/lib /home/yale/sha256_probe/headline_hunt/bets/programmatic_sat_propagator/propagators/cascade_propagator.cc -lcadical -o /tmp/F399_cascade_propagator
```

## Runnable Candidates

| Candidate | VarMap | Arms |
|---|---|---:|
| `bit10_m3304caa0_fill80000000` | `headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit10_m3304caa0_fill80000000.cnf.varmap.json` | 4 |

## Missing Inputs

| Candidate | Missing CNF | Missing VarMap |
|---|:---:|:---:|
| `bit11_m45b0a5f6_fill00000000` | True | True |
| `bit13_m4d9f691c_fill55555555` | True | True |
| `bit0_m8299b36f_fill80000000` | True | True |
| `bit17_m427c281d_fill80000000` | True | True |
| `bit18_m347b0144_fill00000000` | False | True |
