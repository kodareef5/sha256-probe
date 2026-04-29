---
date: 2026-04-29
bet: cascade_aux_encoding
status: HYPOTHESIS_REFUTED — σ1 fan-in does NOT predict W2_58 core fraction
---

# F323: σ1-fan-in hypothesis test on W2_58 anchors

## Hypothesis (F287 next probe (b))

F287 noted that σ1 OUTPUT bits 22-31 have 2-bit fan-in (because SHR-10
truncates), while bits 0-21 have full 3-bit fan-in. Hypothesis: bits with
LIGHT (2-bit) fan-in should have HIGHER mean-core-fraction at W2[58]
across cands, because they're "structurally easier to constrain to a fixed
value via cascade-1 hardlock".

## Test

Computed per-bit core-fraction at W*_58 across the 10 sr60 hard_core JSONs
(F269/F270/F272/F283 series).

For each (word, round, bit), count fraction of 10 cands that include that
bit in their schedule_core list. Then compare:

- light bits {22..31}: σ1 OUTPUT fan-in 2
- dense bits {0..21}: σ1 OUTPUT fan-in 3

## Result

```
=== W2_58 per-bit core fraction (10 cands) ===
b 0: 0.50          b 8: 0.80          b16: 0.90          b24: 0.90
b 1: 0.90          b 9: 0.80          b17: 0.80          b25: 0.80
b 2: 0.50          b10: 0.80         *b14: 1.00         *b26: 1.00 ← anchors
b 3: 0.50          b11: 0.50          b18: 0.60          b27: 0.80
b 4: 0.70          b12: 0.80          b19: 0.90          b28: 0.90
b 5: 0.90          b13: 0.80          b20: 0.70          b29: 0.90
b 6: 0.90          b15: 0.80          b21: 0.80          b30: 0.40
b 7: 0.80                              b22: 0.80          b31: 0.00 ← always shell
```

| Group | Mean core-fraction | n |
|---|---:|---:|
| W2_58 light bits 22-31 (σ1 fan-in=2) | **0.730** | 10 |
| W2_58 dense bits  0-21 (σ1 fan-in=3) | **0.759** | 22 |
| difference (light − dense)            | **−0.029** | |

**Hypothesis REFUTED.** Light bits are *slightly LOWER* in mean core-fraction,
not higher. The σ1 OUTPUT fan-in does not predict W2_58 universal-core
anchoring.

## Cross-checks

### W1_58 control (M1 side)

W1_58 mean core-fraction across all 32 bits = **0.000** (universal SHELL).

This is structurally consistent: in cascade-1 force mode, W1 is unconstrained
(no cascade-target) so W1_58 bits are all in shell. The asymmetry between
W1_58 and W2_58 is the cascade-1 hardlock signature.

### Top 5 W2_58 bits by core-fraction

| Bit | Core fraction | σ1 fan-in |
|---|---:|---|
| 14 | 1.00 | dense (3) |
| 26 | 1.00 | **light (2)** |
| 1  | 0.90 | dense (3) |
| 5  | 0.90 | dense (3) |
| 6  | 0.90 | dense (3) |

4 of 5 top bits are dense fan-in. Only bit 26 (one of the two F286 anchors)
fits the hypothesis. Bit 14 has full fan-in and is also universal — this is
the ASYMMETRY F287 noted, now confirmed: bit 26 might be light-fan-in
flavored, bit 14 is not.

### W2_58[31] = 0.00 anomaly

W2_58 bit 31 has σ1 fan-in = 2 (light), σ0 fan-in = 2 (light), so the LIGHTEST
input dependency in W[58]. Yet it is **0/10 in core** — universal shell. This
is the strongest counter-example to "light fan-in → core". 

A possible explanation: high-bit positions have NO carry-in from below for
σ1 + σ0 + carry contributions, but DO have carry-in from the LSB chain in
the modular addition (σ1(W56) + W51 + σ0(W43) + W42). At bit 31, the
cumulative carry chain crosses 31 bits, and so the bit value depends on a
LONG CHAIN of lower-bit constraints. That's actually a DENSE constraint
surface, the opposite of what fan-in count alone suggests.

## Refined understanding

The W2_58[14] and W2_58[26] universality is NOT a σ-function fan-in
phenomenon. Possible alternative explanations (per F287):

1. **Tseitin encoding layout in cascade_aux_encoder.py force-mode**: the
   specific clauses pinning W2[58] depend on the encoder's variable
   orderings; bits 14 and 26 might be at "join" positions in the encoder.

2. **σ1 + σ0 + carry compound interaction**: bits where σ0/σ1 contributions
   combine with carries from specific lower-bit positions might be uniquely
   pinned.

3. **Schedule-recurrence aliasing**: W[58] = σ1(W[56]) + W[51] + σ0(W[43]) +
   W[42]. Some bits of W[58] may receive contributions that ALWAYS resolve
   to a fixed value across cands due to the algebraic interaction.

(1) is most testable but requires reading encoder source carefully; deferred.

## What's shipped

- This memo with full per-bit table and hypothesis test result.
- 0 SAT compute (data analysis on existing F269/F270/F272/F283 JSONs).

## Concrete F287 status update

| F287 next probe | Status |
|---|---|
| (a) Read cascade_aux_encoder.py force-mode encoding | Open |
| (b) Test σ1 fan-in vs W2_58 core fraction | **DONE — refuted** (this memo) |
| (c) Algebraic constraint propagation | Open |

## Implication for selector / cube design

Yale's `--stability-mode core` selector with stability-weight uses
W2_58[14] and [26] as anchor bits. F323 confirms these are the two
universal anchors (10/10) at W2_58 but does NOT find a structural rule
to predict additional anchors a priori. The selector should keep using
the empirical 132-bit universal core directly rather than predicted
extensions.

## Cross-bet implication

For block2_wang chamber attractor work: the 132-bit universal hard core
includes W2_58[14] and [26]. If the chamber attractor in atlas-loss
landscape is constrained by these 2 specific bits, then block2_wang's
search must pin them explicitly (rather than letting them drift).

## Discipline

- ~10 min wall (data analysis only).
- One hypothesis tested cleanly with existing data.
- Honest negative reported.
- Closes one of F287's three open probes.
