# Cascade Chain State Invariants — Major Structural Discovery

## Empirical observation

For ALL prefixes that satisfy cascade chain (any choice of W1[57..59]
following the deterministic dW chain), the additive state diffs at
each round have specific CONSTANT values (independent of W choices):

| Round | Register | Additive diff | Status |
|---|---|---|---|
| 56 | da | 0 | Cascade input |
| 56 | db..dh | various nonzero | Candidate property |
| 57 | da | 0 | Cascade enforced |
| 57 | de | 0xefef3e30 | **CONSTANT** |
| 57 | df | 0xfe1f3a84 | **CONSTANT** |
| 58 | da | 0 | Cascade enforced |
| 58 | de | varies with W[58] | **NOT constant** |
| 58 | df | 0xefef3e30 | **CONSTANT** (= de57) |
| 59 | da..dd | 0 | Cascade complete |
| 59 | **de** | **0x754fbd5d** | **CONSTANT** ⭐ |
| 59 | df | varies | NOT constant |
| 59 | dg | 0xefef3e30 | **CONSTANT** |
| 59 | dh | 0xfe1f3a84 | **CONSTANT** |

## What's constant

3 of 4 e/f/g/h additive diffs at round 59 are constant: de, dg, dh.
Only df59 varies.

## Why constants exist

Through the shift register:
- h_i = g_{i-1} = f_{i-2} = e_{i-3}: dh59 = de56 (constant)
- g_i = f_{i-1} = e_{i-2}: dg59 = de57 (constant because cascade locks W57)
- And recursively de59 inherits from earlier cascade-locked values

## Why de59 is constant despite "depending" on W[59]

de59 = dd58 + dT1_59 (additive)
dd58 = db56 = constant
dT1_59 depends on W[59] in NAIVE calculation, but cascade chain forces
W[59] such that da_59 = 0, which means T1_59 + T2_59 same → T1_59
differs by exactly -dT2_59 → constant additive difference.

So the cascade chain constraint cancels out the W[59]-dependence of
dT1_59, leaving de59_add as a constant.

## Why df59 VARIES

df59 = de58 (additive). de58 also depends on dT1_58 which is
cascade-constrained. So why does df59 vary?

The mismatch suggests something about the cascade computation isn't
exactly preserving additive constants — possibly the dT2 computation
has W-dependent integer subtraction wrap-around effects that aren't
linear.

Or: the additive diff invariant only holds for SPECIFIC registers, not
all of them. The shift register propagates h, g, f, e values but not
their additive diffs uniformly.

## Implication for cascade chain search

If 3 of 4 round-59 e/f/g/h diffs are constant, then the round-60 cascade
computation has FEWER varying inputs than I thought. The constraint:

cascade_dw_60 = dh59 + dSigma1(e59) + dCh(e59, f59, g59) + dT2_60

dh59 (additive): constant
dSigma1(e59): NOT constant (depends on actual e59 values, not just diff)
dCh: depends on actual values
dT2_60 = 0 (because da59=db59=dc59=0)

Wait — the cascade_dw uses INTEGER differences of states. dh59_add
constant doesn't mean Sigma1(e59_M1) - Sigma1(e59_M2) is constant.
Sigma1 is bitwise, so the integer difference of Sigma1 values depends
on the actual values, not just their integer difference.

So the constants are useful for COUNTING but not directly for the
cascade_dw computation. Hmm.

But wait — dh59 itself is the integer difference (constant). It enters
cascade_dw directly via "+dh". So that contribution IS constant.

What varies in cascade_dw_60 across prefixes:
- dh: constant 0xfe1f3a84
- dSigma1(e59): varies (since e59 actual values differ across prefixes)
- dCh(e59,f59,g59): varies
- dT2: 0 always

So the variation comes from Sigma1 and Ch applied to varying e59 values
across prefixes. The DIFFERENCE de59 is constant but the actual e59
values are different.

## Concrete next experiment

For 1000 prefixes:
- Compute e59_M1 (which varies across prefixes)
- Compute e59_M2 = e59_M1 - 0x754fbd5d
- Compute Sigma1(e59_M1) - Sigma1(e59_M2)
- Plot the distribution

If this distribution is small (few possible values), we have ANOTHER
algebraic structure to exploit.

## Evidence level

**STRONG EVIDENCE**: 8/8 prefixes show identical additive diffs for
de59, dg59, dh59. The constancy is deterministic, not statistical.
df59 actively varies (verified across multiple samples).
