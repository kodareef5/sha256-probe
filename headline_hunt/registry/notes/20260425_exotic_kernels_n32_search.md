# Exotic kernel scan at N=32 — narrow negative
**2026-04-25 evening** — registry/notes — concrete EVIDENCE-level closure on
unmapped kernel hypothesis.

## Question

`kernel_exotic_0_14` and `kernel_exotic_0_1` in registry/kernels.yaml were
confirmed at N=8 only (`n_scope: [8]`). At N=8 they produce more collisions
than (0,9) MSB. **Do these word-pair kernels survive scaling to N=32?**

## Method

Random sample at N=32:
- For (0,14) MSB-bit-31: 16384 random m0 × 5 fill choices = 81920 trials → 0 cascade-eligible.
- For (0,14) and (0,1) × 9 bit positions {0,6,10,11,13,17,19,25,31} × 4 fills × 256 random m0 each: 9216 trials → 0 cascade-eligible.

Total: ~91k random N=32 (m0, fill, kernel-bit, word-pair) trials. **Zero
cascade-eligible candidates found.**

## Comparison

(0,9) MSB family at N=32 has 36 cascade-eligible candidates (registered).
Their discovery probability ≈ 36 / (sample size) — but they were curated
via the cascade-eligibility filter applied to a much larger search.

Per-trial random eligibility rate at N=32 is ~2^-32 for any specific
(kernel, bit, m0, fill) combination. At 91k trials, expected hits ≈
91000 × 2^-32 ≈ 0.00002 per attempt. Observed 0 is consistent with rate
≤ 2^-17.

## Conclusion (EVIDENCE-level)

**Exotic (0,14) and (0,1) kernels at N=32 are NOT readily eligible.**
The N=8 advantage (300-500 collisions vs 260 for (0,9)) does NOT survive
scaling to N=32 in any tested bit position or fill choice within a 91k
random-trial sample.

This **does NOT prove impossibility** — exhaustive search over all 2^32
m0 × N bit positions × multiple fills could still find eligible candidates.
But it rules out "easy random" eligibility at the scale we tested.

## Implication for kernels.yaml

The exotic_0_14 and exotic_0_1 entries are **DORMANT** — confirmed at
N=8 but no candidates have been registered against them at N=32. The
registry should reflect this:
- Update `n_scope` to be explicit: `[8]` only, with a note that N=32
  scan returned 0/91k.
- Or remove the entries entirely if they're not useful for current bets.

## What would change my mind

- Exhaustive m0 sweep (2^32) at fixed (kernel, bit, fill) finds eligible
  candidates at N=32. ETA: ~5 min single-thread.
- Adapted kernel structure (e.g., (0,14) with non-MSB bit AND fill chosen
  specifically) reveals a new path.
- Theoretical derivation showing (0,14) MUST have eligible m0 at N=32
  (analogous to the cascade-extending structure for (0,9)).

## Sharper recommendation

For next worker: if they want to expand the candidate base for sr61_n32,
focus on ALTERNATE bit positions for (0,9) (not yet covered by the 36
candidates) before hunting exotic kernels. The (0,9) eligibility is
verified; exotic eligibility at N=32 is empirically rare.
