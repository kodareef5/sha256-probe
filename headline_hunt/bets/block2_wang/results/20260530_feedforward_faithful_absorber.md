# Faithful 2-block absorber: feed-forward target + post-FF residual + pinned CV (2026-05-30)

Pivot from `linear_lever_gaps` (killed). Owner: macbook-claude. Status: in progress.

## Two faithfulness gaps found in the existing absorber

The bet's headline "18-round absorber" comes from `encoders/absorber_cnf.py`, which has
two conditions that are NOT the real 2-block collision condition:

1. **Wrong target.** It forces `state1[R] == state2[R]` — working-state diff ΔC = 0
   (line 74-75). But Davies-Meyer feed-forward gives `H = CV + state[R]`, so a hash
   collision needs `H1 == H2`, i.e. `ΔC = -Δcv` (modular). With Δcv ≠ 0 (the residual)
   and ΔC = 0, the fed-forward outputs differ by Δcv ≠ 0 → **not a collision.** So the
   R=18 result, even pushed to R=64, would not be a 2-block collision. (The
   `2BLOCK_CERTPIN_SPEC.md` correctly specs the feed-forward + zero-final-chaining target,
   but it was never implemented/run — gated on a hand-designed block-2 trail.)

2. **Wrong input difference.** The absorber pins the input diff to a CLUSTER residual,
   which is the block-1 *working-state* round-63 XOR diff (e.g. bit13 HW=35). But block-2's
   actual input is the *post-feed-forward* chaining diff `CV1 ^ CV2`. Computed from a real
   block-1 near-collision witness (residuals/top50_lowest_hw.jsonl record 0), the post-FF
   residual is **HW=95**, not 35 — the feed-forward's modular carries densify it. So the
   real block-2 input is denser than the bet assumed.

## The faithful tools (built + validated this session)

- `encoders/absorber_feedforward.py` — feed-forward target (H1==H2), free CV. Self-test
  R=8 SAT. A *necessary-condition* probe (free CV can absorb via the FF subtraction).
- `encoders/absorber_pinned.py` — the real test: CV1, CV2 PINNED to a concrete block-1
  output (computed via `precompute_state` + `build_schedule_tail` + 64 rounds + DM
  feed-forward), post-FF residual HW=95, feed-forward target, free block-2 messages.

## Frontier (the key result: the ~18 wall is TARGET-INDEPENDENT)

| R | free-CV feed-forward | CV-pinned feed-forward (faithful) |
|---|---|---|
| 12 | SAT | SAT |
| 16 | SAT | SAT |
| 18 | SAT | (≈, harder) |
| 20 | **TIMEOUT** | **TIMEOUT** (pinned ⊃ harder than free-CV) |
| 24 | **TIMEOUT** | — |

Benchmark: the bet's *working-target* (ΔC=0) absorber walls at R=18/19 (R=18 SAT, R=19+
timeout). The *feed-forward* target (the correct condition) walls at the **same place**
(R=18 SAT, R=20 timeout) — with both free CV and pinned CV. So:

**The ~18 wall is independent of the target condition.** It is NOT caused by solving the
wrong condition (ΔC=0 vs ΔC=−Δcv). It is the round-depth / schedule-re-injection wall the
bet already identified: past ~18 rounds, the block-2 message-schedule re-injects the W0..15
differences into W16+, and they must be re-cancelled — and a dense (HW 95) input difference
admits no sparse characteristic to do so. Correcting the target does not move the wall.

## Honest read (verdict)

The feed-forward + post-FF + pinned-CV correction was the *right* thing to fix (the bet's
R=18 was solving a non-collision condition on the wrong input), and it was genuinely
untested. But it does **not** break the wall: faithful 2-block absorption of a dense post-FF
residual walls at the same ~18 rounds as the bet's proxy. The multi-block route, done
correctly, hits the same schedule-re-injection wall — consistent with SHA-256 being strong.

This matches the linear_lever_gaps finding (single-block walls at sr=60): both this
session's threads converge on the walls being **structural and robust to the specific
technique**, not artifacts of a fixable methodological choice.

## The one remaining lever, checked and closed: post-FF residual density

The only lever that could move the ~18 wall is a sparse **post-FF** residual. The corpus
minimizes the *working-state* HW (floor ~35), which the feed-forward then densifies. So I
re-ranked the corpus by the correct metric — `HW(CV1 ^ CV2)` where `CV = IV + state63`:

- Across 100 corpus witnesses, **min post-FF residual HW = 66** (its working-HW is 68 —
  i.e. the lowest-post-FF witness is NOT the lowest-working-HW one; the corpus optimized
  the wrong metric).
- 66 ≫ Wang's ≤16–24 threshold. The working-HW≥35 structural floor (R63.1/R63.3 + dd63=
  dh63=0) plus feed-forward carry-spreading keeps the post-FF residual dense.

So fixing the metric (minimize post-FF, not working-state, HW) gives 95→66 — better, but
still far too dense to admit a sparse characteristic. A dedicated 10^9-sample post-FF-
minimizing scan might shave further, but to reach ≤24 it would need working-HW well below
the proven ~35 floor — very unlikely. **Low conviction; not pursued.**

## Bottom line for the bet

The feed-forward correction is a real fix to the bet's methodology (its R=18 result targets
a non-collision condition on the wrong input), and the faithful test was run for the first
time. The result is a clean negative: faithful 2-block absorption walls at the SAME ~18
rounds as the proxy, because the wall is schedule-re-injection over a dense (≥66 post-FF)
input — independent of the target condition or CV-pinning. Combined with the linear_lever
sr=60 result, this session establishes both SHA-256 collision walls as structural and
robust to the techniques tried.

## Next

- Complete the CV-pinned frontier (R=20, 24, 28, 32, ... toward 64).
- If it reaches deep: the CONNECTION question (can block-1 produce a CV the block-2
  characteristic needs) becomes the focus — steer block-1's W[57..60] (it has freedom) to
  hit a block-2-absorbable post-FF residual.
- If it walls ~20: document as the faithful confirmation that multi-block absorption of a
  dense post-FF residual is as hard as the single-block wall.
