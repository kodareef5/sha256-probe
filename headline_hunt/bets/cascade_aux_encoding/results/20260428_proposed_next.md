# cascade_aux_encoding — proposed next high-leverage action (2026-04-28)

## Context

Bet status: in_flight, owner=macbook, 785 runs logged, 3.6 CPU-h of
200 budget used. Mode B characterized (2-3.4× front-loaded
preprocessing). Stack hints characterized (1.5-2.5× at ≤100k budget,
regress at ≥500k). de58-de59-stack is current default for low budgets.

Empirical posture (BET.yaml): "Past ~200k base catches up; stack hurts
via restart-heuristic interference." The original SPEC's "≥10× SAT
speedup" is empirically REFUTED at all tested budgets.

## What the principles framework derived today

The 24-hour principles arc (april28_explore/principles/, 23 syntheses
+ 36 deep dives) produced:

- **Σ-Steiner Cayley graph**: tw ≈ 28, spectral gap = 2/3, α = 4
- **3-level partial difference set / association scheme** structure
- **8 polynomial-time algorithm candidates** with rigorous guarantees
  (matroid intersection, BP-Bethe with level-4, Σ-aligned F4, submodular-
  greedy, treewidth DP, Forney GMD, Ricci preprocessing, quantum AA)
- **Predicted BP-Bethe convergence: 10-20 iterations** (from spectral
  gap 2/3) → ~10⁷ ops total per cascade-1 instance

These are POLY-TIME alternatives to CDCL that should match yale's
HW=33 floor with rigorous quality bounds.

## The single highest-leverage next action

**Build a BP-Bethe baseline for cascade_aux at N=8 (maybe N=12).**

This is the bridge from the cascade_aux_encoding bet (which currently
characterizes CDCL behavior with hints) to the principles framework's
algorithmic predictions (which says BP-Bethe should be FASTER than
CDCL on cascade-1 Tanner graphs).

Why high-leverage:

1. **Validates the principles prediction empirically**. If BP-Bethe at
   spectral-gap=2/3 actually converges in 10-20 iterations on a real
   cascade_aux CNF, the framework's prediction is corroborated.

2. **Provides a NEW algorithmic baseline** beyond CDCL+hints. Mode B's
   2-3.4× speedup is preprocessing only; BP-Bethe could give a
   different shape of speedup (poly-time marginal computation, not
   conflict-driven search).

3. **Cascade_aux's hint design contradicted collision-finding**: stack
   hints fix de58/de59 to non-zero values incompatible with HW=0.
   BP-Bethe doesn't have this issue — it computes marginals, doesn't
   restrict the solution space.

4. **Opens path to integrate matroid intersection and Σ-aligned F4**
   in subsequent steps. BP-Bethe is the simplest of the 4 algorithm
   candidates with implementable pseudocode.

## What success looks like

A working BP-Bethe implementation that, on a single cascade_aux N=8
CNF:
- Converges in ≤50 iterations (predicted 10-20)
- Produces marginals consistent with the known SAT/UNSAT verdict
- Runs in <1s wall (predicted ~10⁷ ops)
- Outputs a proposed M with HW(SHA(M)) within 2× of yale's floor

## What success would tell us

**If BP-Bethe matches/beats CDCL+hints**: the cascade_aux bet has a
new algorithmic direction beyond preprocessing-style speedups. The
principles framework's BP-Bethe prediction is validated empirically.

**If BP-Bethe converges but produces poor marginals**: the level-4
cycle correction is needed (gaps 9, 11 multiplicity-2 in Σ-Steiner).
Subsequent step is generalized BP at level 4.

**If BP-Bethe diverges or runs slow**: the spectral gap = 2/3 prediction
is wrong (or the Cayley graph's spectrum doesn't transfer to the full
cascade_aux Tanner graph). Framework needs revision.

Each outcome is informative and actionable.

## Time estimate

**Implementation**: ~3-5 days for working BP-Bethe code.
- Day 1: build Tanner graph from cascade_aux CNF (existing CNF reader)
- Day 2: implement standard BP message passing (sum-product)
- Day 3: log-domain numerical stability + damping
- Day 4: convergence diagnostics + marginal extraction
- Day 5: marginal-guided HW search + comparison to existing CDCL
  results

**Initial sanity check (today, <30min)**: count cycles in cascade_aux
N=8 Tanner graph to verify the gap-9/11 4-cycles are the dominant
short-cycle contributor (per principles framework prediction). If yes,
level-4 cluster expansion is the right correction; if no, framework
prediction needs adjustment before BP implementation.

## Today's <30min concrete action

I'm running this NOW: count 4-cycles in a small cascade_aux CNF
Tanner graph and check whether they cluster on the predicted
gap-9/11 multiplicity-2 edges. This is a pure analysis task on
existing CNF files, no new compute, sub-30min execution.

## Connection to other bets

- block2_wang: yale's heuristic operates on block2_wang trail bundles.
  BP-Bethe on cascade_aux gives a poly-time alternative for
  block2_wang's residual-extraction step.
- programmatic_sat_propagator: the 4 principles algorithms are
  alternatives to CDCL+propagator. If BP-Bethe works, this bet's
  "different propagator" need is partially obviated.
- mitm_residue: BP-Bethe marginals on cascade_aux give the 4-d.o.f.
  free-rank structure that mitm_residue empirically locked.

## Status

Memo written 2026-04-28T14:00 EDT. Highest-leverage next action
identified: build BP-Bethe baseline for cascade_aux. Today's <30min
action: 4-cycle structure verification on cascade_aux N=8 Tanner
graph (running concurrently with this memo).
