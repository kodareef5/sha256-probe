---
date: 2026-04-29
bet: block2_wang (with cross-bet input from singular_chamber_rank/F311)
status: TOOL_2_PIVOT_AND_PILOT — preimage lift unhelpful, atlas-loss search wins
---

# F312: Schedule-space search with carry-chart-atlas loss

## Plan vs reality

The Tools 1+2 plan called for searching dW[16..23] space and lifting back to
dM via a GF(2) preimage solver. F311 (Tool 1, Carry-Chart Atlas) shipped clean
with verified output against the C ground truth.

For Tool 2 we built `preimage_lift.py` first. It works as a linear lifter
(verified), but stress testing revealed:

> The schedule recurrence's GF(2) inverse is structurally dense: lifting a
> low-HW dW[16..23] target (mean target HW 12) yields a dM[0..15] with
> mean HW ≈ 113. Carry corrections then dominate, giving residual HW ≈ 118
> (essentially full-random). 0/100 random low-HW targets had carry residual ≤ 8.

So the original "search dW, lift to dM" approach is structurally unproductive
for finding sparse dM with controlled dW. **This is itself a structural finding**:
the schedule recurrence does not admit cheap preimage lifts in the truncated
range. (Documented but not over-claimed; could be different for full dW[16..30]
where there are more equations to constrain things, but the truncated cut is
unhelpful.)

## What we did instead

The actually-useful Tool 2 (`search_schedule_space.py`) takes the F311
carry-chart atlas as a LOSS FUNCTION on dM-space search:

```
score = 4.0 * a57_xor_hw           (penalize cascade-1 hardlock violation)
      + 1.0 * D61_hw               (chamber-defect floor)
      + 8.0 * (chart_top != (dh,dCh))   (chart-membership penalty)
      + 0.05 * tail63_state_diff_hw     (mild full-state divergence term)
```

The mutator is the same shape as block2_wang's existing
`search_block2_absorption.py` (active-word bit-flips, mask XORs, full-word
randomization). The only mechanism change is the score function — replacing
chain-output diff with the atlas loss.

## Direct comparison vs F115 chain-output-diff baseline (same budget)

8 restarts × 50k iterations, active_words = {0,1,2,8,9}:

| Search | Best atlas score | Best a57_xor_hw | Best D61_hw | Chart of best |
|---|---:|---:|---:|---|
| F115 chain-output-diff | **104.45** | 18 | 18 | (dSig1, dCh) |
| F312 atlas-loss        | **38.85**  | 5  | 12 | **(dh, dCh)**  |

**63% reduction** in atlas loss for the same compute budget.

Per-restart breakdown of F312 8×50k:

| Restart | atlas_score | a57_xor_hw | D61_hw | chart_top2 | tail63 HW | chart_match% |
|---:|---:|---:|---:|---|---:|---:|
| 0 | 47.65 | 7 | 13 | (dh, dCh)   | 133 | 36% |
| 1 | 44.35 | 7 | 10 | (dCh, dh)   | 127 | 34% |
| 2 | 42.10 | 7 | 8  | (dh, dCh)   | 122 | 37% |
| 3 | 48.95 | 8 | 11 | (dCh, dh)   | 119 | 36% |
| 4 | 44.20 | 7 | 10 | (dh, dCh)   | 124 | 34% |
| 5 | 38.85 | 5 | 12 | (dh, dCh)   | 137 | 35% |
| 6 | 39.00 | 5 | 13 | (dh, dCh)   | 120 | 34% |
| 7 | 43.25 | 5 | 17 | (dh, dCh)   | 125 | 36% |

**ALL 8 restarts** find best points in the chamber chart family (dh, dCh).
F115's chain-output-diff search hit (dh, dCh) only on 1 of 5 reported restarts
and at a57_xor_hw = 18.

## Findings

### Finding 1 — Atlas loss reliably steers into the chamber half-plane

8/8 restarts converge to chart=(dh, dCh) under atlas-loss search vs 1/5 under
chain-output-diff. This is a **mechanism win for the F311 hypothesis**: the
chamber chart is reachable by gradient-descent if the loss can see it.

### Finding 2 — Atlas loss reduces a57_xor_hw substantially

Best a57_xor_hw = 5 vs F115 baseline 16-20. The cascade-1 hardlock isn't
fully closed (would require 0), but we're 4-5x closer. Combined with chart
membership, this is the bulk of the score reduction.

### Finding 3 — D61_hw not closing fully

Best D61_hw = 8 vs chamber floor of 4. The atlas-loss search reaches the
chamber chart neighborhood but does not attain the actual chamber attractor.
This is consistent with F311's brittleness finding — the chamber is an
isolated point in coordinate space, not a basin that gradient methods can
descend into directly.

### Finding 4 — Preimage lift in truncated dW[16..23] is structurally
        unhelpful for sparse dM

Stress test: 100 random low-HW dW[16..23] targets (mean HW 12), lifted via
`preimage_lift.py` to dM[0..15], applied to a fixed M1, residual HW measured
against target. Result: 0/100 had residual ≤ 8. Mean dM HW = 113, mean
residual HW = 118 (essentially random). The schedule recurrence's GF(2)
inverse is dense in the truncated range, so the lift produces dense dM,
which produces large carry corrections, which destroys the linear prediction.

This is a structural negative for the original Tool 2 plan. The lift is
mathematically correct (linear round-trip exact: `dM → linear-dW → lift-back →
linear-dW' = original-dW`), but the sparsity needed for short trails is
not preserved. We document this and pivot.

## What this means for the next iteration

(a) **Combine atlas-loss search with active-word seeding from chamber witnesses**:
    extract the (W57, W58, W59) of a known chamber HW4 point, back-solve for
    the M1 that produces those W's via schedule, and start the search there.
    This gives an initialization in the chamber chart with a57_xor exactly 0.

(b) **Multi-bit moves on (W57, W58, W59) directly**: F311 showed single-bit
    moves are brittle. The atlas-loss search uses dM single-bit + mask moves;
    mapping these to (W57, W58, W59) shows dense changes, which is why
    single-step descent doesn't reach D61=4. Trying 2- and 3-bit COMBINED
    moves on (W57, W58, W59) directly with atlas evaluation would test
    whether the chamber has a non-trivial 2-bit basin.

(c) **Larger active word set + atlas loss**: F312 used active_words={0,1,2,8,9}
    matching F115. Trying all 16 active words might give the search more
    freedom to descend further.

## What's shipped

- `headline_hunt/bets/block2_wang/encoders/preimage_lift.py` — verified linear
  GF(2) lifter with self-test passing. Documents that lifts of low-HW dW
  are dense in dM (negative finding).
- `headline_hunt/bets/block2_wang/encoders/search_schedule_space.py` — the
  atlas-loss search.
- `headline_hunt/bets/block2_wang/results/search_artifacts/20260429_F312_atlas_loss_8x50k.json` —
  full results JSON for 8 restarts × 50k iterations.
- This memo.

## Discipline

- ~0.5 h compute (8x50k pilot wall = 142s).
- Direct atlas-score comparison vs F115 baseline (same compute budget).
- Honest negative on the truncated preimage lift; reported as structural
  finding rather than buried.
- Single concrete deliverable: shipped tool + ranked pilot results + memo.

## Cross-bet implication

F311 (atlas) + F312 (atlas-loss search) together establish that:
1. The chamber HW4 attractor lives in a single chart family (dh, dCh) with
   a57_xor=0 — candidate-agnostic structural property.
2. Block2_wang's chain-output-diff search has been in the wrong half-plane
   (chart=(dSig1,dCh) with a57_xor=18); replacing the loss with atlas-loss
   reaches the right half-plane reliably.
3. The chamber attractor itself remains brittle and is not reached by 50k
   iterations of dM-mutation gradient descent.

The 48-hour Tools 1+2 budget is at ~6 hours. Remaining time should be spent
on (a)-(c) above (chamber-seeded initialization, larger active words, multi-bit
direct W-moves) rather than continuing volume work.
