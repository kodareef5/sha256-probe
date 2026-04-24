# Kill criteria — sr61_n32 (BUDGET-CAPPED)

This bet has a hard CPU cap. Two parallel kill conditions:

## #1 — Compute budget exhausted with no SAT and no signal

**Trigger**: cumulative `cpu_hours_spent` reaches 10000 (counting from 2026-04-24
onward, not including pre-pause 1800h) AND:
- no SAT certificate produced,
- no measurable solver-behavior improvement attributable to a new encoding,
- no structural predictor identified that distinguishes promising from hopeless candidates.

**Why this kills**: GPT-5.5's hard limit. Beyond 10k CPU-h without ANY of those signals,
this is seed farming with extra steps.

**Required evidence to fire**:
- `summarize_runs.py` output showing per-candidate CPU spend totaling >= 10k.
- `comparisons/encoding_signal.md` documenting per-encoding solver behavior delta.
- Honest assessment in `results/decision.md` that no predictor was found.

## #2 — Audit failure rate exceeds 1 in 100 runs

**Trigger**: If `audit_cnf.py` flags more than 1% of submitted runs as wrong-labeled,
the bet is closed pending pipeline fix. (This is a process control kill, not a research kill.)

**Why this kills**: The CNF audit disaster cost ~2000 CPU-hours. We will not pay that twice.
A high audit failure rate means the pipeline is regressing.

**Required evidence to fire**:
- `summarize_runs.py` audit-failure column shows rate above 1%.

## Reopen triggers (research-direction)

- A new mechanism (cascade_auxiliary_encoding succeeds, programmatic_sat_propagator
  ships, block2_wang sheds light on residual structure) materially changes solver behavior.
- A new TRUE sr=61 candidate class is discovered that has not been previously tested.

## Reopen triggers (process)

- Audit pipeline fixed AND validated against historical CNFs (back-audit confirms
  the existing labels match clause-structure inference).
