---
date: 2026-04-29
bet: cascade_aux_encoding
status: SHARPENED — σ-function fan-in correlates NEGATIVELY with core fraction
---

# F332: σ0 fan-in test on W2_58 inverts the F287 intuition

## Setup

F323 tested σ1 fan-in (bits 22-31 light, 0-21 dense) on W2_58 core fraction
across 10 sr60 cands and found a slight NEGATIVE difference (-0.029 light
vs dense). F332 extends to σ0 fan-in:

- σ0(x)[b] = x[(b+7)%32] ⊕ x[(b+18)%32] ⊕ x[b+3 if b+3<32 else absent]
- σ0 fan-in is 2 for bits 29-31 (SHR-3 truncates), 3 for bits 0-28.

## Result

```
σ0 light bits 29-31 (fan-in=2): mean core fraction = 0.433
σ0 dense bits  0-28 (fan-in=3): mean core fraction = 0.783
diff (light - dense): -0.349
```

**Light σ0 bits have core fraction 0.433 vs dense 0.783** — a 35% NEGATIVE
correlation. Light fan-in correlates with LOWER core fraction, not higher.

## Compound σ0 + σ1 partition

The 32 bits of W2_58 partition into three zones based on which σ functions
have light fan-in at that output bit:

| Zone | Bits | n | σ0 fan-in | σ1 fan-in | Mean core fraction |
|---|---|---:|---|---|---:|
| Both light | 29-31 | 3 | 2 | 2 | **0.433** ← lowest |
| σ1 light only | 22-28 | 7 | 3 | 2 | **0.857** ← highest |
| Both dense | 0-21 | 22 | 3 | 3 | 0.759 |

**The σ1-light-only zone (bits 22-28) is the most-core region.** F286's
universal anchor at bit 26 sits in this zone.

## Per-bit anomaly: bit 31 is universally SHELL

```
b30: core_frac = 0.40
b31: core_frac = 0.00  ← 0/10 cands across the entire dataset
```

Bit 31 is the LIGHTEST in fan-in (σ0 + σ1 both 2-input) AND has no
carry-out (modular addition saturates at bit 31). By the F287 intuition,
this should be MOST core. Instead it's LEAST core — universally shell.

## What's actually going on

Reframing the F287 intuition:

The original F287 hypothesis was: "lighter fan-in = easier for CDCL to
constrain via cascade-1 hardlock = more often core". F323 refuted this
mildly for σ1; F332 refutes it strongly for σ0.

**A coherent reframe**: high-bit positions in σ functions don't receive
carries from below in modular addition, but they also don't propagate
carries forward. So they have FEWER coupling constraints from the
cascade-1 hardlock — they're STRUCTURALLY ISOLATED, making them
harder for CDCL to derive. Hence MORE shell, not more core.

The "active" zone in cascade-1 collisions is the MID-BIT range (22-28)
where σ functions still have light fan-in but where carry chains both
in and out of the bit position couple to neighboring bits. CDCL
conflict analysis derives those bits because they participate in the
cascade-offset modular constraint chain.

## Updated F286 anchor explanation (preliminary)

W2_58[14] (universal): σ0 dense, σ1 dense — sits in the ALL-DENSE zone.
Likely an anchor due to specific carry-chain interaction at low bit.

W2_58[26] (universal): σ0 dense, σ1 light — sits in the HIGHEST-MEAN zone.
The σ1-light-only zone is structurally the most "core-ready", and 26 is
the most-core bit in that zone.

But neither the all-dense nor σ1-light-only zone has a SIMPLE single-bit
explanatory rule. The anchor positions are determined by carry-chain
algebraic interactions that single-property analyses can't predict.

## What's shipped

- F332 σ0 + compound test results in this memo.
- Combined with F323 (σ1 alone) and F324-F326 (UP test): the F286
  universal-core anchor mystery still has no simple structural rule, BUT:
  - σ-function fan-in correlates NEGATIVELY (not positively) with core fraction
  - High-bit isolation explains why bit 31 is universally shell
  - Mid-bit (σ1-light-only) zone has highest mean core fraction

## F287 status table (final final)

| F287 next probe | Status |
|---|---|
| (a) Read encoder force-mode encoding | F324+F325+F326 ANSWERED |
| (b) σ1 fan-in vs core fraction | F323 REFUTED (slight negative correlation) |
| (b') σ0 fan-in vs core fraction | F332 REFUTED MORE STRONGLY (-0.349) |
| (c) Algebraic constraint propagation | F324+F325 PARTIAL — UP-up-to-2-bits insufficient |

## Discipline

- ~2 min wall (analysis on existing F269/F270/F272/F283 JSONs).
- Sharpens F323 with the σ0 direction.
- 0 SAT compute.

## Takeaway

The simple-fan-in hypothesis was wrong in BOTH directions. The 132-bit
universal hard core's specific bit positions (14, 26 anchors and
W*_59/W*_60 round bits) are determined by CDCL conflict analysis on the
cascade-1 modular-arithmetic constraint, not by σ-function fan-in or
encoder Tseitin layout. This is consistent with F324-F326's "search-
invariant" thesis.
