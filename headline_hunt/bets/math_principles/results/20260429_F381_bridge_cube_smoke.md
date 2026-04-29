---
date: 2026-04-29
bet: math_principles
status: BRIDGE_CUBE_SMOKE
---

# F381: bridge cube smoke tests

## Summary

Verdict: `bridge_cube_smoke_found_unsat_cube`.
Promote UNSAT bridge cubes to proof/log extraction.
CNF: `headline_hunt/bets/cascade_aux_encoding/cnfs/aux_force_sr60_n32_bit31_m17149975_fillffffffff.cnf`.
Conflict cap: 5000; timeout: 5s.

| Cube | Assumptions | Status | rc | Wall |
|---|---:|---|---:|---:|
| `F378_D61_floor_guard_explosion::ones_w57_w63` | 116 | `UNKNOWN` | 0 | 0.285672 |
| `F378_D61_floor_guard_explosion::w61` | 32 | `UNSATISFIABLE` | 20 | 0.173421 |
| `F378_D61_floor_guard_explosion::w57_w60` | 128 | `UNSATISFIABLE` | 20 | 0.099024 |
| `F375_D61_to_guard_bridge::ones_w57_w63` | 120 | `UNKNOWN` | 0 | 0.207775 |
| `F375_D61_to_guard_bridge::w61` | 32 | `UNSATISFIABLE` | 20 | 0.095508 |
| `F375_D61_to_guard_bridge::w57_w60` | 128 | `UNSATISFIABLE` | 20 | 0.037276 |
| `F374_low_guard_corner::ones_w57_w63` | 105 | `UNKNOWN` | 0 | 0.228829 |
| `F374_low_guard_corner::w61` | 32 | `UNSATISFIABLE` | 20 | 0.040458 |
| `F374_low_guard_corner::w57_w60` | 128 | `UNSATISFIABLE` | 20 | 0.013225 |
