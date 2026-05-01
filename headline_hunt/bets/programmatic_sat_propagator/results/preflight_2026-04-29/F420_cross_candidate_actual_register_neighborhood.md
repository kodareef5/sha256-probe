---
date: 2026-05-01
bet: programmatic_sat_propagator
status: CROSS_CANDIDATE_ACTUAL_REGISTER_LEARNED_NEIGHBORHOOD
parents: F419
---

# F420: cross-candidate actual-register learned-neighborhood scan

## Summary

Conflict cap: 50000. Same watch scope as F419: actual `a/e` registers for rounds 57-63 in both pairs plus `aux_modular_diff` targets. F420 runs the helper candidates bit24 and bit28, baseline and F343-injected.

| Candidate | Condition | Audit | Watch vars | Decisions | Backtracks | Learned exported | Learned touching watched | Touch % | Top touches |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| `bit24_mdc27e18c_fillffffffff` | baseline | CONFIRMED | 1021 | 396658 | 58805 | 46775 | 34898 | 74.608% | `actual_p1_a_57_b14=4350` `actual_p1_a_57_b4=4026` `actual_p1_a_57_b16=3902` `actual_p1_a_57_b18=3845` `actual_p1_a_57_b17=3841` `actual_p1_a_57_b6=3615` `actual_p1_a_57_b9=3395` `actual_p1_a_57_b21=3318` `actual_p1_a_57_b3=3171` `actual_p1_a_57_b12=3122` |
| `bit24_mdc27e18c_fillffffffff` | f343 | CONFIRMED | 1021 | 407049 | 58965 | 46696 | 35177 | 75.332% | `actual_p1_a_57_b22=5078` `actual_p1_a_57_b23=4442` `actual_p1_a_57_b24=4357` `actual_p1_a_57_b21=4103` `actual_p1_a_57_b25=3982` `actual_p1_a_57_b18=3576` `actual_p1_a_57_b14=3569` `actual_p1_a_57_b17=3563` `actual_p1_a_57_b9=3305` `actual_p1_a_57_b11=3304` |
| `bit28_md1acca79_fillffffffff` | baseline | CONFIRMED | 1019 | 367451 | 58046 | 46674 | 34736 | 74.423% | `actual_p1_a_57_b5=6505` `actual_p1_a_57_b6=5319` `actual_p1_a_57_b2=5076` `actual_p1_a_57_b0=4501` `actual_p1_a_57_b7=4477` `actual_p1_a_57_b10=4159` `actual_p1_a_57_b8=4013` `actual_p1_a_57_b3=3674` `actual_p1_e_58_b17=3584` `actual_p1_a_57_b4=3565` |
| `bit28_md1acca79_fillffffffff` | f343 | CONFIRMED | 1019 | 322416 | 57448 | 46843 | 34750 | 74.184% | `actual_p1_a_57_b5=5828` `actual_p1_a_57_b2=4995` `actual_p1_a_57_b0=4322` `actual_p1_a_57_b6=4235` `actual_p1_a_57_b22=3695` `actual_p1_a_57_b7=3501` `actual_p1_a_57_b11=3355` `actual_p1_a_57_b10=3258` `actual_p1_e_58_b4=3167` `actual_p1_a_57_b4=3114` |

## F343 Delta With Same Watcher

| Candidate | Δ decisions | Δ backtracks | Δ learned exported | Δ learned touching watched |
|---|---:|---:|---:|---:|
| `bit24_mdc27e18c_fillffffffff` | +10391 (+2.62%) | +160 (+0.27%) | -79 (-0.17%) | +279 (+0.80%) |
| `bit28_md1acca79_fillffffffff` | -45035 (-12.26%) | -598 (-1.03%) | +169 (+0.36%) | +14 (+0.04%) |

## Initial Read

F419 showed bit2 learned clauses concentrate heavily in actual-register variables, especially `actual_p1_a_57` bits 3/7/8. F420 asks whether the helper candidates share that learned neighborhood.

The answer is yes: bit24 and bit28 also put the learned-clause mass in actual-register variables, with `actual_p1_a_57` bits dominating the top ranks. This supports an operator shift away from `dW57` aux-row nudges and toward actual `a_57` learned-neighborhood variables.

## Verdict

The actual-register hotspot is cross-candidate, not a bit2 fluke. The next implementable test is an `actual_p1_a_57` priority/phase matrix using the top learned-neighborhood bits, measured against the same F343 baseline.

## Compute Discipline

- 4 CNFs audited before solver launch.
- 4 solver runs appended with `append_run.py`.
- Logs: `/tmp/F420/*.stderr.log` and `/tmp/F420/*.stdout.log`.
