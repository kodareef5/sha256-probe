---
date: 2026-05-01
bet: programmatic_sat_propagator
status: ACTUAL_REGISTER_LEARNED_NEIGHBORHOOD_CROSS_CANDIDATE
parents: F416, F417, F418, F419
evidence_level: EVIDENCE
---

# F420: actual-register learned-neighborhood generalizes across the F416-F419 panel

## Steering Decision

After reading F416-F419, the old Path B plan to keep mining F343/dW-row learned
clauses is mostly superseded: F417 found zero learned clauses touching the F343
triple, and F418 found zero touching the full `dW57`/`dW58` aux rows.

I did not treat Path B as dead. F419 found fresh CDCL learning in actual
registers for bit2, especially `actual_p1_a_57`. The non-duplicative Path B
continuation is therefore a cross-candidate F419 replication: same
`cadical-ipasir-up` learner callback, same 50k conflict cap, same actual-register
watch surface, but across bit2/bit24/bit28 baseline and F343-injected arms.

## Method

Watch surface: actual `a/e` registers for rounds 57-63 in both pairs, plus
`aux_modular_diff` targets. This matches F419's intended scope.

Candidate panel:

- `bit2_ma896ee41_fillffffffff`
- `bit24_mdc27e18c_fillffffffff`
- `bit28_md1acca79_fillffffffff`

All final-panel CNFs audited `CONFIRMED` before launch. The local checkout lacked
the bit24 aux-force varmap sidecar, so the runner regenerated the bit24
aux-force CNF/varmap into `/tmp/F420_full` from the committed encoder and audited
that regenerated CNF before solving.

## Summary

| Candidate | Condition | Decisions | Backtracks | Learned exported | Learned touching watched | Touch % | Top learned-touch variables |
|---|---|---:|---:|---:|---:|---:|---|
| `bit2_ma896ee41_fillffffffff` | baseline | 353889 | 58131 | 47054 | 36896 | 78.41% | `a57_b3`, `a57_b8`, `a57_b7`, `a57_b4`, `a57_b10` |
| `bit2_ma896ee41_fillffffffff` | F343 | 350989 | 57869 | 46769 | 35922 | 76.81% | `a57_b8`, `a57_b3`, `a57_b7`, `a57_b16`, `e57_b0` |
| `bit24_mdc27e18c_fillffffffff` | baseline | 396658 | 58805 | 46775 | 34898 | 74.61% | `a57_b14`, `a57_b4`, `a57_b16`, `a57_b18`, `a57_b17` |
| `bit24_mdc27e18c_fillffffffff` | F343 | 407049 | 58965 | 46696 | 35177 | 75.33% | `a57_b22`, `a57_b23`, `a57_b24`, `a57_b21`, `a57_b25` |
| `bit28_md1acca79_fillffffffff` | baseline | 367451 | 58046 | 46674 | 34736 | 74.42% | `a57_b5`, `a57_b6`, `a57_b2`, `e57_b0`, `a57_b7` |
| `bit28_md1acca79_fillffffffff` | F343 | 322416 | 57448 | 46843 | 34750 | 74.18% | `a57_b5`, `a57_b2`, `e57_b0`, `a57_b6`, `a57_b22` |

F343 deltas under the same watcher:

| Candidate | Δ decisions | Δ backtracks | Δ learned exported | Δ learned touching watched |
|---|---:|---:|---:|---:|
| `bit2_ma896ee41_fillffffffff` | -2900 (-0.82%) | -262 (-0.45%) | -285 (-0.61%) | -974 (-2.64%) |
| `bit24_mdc27e18c_fillffffffff` | +10391 (+2.62%) | +160 (+0.27%) | -79 (-0.17%) | +279 (+0.80%) |
| `bit28_md1acca79_fillffffffff` | -45035 (-12.26%) | -598 (-1.03%) | +169 (+0.36%) | +14 (+0.04%) |

## Initial Read

F420 confirms that F419 was not a bit2-only artifact. Across all three
candidates, roughly 74-78% of exported learned clauses touch the actual-register
watch surface. This sharply contrasts with F417/F418's zero-touch result for
`dW57`/`dW58` aux rows.

The reusable cross-candidate signal is the register family, not a single bit:
learned clauses concentrate in `actual_p1_a_57`, but the hottest bits are
candidate-specific. Bit2 emphasizes low/mid bits 3/7/8, bit24 shifts into 14/16
and then 21-25 under F343, and bit28 emphasizes 2/5/6.

F343's solver-counter effect is not explained by raw learned-touch volume. Bit28
gets a large decision reduction while learned-touch count is essentially flat.
Bit24 gets worse while touching slightly more watched learned clauses. Bit2 is
mildly better while touching fewer watched clauses.

## Verdict

Do not continue Path B on F343/dW learned clauses. The learned-neighborhood
target is actual `a_57`, with candidate-specific bit positions. The next
mechanism-aligned intervention should be a revised Path A: priority or activity
pressure over each candidate's top `actual_p1_a_57` hotspot bits, not another
F343 phase/clause-placement nudge.

F420 does not yet provide a generalized learned-clause body. It provides a
generalized learned-clause neighborhood: actual `a_57` dominates where CDCL is
learning.

## Artifacts

- `F420_actual_register_cross_candidate_learned_neighborhood.json`
- `F420_actual_register_learned_neighborhood_scan.py`
- Final solver logs: `/tmp/F420_full/*.stderr.log` and `/tmp/F420_full/*.stdout.log`

## Compute Discipline

- 6 final-panel CNFs audited before solver launch; all `CONFIRMED`.
- 6 final-panel `cadical-ipasir-up` runs logged through `append_run.py`.
- 2 preliminary bit2 F420 runs were also logged before the runner discovered the
  missing local bit24 varmap; final analysis uses the `/tmp/F420_full` six-run
  panel.
- `validate_registry.py`: 0 errors, 0 warnings after logging.
