# Kill criteria — math_principles_calibration

> **Status**: SCAFFOLDED 2026-04-30 by macbook. Yale (owner) to fill in.
> The criteria below are placeholders inferred from the bet's README and
> commit history. Yale should review, edit, and replace them with the
> real falsification gates yale has in mind.

## Inferred placeholder kill criteria (TBD by yale)

The math_principles bet's stated goal is "small, checkable tools" that
turn the April 2026 math-principles survey into measurement and triage.
Plausible kill criteria, given the active research lines:

### Placeholder #1 — REM/tail-law fit fails on block2 corpus

**Trigger**: The Random Energy Model / tail-law fits on the block2_wang
absorber-score corpus do not produce useful predictive power on
out-of-sample new candidate scores.

**Proxy metric**: predictive R² < 0.3 across new candidates added to
the corpus after the fit was constructed.

**Why this would kill**: If the math-principles framework can't predict
which active-word sets will score well in block2_wang, the framework's
value-add is limited.

### Placeholder #2 — Submodular mask selection doesn't outperform random sampling

**Trigger**: Submodular-greedy active-word selection (F343/F344 lineage
on yale side) doesn't beat uniform-random masks at finding low-score
absorbers in block2_wang.

**Proxy metric**: Expected score after K=100 evaluations is no better
than random ±1 standard deviation across 5 cands.

**Why this would kill**: Submodular structure is the principles
framework's bet on active-word interactions. If random matches it,
the framework is descriptive but not prescriptive.

### Placeholder #3 — Strict-kernel basin search produces no novel SAT

**Trigger**: Yale's strict-kernel basin search + bridge-cube design
chain (F370+) produces no SAT-finding artifact distinct from what
macbook's F339-F369 propagator-side work already produces.

**Proxy metric**: 0 SAT instances and no UNSAT proof simpler than
the IPASIR-UP approach across yale's accumulated CDCL bridge cubes.

**Why this would kill**: If the basin search is structurally
equivalent to macbook's CDCL preflight (same Class 1a-univ + Class 2
clauses derivable both ways), yale's framework adds analytic clarity
but no headline-class output.

## Reopen triggers (TBD by yale)

- A math-principles fit predicts a candidate that, when run through
  block2_wang, yields a score < 80 (current best is 86) — would
  indicate the framework has prescriptive power.
- Yale's bridge-cube design produces a SAT model that solver-only
  search has not reached.
- A new abstraction (sub-corpus structure, hidden symmetry) emerges
  from the principles framework that was not visible to direct
  empirical search.

## Notes

- This file was scaffolded by macbook 2026-04-30 because the
  `math_principles` bet directory had no BET.yaml or kill_criteria.md
  while every other bet did. The discipline gap was real; the placeholder
  content here is best-effort inference from yale's README + commit
  history. Yale should replace these with real criteria when convenient.
- The `BET.yaml` next to this file documents the scaffolding decision
  in full; see its `scaffold_notes_2026-04-30` field.
