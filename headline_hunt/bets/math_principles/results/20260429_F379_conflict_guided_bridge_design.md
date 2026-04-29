---
date: 2026-04-29
bet: math_principles
status: CONFLICT_GUIDED_BRIDGE_DESIGN
---

# F379: conflict-guided bridge design

## Summary

Verdict: `conflict_guided_bridge_design_ready`.
Use F378 as a diagnostic target for sound CDCL/propagator experiments; do not inject empirical hard-core clauses as facts.

The strict-kernel basin work gives a diagnostic target, not another reason to keep mutating dM.
The design rule is soundness first: arithmetic consequences may be propagated as clauses, while empirical hard-core observations become decision priorities or assumption cubes until proven.

## Diagnostic Targets

| Target | Source | Score | a57 | D61 | Chart | Use |
|---|---|---:|---:|---:|---|---|
| `scalar_floor` | `F372/F377` | 37.8 | 6 | 8 | `dh,dCh` | baseline strict score floor to beat |
| `guard_corner` | `F374/F377` | 40.8 | 4 | 11 | `dT2,dCh` | a57=4 branch; chart repair target |
| `D61_floor_guard_explosion` | `F378` | 86.1 | 19 | 4 | `dCh,dh` | diagnostic cube: D61 reaches chamber floor while guard explodes |
| `D61_to_guard_bridge` | `F375/F377` | 39.1 | 5 | 13 | `dCh,dh` | confirmed bridge direction; loses D61 while repairing guard |

## Soundness Split

| Class | Allowed API hooks | Rule |
|---|---|---|
| `sound_arithmetic` | `cb_propagate, cb_add_reason_clause_lit, cb_check_found_model` | Only proven cascade arithmetic, schedule recurrence, and modular-add consequences may be injected as clauses. |
| `empirical_core_prior` | `cb_decide` | F286/F324-F326 hard-core bits are decision priorities, not clauses, unless separately derived for the current CNF. |
| `diagnostic_assumption_cube` | `solver assumptions, conflict/decision logging` | F378 and F375 split points become cubes for measuring conflict paths and extracting learned-clause candidates. |
| `forbidden_unsound_clause` | `` | Do not add clauses merely saying the chamber target must hold; that would solve a different problem. |

## Experiments

| Step | Goal | Output | Stop condition |
|---|---|---|---|
| `E1_bridge_cubes` | Turn F378 D61=4/a57=19 and F375 a57=5/D61=13 into assumption cubes against the F322/F372 CNFs. | conflict counts, first-conflict levels, and learned clauses touching W57-W60/core bits | no distinct conflict signature versus baseline after 20 cubes |
| `E2_cb_decide_core_priority` | Use 132 hard-core bits plus F378 split bits as cb_decide priorities without adding clauses. | conflict/decision/restart deltas against vanilla CaDiCaL on the same CNFs | <1.5x conflict reduction at 100k and 1M caps |
| `E3_sound_rule4_bridge` | Implement only sound Rule 4/5 modular consequences at the D61/a57 bridge boundary. | propagations fired, reason-clause sizes, conflict reduction, and zero model-rejection false positives | reason clauses exceed useful size or conflicts do not drop by >=2x on bridge cubes |

## Implementation Notes

- Use `add_observed_var` narrowly: W57-W60, the 132 hard-core schedule bits, and register bits needed for D61/a57 bridge rules.
- F378's D61=4/a57=19 point is the first diagnostic where the chamber D61 floor is reached under strict kernel; it should be the first cube.
- The bridge experiments should log learned clauses and variable decision ranks, because the thesis is about CDCL trajectory, not UP.
- A successful propagator must beat common-mode search by reducing conflicts or producing a bridge clause; another local-search run is not enough evidence.
