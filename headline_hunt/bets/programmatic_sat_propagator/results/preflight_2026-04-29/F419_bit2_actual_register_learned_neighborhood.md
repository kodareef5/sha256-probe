---
date: 2026-04-30
bet: programmatic_sat_propagator
status: BIT2_ACTUAL_REGISTER_LEARNED_NEIGHBORHOOD
parents: F418
---

# F419: bit2 actual-register learned-neighborhood scan

## Summary

Conflict cap: 50000. Watches actual `a/e` registers for rounds 57-63 in both pairs plus `aux_modular_diff` targets. Watch vars: 1021.

| Condition | Audit | Decisions | Backtracks | Learned exported | Learned touching watched | Touch % | Top touches |
|---|---|---:|---:|---:|---:|---:|---|
| baseline | CONFIRMED | 353889 | 58131 | 47054 | 36896 | 78.412% | `actual_p1_a_57_b3=5540` `actual_p1_a_57_b8=5050` `actual_p1_a_57_b7=4940` `actual_p1_a_57_b4=4683` `actual_p1_a_57_b10=4670` `actual_p1_a_57_b2=4385` `actual_p1_a_57_b6=4185` `actual_p2_e_58_b12=4140` `actual_p1_a_57_b0=3828` `actual_p1_e_58_b12=3785` |
| f343 | CONFIRMED | 350989 | 57869 | 46769 | 35922 | 76.807% | `actual_p1_a_57_b8=5552` `actual_p1_a_57_b3=5299` `actual_p1_a_57_b7=5268` `actual_p1_a_57_b16=4887` `actual_p1_a_57_b0=4593` `actual_p1_a_57_b17=4425` `actual_p1_a_57_b13=4219` `actual_p1_a_57_b11=4066` `actual_p1_a_57_b12=4002` `actual_p1_a_57_b2=3958` |

## F343 Delta With Same Watcher

| Δ decisions | Δ backtracks | Δ learned exported | Δ learned touching watched |
|---:|---:|---:|---:|
| -2900 (-0.82%) | -262 (-0.45%) | -285 (-0.61%) | -974 (-2.64%) |

## Initial Read

F418 found no learned clauses touching `dW57` or `dW58` aux rows. F419 moves the watch surface to actual-register variables and Rule-4 modular-diff aux targets for bit2 only.

This immediately finds the learned neighborhood. Roughly 77-78% of exported learned clauses touch at least one watched actual/modular variable. The dominant variables are not modular-diff targets and not `dW57`; they are actual-register bits, especially `actual_p1_a_57` low/mid bits. The most stable top hits across baseline and F343 are `a_57` bits 3, 7, and 8.

F343 injection is mildly helpful under this watch surface on bit2 (-0.82% decisions), but it also reduces learned clauses touching the watched actual neighborhood by 2.64%. Treat that as descriptive, not an optimization result; the important outcome is that the next operator target is now concrete.

## Verdict

The learned-clause action for bit2 is in actual `a_57`, not the `dW57`/`dW58` aux rows. The next useful test is an `a_57` learned-neighborhood priority/phase scan or a cross-candidate F419 replication to see whether helpers share the same `a_57` hotspot.

## Compute Discipline

- 2 CNFs audited before solver launch.
- 2 solver runs appended with `append_run.py`.
- Logs: `/tmp/F419/*.stderr.log` and `/tmp/F419/*.stdout.log`.
