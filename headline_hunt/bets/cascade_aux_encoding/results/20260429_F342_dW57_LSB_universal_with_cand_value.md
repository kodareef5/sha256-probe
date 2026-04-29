---
date: 2026-04-29
bet: cascade_aux_encoding
status: REFINED — dW57[0] is universally single-bit-constrained; forced value is cand-parameterized
---

# F342: dW57[0] universal single-bit UNSAT extends to all 6 tested cands

## Setup

F341 found dW57[0] = 0 UNSAT (so dW57[0] = 1 forced) for cand
m17149975/bit31. F341 hypothesized this is a Class 1a unit-clause
constraint tied to F286's universal LSB anchors W1_57[0] and W2_57[0]
(both 10/10 core fraction).

F342 cross-validates on the 5 other cands tested in F340, plus tests
dW58[0]/dW59[0]/dW60[0] for additional unit constraints.

## Result

```
F342 cross-cand single-bit dW{57,58,59,60}[0] UNSAT test (cadical 5s budget):

bit0 (m8299b36f, fill=0x80000000):
  dW57[0]: =1 UNSAT in 0.01s ← forced=0
  dW58, dW59, dW60: no fast-UNSAT

bit10 (m3304caa0, fill=0x80000000):
  dW57[0]: =1 UNSAT in 0.01s ← forced=0
  others: no fast-UNSAT

bit11 (m45b0a5f6, fill=0x00000000):
  dW57[0]: =0 UNSAT in 0.01s ← forced=1
  others: no fast-UNSAT

bit13 (m4d9f691c, fill=0x55555555):
  dW57[0]: =1 UNSAT in 0.01s ← forced=0
  others: no fast-UNSAT

bit17 (m427c281d, fill=0x80000000):
  dW57[0]: =0 UNSAT in 0.01s ← forced=1
  others: no fast-UNSAT
```

Plus F341 result for completeness:
```
bit31 (m17149975, fill=0xffffffff):
  dW57[0]: =0 UNSAT in 0.02s ← forced=1
```

## Findings

### Finding 1 — dW57[0] is UNIVERSALLY single-bit constrained across all 6 cands

ALL 6 cands have exactly ONE polarity at dW57[0] that triggers cadical
fast UNSAT (0.01-0.02s). The constraint is universal — F286's
universal LSB anchors W1_57[0] and W2_57[0] manifest as a single-bit
unit clause on dW57[0].

### Finding 2 — Forced value is CAND-SPECIFIC

| Cand | M[0] | fill | kernel bit | dW57[0] forced |
|---|---|---|---:|:---:|
| bit0  | 8299b36f | 0x80000000 | 0  | **0** |
| bit10 | 3304caa0 | 0x80000000 | 10 | **0** |
| bit13 | 4d9f691c | 0x55555555 | 13 | **0** |
| bit11 | 45b0a5f6 | 0x00000000 | 11 | **1** |
| bit17 | 427c281d | 0x80000000 | 17 | **1** |
| bit31 | 17149975 | 0xffffffff | 31 | **1** |

The forced value flips between 0 and 1 across cands. NOT determined by
fill bit-31 alone (bit0 fill=0x80000000 → forced 0; bit17 same fill →
forced 1). Determined by some combination of (M[0], fill, kernel-bit).

### Finding 3 — dW58[0], dW59[0], dW60[0] are NOT single-bit-UNSAT-fast

In all 6 cands, dW58[0], dW59[0], dW60[0] showed no fast UNSAT in 5s
of cadical for either polarity. The single-bit constraint is specific
to round 57, not propagating as single-bit unit clauses to later rounds
at this CDCL budget.

This is consistent with F286: the LSB anchors are at W1_57[0] /
W2_57[0], NOT at W*_58[0] / W*_59[0] / W*_60[0]. The single-bit
mechanism is round-57-specific.

### Finding 4 — Algebraic interpretation

For idx=0 with kernel bit b:
- W1[0] = M[0]; W2[0] = M[0] ^ (1 << b)
- W1[9] = M[9]; W2[9] = M[9] ^ (1 << b)
- For b ≠ 0: W1[0..15] LSBs are unchanged → schedule LSBs propagate identically initially
- For b = 0: W1[0] LSB IS perturbed; full schedule LSB chain affected

By round 57 the schedule has compounded through 41 σ-recurrence steps.
The LSB of the differential dW[57] depends on accumulated XOR + carry
behavior from round 0..56 LSBs. The forced value is the algebraic
result of:

  dW[57][0] = LSB(σ1(dW[55]) + dW[50] + σ0(dW[42]) + dW[41] + ε_carry)

where ε_carry is the modular-subtraction carry. The specific forced
value depends on M[0], fill, and kernel bit through the 57-round
schedule expansion.

This is in principle algebraically derivable from cand metadata. For
the propagator, simpler: run a 0.01s cadical preflight on each new
cand to extract the forced dW57[0] value, then inject as unit clause.

## Refined three classes

| Class | Structure | Universality | Polarity |
|---|---|---|---|
| 1a-univ | Single-bit unit at dW57[0] | universal across all 6 cands | cand-parameterized (per F342) |
| 2-univ | 2-bit at W57[22:23] | universal across all 6 cands | fill-bit31-parameterized (per F340) |
| 3 | F286 132-bit hard core | universal | (branching priority, not polarity) |
| 4 | yale F378-F384 mined cores | per-cand | per-cand |

Both Class 1a-univ and Class 2-univ are UNIVERSAL constraint families
with cand-parameterized polarity. They can be pre-loaded by the
propagator per-cand via 0.01-0.1s preflight cadical runs to determine
the polarity, then injected as forced clauses for the full CDCL search.

## Next probes

(a) **dW57 bit-by-bit enumeration on additional cands**: are there
more single-bit constraints at non-LSB positions for some cands?
F341 found ONLY dW57[0] for m17149975/bit31. Cross-cand check on
this is fast (0.02s × 32 bits × 2 polarities × 5 cands = ~6s wall
since UNSAT path is fast).

(b) **Propagator preflight implementation**: a small Python script
that takes a cand spec (sr, M0, fill, kernel-bit) and produces a
JSON of forced unit clauses (Class 1a) and 2-bit clauses (Class 2).
Concrete IPASIR-UP `cb_add_external_clause` input.

(c) **Algebraic derivation of dW57[0] forced value**: derive a
closed-form formula for forced(M0, fill, kernel_bit). Saves the
cadical preflight if the formula is simple.

## What's shipped

- F342 cross-cand cross-round results in this memo.
- Refines F341's hypothesis with broader cross-cand data.

## Discipline

- ~3 min wall (5 cands × 4 rounds × 2 polarities × ~5s).
- 0 long compute.
- Direct cross-cand validation of F341's single-bit class.

## Cross-machine implication

The Phase 2D propagator clause library now has TWO cleanly-validated
universal-with-cand-parameterized-polarity classes:

```
For new cand (sr, M0, fill, kernel_bit):
1. Preflight cadical 0.01s on ¬dW57[0] then dW57[0]:
     → exactly one is UNSAT → unit clause for dW57[0] direction
2. Preflight cadical 0.07s on each of 4 polarity combos at W57[22:23]:
     → exactly one is UNSAT → 2-bit blocking clause
3. Both injected via cb_add_external_clause at solver init.
```

Total preflight cost per cand: ~0.1s. Total clauses injected: 2.
For long-running cadical (hundreds of seconds) on hard sr=61 instances,
this is essentially free preprocessing.
