---
date: 2026-05-01
bet: programmatic_sat_propagator
status: ACTUAL_A57_HOTSPOT_PRIORITY_MATRIX
parents: F397, F399, F407, F416, F420
evidence_level: EVIDENCE
---

# F421: actual `a_57` hotspot priority does not dominate F343

## Choice

I executed revised Path A rather than pivoting. F420 gave a concrete learned
neighborhood: actual `a_57`, not `dW57/dW58`. The right next test was therefore
whether bounded `cb_decide` pressure on those hotspot vars changes the 50k
conflict trajectory.

The hotspot arm uses `--priority-max-suggestions=132`. F407/F411 already showed
uncapped `cb_decide` oversteers, so this matrix tests the controlled opening-book
version of the idea.

## Setup

Candidates and hotspot bits:

- `bit2_ma896ee41_fillffffffff`: `actual_p1_a_57` bits 3, 7, 8
- `bit24_mdc27e18c_fillffffffff`: bits 14, 16, 21, 22, 23, 24, 25
- `bit28_md1acca79_fillffffffff`: bits 2, 5, 6

Arms:

- `baseline`: C++ cascade propagator, no F343, no decision priority
- `f343`: same runner with F343 clauses injected into the CNF
- `hotspot_priority_max132`: baseline CNF plus `cb_decide` priority over the
  candidate's F420 hotspot bits, capped at 132 suggestions

Each arm ran seeds 0, 1, 2 at 50k conflicts. All solver results are `TIMEOUT`
under the cap.

## Results

Mean decisions across three seeds:

| Candidate | Baseline | F343 | Δ F343 | Hotspot priority | Δ hotspot |
|---|---:|---:|---:|---:|---:|
| `bit2_ma896ee41_fillffffffff` | 351404 | 346135 | -1.50% | 403384 | +14.79% |
| `bit24_mdc27e18c_fillffffffff` | 406585 | 404511 | -0.51% | 312426 | -23.16% |
| `bit28_md1acca79_fillffffffff` | 368777 | 322814 | -12.46% | 415560 | +12.69% |

Mean backtracks:

| Candidate | Baseline | F343 | Hotspot priority |
|---|---:|---:|---:|
| `bit2_ma896ee41_fillffffffff` | 58024 | 57720 | 58828 |
| `bit24_mdc27e18c_fillffffffff` | 58939 | 58857 | 57144 |
| `bit28_md1acca79_fillffffffff` | 58030 | 57472 | 58928 |

Aggregate candidate-normalized decision delta:

- F343: -4.82%
- Hotspot priority max132: +1.44%

## Read

The actual-register hotspot is a real learned-clause neighborhood, but direct
priority pressure is not a general rescue.

Bit24 is the one strong positive: the hotspot arm cuts mean decisions by 23.16%
and backtracks by about 1795 versus baseline. That says the F420 surface can be
actionable for a candidate whose learned hotspot is shifted into bits 14/16/21-25.

Bit2 and bit28 go the other way. The same priority mechanism inflates decisions
by 14.79% and 12.69%, respectively, while F343 remains mildly helpful for bit2
and strongly helpful for bit28. The priority arm also drives 132 suggestions and
roughly triples `cb_propagate` fires on bit2/bit28, which is consistent with the
F407 oversteer warning even after capping.

## Verdict

Actual `a_57` hotspot priority does **not** dominate F343-style nudges on this
panel. It is candidate-specific: promising for bit24, harmful for bit2 and
bit28. Do not deploy it as a universal revised Path A operator.

Relative to F416's F343 phase-hint trace, the same conclusion holds: hotspot
priority is a bit24 lead, not a panel-wide replacement for phase or clause
nudges.

Best next follow-up, if continuing Path A, is a bit24-only refinement: test
whether the win comes from the high-bit cluster 21-25 or from bits 14/16, and
whether a smaller cap preserves the gain with less `cb_propagate` overhead.
For bit2 and bit28, the current hotspot-priority direction should stop.

## Artifacts

- `F421_actual_a57_hotspot_priority_matrix.json`
- `F421_actual_a57_hotspot_priority_specs.json`
- Runner extension: `propagators/run_decision_priority_matrix.py --hotspot-matrix`
- Logs: `/tmp/F421_hotspot_priority/*.stderr.log` and `*.stdout.log`

## Compute Discipline

- Added `--seed=N` to `cascade_propagator.cc` and set CaDiCaL's seed before
  solving.
- 27 final solver launches audited before solve; all audited `CONFIRMED`.
- 27 final `cadical-ipasir-up` runs logged via `append_run.py`.
- `validate_registry.py`: 0 errors, 0 warnings.
