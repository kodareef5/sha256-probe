---
date: 2026-04-30
bet: programmatic_sat_propagator
status: BOTH_PATHS_HARDCORE_LOWBIT_COMPARISON
parents: F402, F411
---

# F412: both-paths hard-core low-bit comparison

## Question

Does bit2 stand out because the two F332 low-bit keys missing from F409 are absent from its hard core?

## Result

| Candidate | F343 effect | F286 missing | F332 missing | w2[57].b1 | w2[58].b1 | Schedule core |
|---|---:|---:|---:|---|---|---:|
| `bit2_ma896ee41_fillffffffff` | +0.07% | 0 | 2 | shell | shell | 182 |
| `bit4_md41b678d_fillffffffff` | -9.40% | 2 | 5 | shell | core | 175 |
| `bit24_mdc27e18c_fillffffffff` | -7.13% | 0 | 3 | core | core | 181 |
| `bit28_md1acca79_fillffffffff` | -6.37% | 0 | 1 | core | core | 184 |

## Missing F332 Keys

- `bit2_ma896ee41_fillffffffff`: `w2[57].b1`, `w2[58].b1`
- `bit4_md41b678d_fillffffffff`: `w2[58].b14`, `w2[58].b26`, `w2[57].b1`, `w2[58].b27`, `w2[58].b4`
- `bit24_mdc27e18c_fillffffffff`: `w2[58].b4`, `w2[58].b8`, `w2[58].b9`
- `bit28_md1acca79_fillffffffff`: `w2[58].b16`

## Verdict

Bit2 is the only candidate in this n=4 both-paths panel where both `w2[57].b1` and `w2[58].b1` fall outside the schedule core.

That is a clue, not a full explanation. Bit4 also loses `w2[57].b1`, has worse F332 completeness overall, and still gets a strong F343 speedup. Bit24 and bit28 keep both low-bit keys and help. So the low-bit F332 gap should guide bit2-specific trace mining, but it is not sufficient as a predictor.

## Next

Use the shell-shell bit2 signature to seed a targeted trace comparison: watch when `w2[57].b1`, `w2[58].b1`, and the F343 literals enter the assignment trail on bit2 vs bit24/bit28.
