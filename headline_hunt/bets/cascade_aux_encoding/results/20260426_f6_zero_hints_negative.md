# F6: de60..de63=0 zero hints — mixed/negative
**2026-04-26 19:35 EDT**

Followup to F4b (commit 7be3536, de58+de59 stack 1.87× n=18). Tested
whether stacking 4×32=128 additional unit clauses fixing de60..de63
to 0 helps beyond the 64-bit stack.

Structural justification: under cascade-1, de60=de61=de62=de63=0 is
forced empirically (verified across multiple chambers, all four cands
tested). So these zero hints are theoretically free — they tell the
solver about constraints the encoder may not propagate efficiently.

## n=4 result (3 seeds, 50k kissat budget)

| cand | base (F1) | stack-only (F4b) | stack + zero (F6) | F6 vs stack |
|---|---:|---:|---:|---:|
| idx0  | 2.83 | 1.74 (1.63×) | 1.43 (1.98×) | **1.22× better** |
| idx8  | 2.74 | 1.04 (2.64×) | 1.82 (1.51×) | **0.57× WORSE** |
| idx17 | 2.45 | 1.65 (1.48×) | 1.73 (1.42×) | 0.95× (slight worse) |
| bit19 | 2.54 | 1.61 (1.58×) | 1.36 (1.87×) | 1.18× better |

idx8's stack-only result was the n=18 ceiling case (2.64×). Adding
the 128 zero hints DROPS that to 1.51×, a major regression. idx0 and
bit19 improve but the gain is below the n=4 noise floor for some
cands.

## Why it's negative

Hypothesis: the encoder's cascade-2 + extension constraints already
encode de60=de61=de62=de63=0. The 128 explicit unit clauses are
redundant in a way that interacts badly with kissat's elimination
phase / restart strategy on certain cands.

Specifically, when the encoder's clauses derive de_k=0 through a
specific propagation chain, a unit clause at the front fixes the
variable PRE-cascade-clause-firing, which can block certain
implication graphs the solver would otherwise explore.

Net effect: **stack-only is the safer deployable variant.** Adding
the zero hints is high-variance and at minimum risks cancelling the
biggest stack-only wins.

## Decision

- **Do NOT ship** in wrapper as a default.
- The 64-bit stack remains the recommended default (commit 9427f17).
- Keeping this memo as a kill record so future iterations don't
  re-attempt the same naive approach without acknowledging the
  encoder-interaction risk.

## What might still work

If we wanted to push beyond 1.87× median, options are:

1. **Mode B + stack composition (F7)**: orthogonal mechanisms (Mode B
   restricts solution set; stack adds unit propagation). Worth testing.
2. **da[58..60]=0 explicit hints**: cascade-1 forces these but maybe
   the encoder's chain-of-reasoning is suboptimal for them too.
3. **Earlier-slot hints**: a[57], a[58] aux variables — if these have
   per-chamber size 1, they'd be NEW info compared to e-slot hints
   (they index different state-vector components).

EVIDENCE-level: HYPOTHESIS — at n=4, F6 is mixed and risks idx8-style
regressions. n=18 not run because the n=4 ceiling case regressed by
~50%, suggesting deployment risk dominates expected gain.
