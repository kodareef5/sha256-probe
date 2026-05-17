# Task Portfolio: Hunt sr=64

Date: 2026-05-17

Goal: spend time on work that can plausibly move from sr=60 relaxed-schedule
collisions toward sr=64 full-schedule collisions. This packet is for research
execution, not publishing or presentation cleanup.

## Core judgement

The next progress will probably not come from more black-box SAT on unchanged
CNFs. The useful work is either:

1. Press the sr=61 boundary with changed structure, changed encodings, or
   changed candidate geometry.
2. Build new algebraic objects that reveal a lower-dimensional route to the
   full schedule.
3. Convert speculative math into measurable predictors or solver constraints.

If an idea cannot produce a certificate, a ranked candidate list, a learned
lemma, a smaller CNF, a lower residual, or a falsifiable negative result, it
should not consume prime compute.

## Time split for the next 4 weeks

| Track | Time | Purpose |
|---|---:|---|
| A. sr=61 pressure | 35% | Try to get a true sr=61 certificate or a precise obstruction. |
| B. New algebraic angles | 35% | Build tools that change the search space, not just tune it. |
| C. Block-2 / alternate trails | 15% | Avoid being trapped by the single-block cascade mechanism. |
| D. Speculative math triage | 10% | Test zeta, p-adic, manifold, and dimensionality ideas as predictors. |
| E. Verification discipline | 5% | Only the minimum needed to trust certificates and avoid wasted runs. |

## Independent work packets

1. `sr61_pressure_tasks`: direct boundary pressure with assumption ladders,
   defect-surface mining, certificate inverse-lifts, and non-cascade sr=61.
2. `new_angles_algebraic_tasks`: human-assisted algebraic work, carry chambers,
   programmatic SAT lemmas, MITM residue, and block-2 trail construction.
3. `speculative_math_triage`: zeta/manifold/Riemann-adjacent ideas converted
   into experiments with concrete pass/fail outputs.
4. `free_word_shaping_mitm`: focused plan for shaping the remaining relaxed
   words and meeting schedule-side constraints in the middle.
5. `time_budget_and_artifacts`: near-term schedule and artifact checklist.

## Working rules

- No seed farming on unchanged sr=61 CNFs.
- Every compute batch must vary at least one of: encoding, candidate family,
  kernel, assumptions, objective, or propagator.
- Prefer small exact reduced-N experiments if they produce a transferable
  invariant.
- Treat "manifold", "zeta", "dimension", and "entropy" as names for measurable
  objects, not as explanatory language by themselves.
- A negative result is valuable only if it closes a mechanism class, not a
  single unlucky candidate.
