---
date: 2026-04-29
bet: cascade_aux_encoding
status: UNIVERSAL_HARDCORE_DECOMPOSED — 132 bits = 128 + 4 specific anchors
---

# F286: universal hard-core decomposes to 128 round-bits + 4 specific anchors

## Setup

F284 found 132 stable_core bits across 10 sr60 cands. F271/F273
attributed 128 to W*_59 + W*_60. F286 identifies the remaining 4
"extra" bits.

## Result

Per-bit universal-core analysis across 10 sr60 cands:

| Word/round | Universal bits (10/10) | Count |
|---|---|---:|
| W1_57 | bit 0 | 1 |
| W1_58 | (none — universal SHELL) | 0 |
| W1_59 | bits 0..31 | 32 |
| W1_60 | bits 0..31 | 32 |
| W2_57 | bit 0 | 1 |
| W2_58 | bits 14, 26 | 2 |
| W2_59 | bits 0..31 | 32 |
| W2_60 | bits 0..31 | 32 |

**Total: 132 universal hard-core bits.**

## Composition

- 128 universal "round bits": W*_59 + W*_60 = full LATER 2 rounds
  for both message instances. Per F271/F273, structural property of
  cascade-1 collision encoding.
- 4 specific anchor bits:
  - **W1_57[0]**: LSB of dW[57] from M1 side
  - **W2_57[0]**: LSB of dW[57] from M2 side
  - **W2_58[14]**: bit 14 of W2's W[58]
  - **W2_58[26]**: bit 26 of W2's W[58]

## Why bit 0 anchors are structural

The LSB of any 32-bit word has NO carry-in from a lower bit. In the
SHA round-equation Tseitin encoding, this makes bit 0 a "clean
anchor" — its value is determined directly by σ/σ rotations + adds
without carry-propagation noise.

For dW[57] = W2[57] ⊕ W1[57], bit 0 is structurally cleaner than
bits 1-31 because:
1. No carry-in from below
2. Σ rotations (7, 18) wrap from upper bits to lower bits, but
   bit 0 specifically has no rotation-shift contribution from
   adjacent bits
3. The cascade-1 hardlock at round 57 propagates most cleanly
   through bit 0 first

## W2_58[14] and W2_58[26] mystery

These two bits are universal-core in W2[58] but the rest of W2[58]
is cand-variable. Why specifically bits 14 and 26?

Possibilities:
1. **Σ1 fixed points**: σ1(x) = ROTR(x, 17) ⊕ ROTR(x, 19) ⊕ SHR(x, 10).
   The bits 14 and 26 might be at "rotation-stable" positions where
   σ1 maps them to themselves under the XOR.
2. **Schedule recurrence interaction**: W[58] = σ1(W[56]) + W[51] +
   σ0(W[43]) + W[42]. Bits 14 and 26 of W[58] might receive
   particularly constrained input combinations.
3. **Encoder accident**: the cascade_aux encoder's specific Tseitin
   layout might force these bits more than others, structurally
   irrelevant.

Worth checking: does (14, 26) have a SHA-rotation relationship?
- 26 - 14 = 12
- 26 ⊕ 14 = 16 (binary: 11010 ⊕ 01110 = 10100)
- 26 + 14 = 40 ≡ 8 mod 32
- ROTR(., 12): bit 14 → bit 14-12 = 2; bit 26 → bit 14
  → bit 26 maps to bit 14 under ROTR-12. Suggestive!

ROTR-12 isn't a SHA-256 rotation amount directly, but it could
emerge from σ0/σ1 compositions:
- σ1's ROTR-17 ⊕ ROTR-19: applied twice = ROTR-(17+17) ⊕ ROTR-(17+19)
  ⊕ ROTR-(19+17) ⊕ ROTR-(19+19) = ROTR-2 ⊕ ROTR-4 ⊕ ROTR-6 ⊕ ROTR-(38 mod 32)=ROTR-6
- That doesn't directly give ROTR-12.

Worth more careful investigation, but for now: noting the empirical
fact that W2_58[14] and W2_58[26] are universal-core anchors is the
finding.

## Updated active-schedule space size

Previous estimate: 128-bit universal hard core + 60-95 cand-variable
bits.

Refined: **132-bit universal hard core** + 88 cand-variable bits
(per F284's exact counts: 132+36+88 = 256).

## Implications

### For yale's cube selector

Yale's `--stability-mode core` selector with F284 stability data
already includes these 4 extra anchors automatically. Yale's
universal-core cube targeting (F321) gets 132 obligate bits, not 128.

### For Phase 2D propagator

The IPASIR-UP propagator's branching priority should target the
132 universal hard-core bits. The cascade-1 hardlock determines
W*_57[0] (LSB anchors) immediately at round 57; the "extra"
W2_58[14] and W2_58[26] are predictable anchors that the propagator
can exploit before search begins.

### For BDD enumeration

A BDD over the 132 universal hard-core bits has 2^132 worst-case
states — too large for direct enumeration. But the 132 bits are
NOT independent: the 128 round-bits and 4 anchors share structural
relationships. A well-ordered BDD might compress the
representation substantially.

## Concrete next probes

(a) **Compute σ1 + σ0 algebraic constraints on bits 14/26 of W[58]**:
    derive the predicate that universally forces these bits.

(b) **Test the 132-vs-128 distinction empirically**: do cube
    experiments targeting just the 4 anchor bits (W1_57[0],
    W2_57[0], W2_58[14], W2_58[26]) show different solver behavior?

(c) **Run F286-style decomposition on sr=61 stability data**:
    do similar "+ N anchor bits" emerge for sr=61 (where the
    universal-core was W*_58 + W*_59)?

## Discipline

- 0 SAT compute (bit-frequency analysis on existing JSONs)
- ~5 min wall
- Data-driven structural finding from 10-cand stability sample

## Cross-bet implication

This refines the F211/F238 BP-decoder design:
- Marginal computation must include W1_57[0], W2_57[0], W2_58[14],
  W2_58[26] in the universal-target set.
- Without these 4 bits, the decoder operates on the 128-bit
  representative subset; with them, on the full 132-bit universal core.

For the F211 decoder's 10⁷ ops estimate, the difference between 128
and 132 bits is negligible computationally but may matter
structurally if the 4 anchors propagate constraints differently.
