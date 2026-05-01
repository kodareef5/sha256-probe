---
date: 2026-04-30
bet: programmatic_sat_propagator
status: DECISION_PRIORITY_CONTROL_VERDICT
parents: F397, F403, F405, F406
---

# F407: decision-priority needs a bounded nudge, not full branch takeover

## Setup

Yale-side dependency blocker is fixed with repo-local CaDiCaL 3.0.0 headers/lib
and nlohmann/json. The F397 matrix can now compile and run locally through
`run_decision_priority_matrix.py`.

The missing F397 sr60/force CNF+varmap inputs were regenerated locally from
`cascade_aux_encoder.py --varmap +`, giving all 6 F397 candidates runnable.
Those CNFs/varmaps are ignored reproducible artifacts.

## Result 1: uncapped priority is harmful

F403 ran the 6-candidate matrix with the original cb_decide policy: whenever
CaDiCaL asks for a decision, return the next unassigned priority var.

That oversteers the solver. Every priority arm is slower than the existing
propagator, and decision counts inflate sharply:

| Candidate | F286 decision delta | F332 decision delta | F286 wall delta | F332 wall delta |
|---|---:|---:|---:|---:|
| bit10 | +16.5% | +98.9% | +10.8% | +53.1% |
| bit11 | +84.7% | +48.2% | +36.9% | +20.1% |
| bit13 | +150.8% | +141.9% | +60.5% | +56.9% |
| bit0 | +65.5% | +65.1% | +21.7% | +16.7% |
| bit17 | +58.3% | +125.9% | +19.1% | +71.8% |
| bit18 | +29.5% | +59.6% | +7.1% | +15.1% |

Verdict: do not deploy uncapped F397 priority as a replacement branching
policy.

## Result 2: cap-132 partly rescues the idea

F405 added `--priority-max-suggestions=132`: the priority list can nudge
early search, then CaDiCaL takes over.

Best capped outcome per candidate:

| Candidate | Best capped arm | Wall delta | Decision delta | Verdict |
|---|---|---:|---:|---|
| bit10 | F286 max132 | -20.8% | -10.8% | useful |
| bit11 | F332 max132 | +4.4% | +9.0% | not useful |
| bit13 | F332 max132 | +7.7% | +19.8% | not useful |
| bit0 | F332 max132 | +5.0% | -4.7% | mixed |
| bit17 | F332 max132 | -0.1% | +2.2% | neutral |
| bit18 | F332 max132 | +4.2% | -1.3% | mixed |

Verdict: bounded priority is a candidate-specific control knob. It is not a
universal policy, but it is no longer dead: bit10 shows a real win, and bit0 /
bit18 show decision-count improvement with small wall cost.

## Result 3: stride-16 is worse on bit10

F406 tested `--priority-max-suggestions=132 --priority-stride=16` on bit10.
Spreading suggestions across the run lost the cap-132 benefit:

| Arm | Wall | Decisions | cb_decide |
|---|---:|---:|---:|
| existing propagator | 4.090s | 370215 | 0 |
| F286 max132 stride16 | 4.162s | 436887 | 132 |
| F332 max132 stride16 | 4.067s | 439118 | 132 |

Verdict: if priority helps, it helps as an early bounded perturbation, not as a
slow periodic intervention.

## Engineering Changes

- Added `--priority-max-suggestions=N` to the C++ propagator.
- Added `--priority-stride=N` to the C++ propagator.
- Extended the matrix runner so capped/strided priority policies are first-class
  reportable arms.

## Next

F402 asked the right follow-up: test whether F397-style decision nudging rescues
`bit2_ma896ee41`, the singleton F343 outlier.

Current blocker: F397 only contains priority specs for the 6 F332 hard-core
stability candidates, not bit2. The next useful implementation is a bit2
priority-spec generator that maps the F286/F332-style feature recipe onto
bit2's sr60/force varmap, then runs:

1. existing propagator
2. F343-injected baseline if available in this C++ path
3. bit2 priority max132
4. bit2 priority max132 plus F343, if clause injection is wired here

The priority lesson is now clear enough: do not ask cb_decide to drive the
whole solve. Use it as a short, candidate-gated opening book.
