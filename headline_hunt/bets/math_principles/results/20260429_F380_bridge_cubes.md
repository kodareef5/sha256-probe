---
date: 2026-04-29
bet: math_principles
status: BRIDGE_CUBE_GENERATOR
---

# F380: bridge cube generator

## Summary

Verdict: `bridge_cubes_generated`.
Run E1 with the generated DIMACS assumption sidecar and compare conflict signatures.
Varmap: `headline_hunt/bets/math_principles/data/20260429_F380_aux_force_sr60_n32_bit31_m17149975_fillffffffff.varmap.json`.

| Target | Subset | Bits | Ones | Assumptions | Const conflicts | Candidate |
|---|---|---:|---:|---:|---:|---|
| `F378_D61_floor_guard_explosion` | `ones_w57_w63` | 116 | 116 | 116 | 0 | a57=19 D61=4 chart=`dCh,dh` |
| `F378_D61_floor_guard_explosion` | `w61` | 32 | 17 | 32 | 0 | a57=19 D61=4 chart=`dCh,dh` |
| `F378_D61_floor_guard_explosion` | `w57_w60` | 128 | 63 | 128 | 0 | a57=19 D61=4 chart=`dCh,dh` |
| `F375_D61_to_guard_bridge` | `ones_w57_w63` | 120 | 120 | 120 | 0 | a57=5 D61=13 chart=`dCh,dh` |
| `F375_D61_to_guard_bridge` | `w61` | 32 | 18 | 32 | 0 | a57=5 D61=13 chart=`dCh,dh` |
| `F375_D61_to_guard_bridge` | `w57_w60` | 128 | 70 | 128 | 0 | a57=5 D61=13 chart=`dCh,dh` |
| `F374_low_guard_corner` | `ones_w57_w63` | 105 | 105 | 105 | 0 | a57=4 D61=11 chart=`dT2,dCh` |
| `F374_low_guard_corner` | `w61` | 32 | 16 | 32 | 0 | a57=4 D61=11 chart=`dT2,dCh` |
| `F374_low_guard_corner` | `w57_w60` | 128 | 62 | 128 | 0 | a57=4 D61=11 chart=`dT2,dCh` |

## Usage

Use coordinate cubes directly for propagator diagnostics. If a matching varmap is supplied, the `.dimacs.txt` sidecar gives assumption literals for CaDiCaL-style runs. Do not use cubes from a mismatched kernel-bit CNF as proof artifacts; they are diagnostics.
