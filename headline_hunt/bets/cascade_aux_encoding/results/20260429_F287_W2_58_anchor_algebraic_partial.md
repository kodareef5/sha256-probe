---
date: 2026-04-29
bet: cascade_aux_encoding
status: PARTIAL_ALGEBRAIC_INVESTIGATION
---

# F287: Algebraic investigation of W2_58[14] and W2_58[26] anchors

## Setup

F286 found 4 specific universal-core anchors beyond the 128-bit
round-block: W1_57[0], W2_57[0], W2_58[14], W2_58[26]. The first
two (LSB anchors) are explained structurally (no carry-in). F287
investigates W2_58[14] and W2_58[26] algebraically.

## σ-function fan-in analysis

### σ1(x) = ROTR(x,17) ⊕ ROTR(x,19) ⊕ SHR(x,10)

Output bit p depends on input bits (p+17)%32, (p+19)%32, and
(p+10) if p+10<32.

**σ1 OUT bits 22-31 have ONLY 2-bit fan-in** (SHR-10 truncates):

```
σ1(x)[22] = x[7] ⊕ x[9]
σ1(x)[23] = x[8] ⊕ x[10]
σ1(x)[24] = x[9] ⊕ x[11]
σ1(x)[25] = x[10] ⊕ x[12]
σ1(x)[26] = x[11] ⊕ x[13]
σ1(x)[27] = x[12] ⊕ x[14]
σ1(x)[28] = x[13] ⊕ x[15]
σ1(x)[29] = x[14] ⊕ x[16]
σ1(x)[30] = x[15] ⊕ x[17]
σ1(x)[31] = x[16] ⊕ x[18]
```

These 10 output bits are "structurally light" — only 2 input bits
each. The cascade-1 hardlock could propagate cleanly through them.

### σ1 bit 14 vs bit 26

| Bit | σ1 fan-in | Inputs |
|---|---:|---|
| **σ1(x)[14]** | 3 | x[31] ⊕ x[1] ⊕ x[24] |
| **σ1(x)[26]** | 2 | x[11] ⊕ x[13] |

Bit 26 has minimum fan-in (2 bits). Bit 14 has full fan-in (3 bits).

### σ0 fan-in analysis

```
σ0(x)[14] = x[21] ⊕ x[0] ⊕ x[17]    (3 bits, includes LSB x[0])
σ0(x)[26] = x[1]  ⊕ x[12] ⊕ x[29]   (3 bits)
```

σ0 OUT bits 29, 30, 31 have 2-bit fan-in (only those three). Bit 14
and bit 26 are full-fanin in σ0.

## Schedule recurrence at W[58]

`W[58] = σ1(W[56]) + W[51] + σ0(W[43]) + W[42]` plus carries.

Bit 14 of W[58]:
- σ1(W[56])[14] = W[56][31] ⊕ W[56][1] ⊕ W[56][24]
- W[51][14]
- σ0(W[43])[14] = W[43][21] ⊕ W[43][0] ⊕ W[43][17]
- W[42][14]
- + carry from bits 0-13

**Bit 14 of W[58] depends on 8+ input bits** spanning W[56], W[51],
W[43], W[42], plus carry chain.

Bit 26 of W[58]:
- σ1(W[56])[26] = W[56][11] ⊕ W[56][13]
- W[51][26]
- σ0(W[43])[26] = W[43][1] ⊕ W[43][12] ⊕ W[43][29]
- W[42][26]
- + carry from bits 0-25

**Bit 26 of W[58] depends on 7+ input bits** spanning the same
source words plus a longer carry chain.

## Partial conclusion

The two anchors W2_58[14] and W2_58[26] don't share a SINGLE
explanatory property:
- Bit 26's σ1 component has minimum fan-in (2 bits) — structurally
  light, possibly easier to constrain to a fixed value via cascade-1
  hardlock.
- Bit 14's σ1 component has full fan-in (3 bits). No fan-in advantage.

But both bits ARE empirically universal-core across 10 sr60 cands.

## Hypothesis

The universal-anchoring of W2_58[14] and [26] may emerge from the
specific TSEITIN ENCODING of the cascade-1 hardlock + the round-58
round-equation interaction, not from σ-function fan-in alone.

A complete derivation requires:
1. Reading cascade_aux_encoder.py's force-mode Tseitin layout.
2. Tracing which clause groups in the encoded CNF specifically pin
   W2[58] bits.
3. Identifying why bits 14 and 26 are pinned across all cands but
   other W2[58] bits aren't.

This is multi-hour-investigation work, deferred to future session.

## What F287 partially establishes

- σ1 fan-in count is NOT the single explanatory property
  (bit 26 fits, bit 14 doesn't).
- Both anchor bits have dense dependencies in the schedule
  recurrence (7-8 input bits each).
- The W2_58[14]/[26] universality is encoder-specific, not pure
  SHA-arithmetic-structural.

## Reverse direction: which σ1 OUT bits would be EASIEST to constrain?

If we wanted to predict universal-core anchors a priori:
- σ1 OUT bits 22-31 (2-bit fan-in) are structurally light.
- σ1 OUT bits 0-21 (3-bit fan-in) are denser.
- Bit 26 fits (light); but bits 22, 23, 24, 25, 27-31 don't appear
  in F286's universal-core list. So fan-in alone doesn't predict.

Other combinations (σ0 + σ1 fan-in product, dW differential
constraints, etc.) might give better predictions but require
more analysis.

## Concrete next probes

(a) **Read cascade_aux_encoder.py force-mode encoding** to map
    which bits of W2[58] receive Tseitin clauses pinning them.

(b) **Test the prediction empirically**: do σ1 OUT bits 22-31 have
    higher mean-core-fraction than σ1 OUT bits 0-21 across the 10
    sr60 cands?

(c) **Algebraic constraint propagation**: compute which bits of
    W2[58] are forced by a fixed W1 (pin everything else and check
    SAT propagation).

## Discipline

- 0 SAT compute (Python algebra computation)
- ~5 min wall
- Partial finding shipped; complete derivation deferred

## Status

F287 partially answers user's "algebraic prediction of hard-bit
positions" suggestion. Bit 26's σ1 minimum fan-in is a real
structural fact; bit 14 needs deeper investigation (encoder source
or constraint propagation).
