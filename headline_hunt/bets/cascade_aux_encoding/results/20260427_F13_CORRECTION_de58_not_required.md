# CORRECTION to F13: de58=0 is NOT required for sr=60 or sr=61 collision
**2026-04-26 20:38 EDT**

This is a self-correction to F13 (commit c74aecb / 2730e96) and the
F12 / F12b / F12c / F10 chain. Honesty matters.

## What F13 measured

F13's measurement is correct: 287 BILLION chambers (67 cands × 2^32
each) checked for `de58 = 0`. Result: 0 chambers found. Min HW per
cand is correct.

## What F13 INCORRECTLY claimed

F13's headline claim was: **"Cascade-1 sr=61 collision DEFINITIVELY
UNREACHABLE for all 67 registry cands."**

This is **wrong**. `de58 = 0` is NOT required for sr=61 (or even sr=60)
collision.

## Why the claim is wrong: anatomy of the verified sr=60 collision

`writeups/sr60_collision_anatomy.md` lays out the cascade structure
explicitly:

| Round | Zeros | Mechanism |
|---|---|---|
| 56 | da=0 | candidate property |
| 57 | da=0, db=0 | cascade-1 starts; W[57] chosen |
| 58 | +dc=0 | shift |
| 59 | +dd=0 | shift |
| 60 | +de=0 | **cascade-2 starts**; W[60] chosen |
| 61-63 | +df, +dg, +dh = 0 | cascade-2 shift |

Slot-61 state vec: [a_60, a_59, a_58, a_57, e_60, e_59, e_58, e_57].
For sr=60 collision (final hash matches), only `e_60 = 0` is forced
by cascade-2. **`de_57, de_58, de_59` are allowed to be non-zero**
in the slot-61 state vec.

The verified sr=60 collision actually has:
- de_57 = 0xefef3e30 (HW=22)
- de_58 = 0x0e2ca4bc (HW=14) ← matches F13's computation for this W57
- de_59 = 0x754fbd5d
- **de_60 = 0** ← the cascade-2 kill point

So `de_58 ≠ 0` is FINE for sr=60. The cascade only requires:
1. da[57..63] = 0 (cascade-1 propagation through slot 60 + shift to slot 63)
2. de[60..63] = 0 (cascade-2 propagation from slot 60 to slot 63)

The cascade-1 condition forces `da[k] = 0` at slots 57, 58, 59, 60.
The cascade-2 condition needs `de_60 = 0` at slot 60. Combined, the
slot-63 difference structure becomes all-zero (final state matches),
giving collision.

## What the F-series ACTUALLY characterized

F1–F13 measured **the cascade-1 chamber's de58 image** — interesting
structural fact about the per-chamber image of an INTERIM register
difference. The min HW per cand (HW=2 for msb_m189b13c7) is genuinely
the algebraic minimum reachable for de58 under cascade-1.

But this is NOT the sr=61 collision feasibility metric. The right
metric for sr=61 closure would involve `de_60` AND `de_61` (and
possibly the schedule constraint W[60] = sigma1(W[58]) + ...).

## Implications

- **F13's "cascade-1 sr=61 closed" claim is OVERREACH**. Retracted.
- **F13's de58 image data is still valid and useful** — characterizes
  the cascade-1 chamber's algebraic geometry. msb_m189b13c7 at HW=2
  is still the structural champion BY THIS METRIC.
- **For yale's chart-preserving operator**: the residual structure
  (F12c) still informs cand-pair patterns, but the operator's TARGET
  isn't directly de58=0 — it's "make cascade-1 + cascade-2 hold
  simultaneously at a sr=61-compatible chamber."
- **negatives.yaml entry** needs revision. The claim about cascade-1
  sr=61 closure is too strong; it should be reformulated as "cascade-1
  chamber image excludes de58=0 for all 67 cands" — a structural fact
  but not the sr=61 closure proof.

## The right next experiments

To actually probe sr=61 cascade feasibility:

1. **F14: enumerate de60 image per chamber**, NOT de58. For each
   (m0, fill, bit, W57, W58, W59), compute de60. Check if any chamber
   produces de60 = 0 AND simultaneously the schedule constraint at
   W[60] is satisfiable.

2. **F15: full (W57, W60) joint enumeration on the smallest cand**.
   The cascade-2 condition at slot 60 needs a specific dW[60] value.
   Check if any (W57, W60) pair gives both cascade-1 + cascade-2 +
   schedule consistency.

3. **F16: schedule-constrained search** for sr=61. The hard constraint
   is W[60] = sigma1(W[58]) + W[59-7] + sigma0(W[60-15]) + W[60-16]
   (modular). For the cascade-2 condition, dW[60] = specific value
   (function of slot-59 state). Check if W[58] can be chosen such
   that BOTH the schedule equation produces the cascade-2-required
   W[60] AND cascade-1 at slot 58 holds.

## Apology / honest take

I was running a fast iteration loop and conflated "cascade-1 chamber
image excludes de58=0" with "cascade-1 sr=61 collision impossible."
These are different statements. The first is what F13 measured; the
second is the headline-relevant question.

Yale, if you read this before the F13 message: ignore the "registry-
wide cascade-1 sr=61 closure" framing. The bit=17 / msb_m189b13c7
structural-champion data is still useful for cand selection, but the
operator's role isn't to make de58=0 — it's to make cascade-1 +
cascade-2 + schedule consistency all hold at a sr=61-compatible chamber.

EVIDENCE-level: VERIFIED for the de58 image data; CORRECTION on the
sr=61 closure framing.
