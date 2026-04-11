# Round-61 Cascade Closure: Two-Level Constraint Structure

## The constraint chain

To extend the cascade chain through round 61 (maintaining da61=0), we need:

```
required_C61(state60) = schedule_dW61(W1[59])
```

Where:
- **required_C61** depends on the state at round 60, which depends on
  W1[60] (and earlier W values via cascade chain)
- **schedule_dW61** depends only on W1[59] (via sigma1) and pre-schedule
  constants

This is TWO constraints:
1. `f(W1[59]) := sigma1(W1[59] + C59) - sigma1(W1[59]) = target_a` (fixes part of LHS)
2. `required_C61(W1[60] | state59) = target_b` (fixes RHS)

Where target_a + sched_const_diff = target_b.

## Empirical sparsity

Tested with cert prefix (W1[57]=0x9ccfa55e, W1[58]=0xd9d64416, W1[59]=0x9e3ffb08):
- schedule_dW61 = 0x7a5ee60e (fixed by W1[59])
- 100,000 random W1[60] values: **0 produce required_C61 = 0x7a5ee60e**
- Cert's W1[60] = 0xb6befe82: produces required_C61 = 0x7a5ee60e ✓

## Implication

For each (W1[57], W1[58], W1[59]) prefix, there's expected ~1 valid W1[60]
that closes the cascade through round 61. We can't find it by random
sampling — we need to INVERT cascade_dw at round 60 to get the W1[60]
that produces a target required_C61.

## How to invert cascade_dw at round 60

cascade_dw(state60) = dh60 + dSigma1(e60) + dCh(e60,f60,g60) + dT2_60

Where state60 components are functions of W1[60] (the new variable):
- e60 = d59 + T1_60(W1[60])
- f60, g60, h60 = (shifted from earlier rounds, FIXED)
- a60, b60, c60 = (computed from T1_60 + T2_60, depend on W1[60])

This depends nonlinearly on W1[60] through T1_60 = h59 + Sigma1(e59) + Ch(...) + W1[60].

## Approach

Given target required_C61, work backward to find W1[60]:

1. e60 needs to satisfy: dSigma1(e60) appears in C61 = dh60 + dSigma1(e60) + dCh + dT2
2. dh60 = dg59 (shift) — known from state59
3. e60 = d59 + h59 + Sigma1(e59) + Ch(...) + K[60] + W1[60] (mod 2^32)
4. So Sigma1(e60) is a function of W1[60]

The constraint reduces to:
- dSigma1(e60(W1[60])) = target_c
- where target_c = required_C61 - dh60 - dCh(e60,f60,g60) - dT2(a60,b60,c60)

But dCh and dT2 also depend on W1[60] indirectly (via a60, b60, c60).

## Key observation

Since this is a fixed-point equation in W1[60] across multiple
nonlinear operations, direct inversion may not be tractable. But we
can iterate or use structural properties.

ALTERNATIVE: Sample (W1[57], W1[58], W1[59]) and for each prefix,
brute-force the 2^32 W1[60] values exhaustively to find any matches.
At 100M evals/sec, that's ~40 seconds per prefix. Then check if those
matches also satisfy round 62 and 63 constraints (each adding 1 more).

This is a tractable but expensive search: 2^96 prefixes × 40s each =
10^31 seconds, infeasible. But maybe with pruning?

## Alternative: solve W1[60] given target

For each (W1[57], W1[58], W1[59]), we have a TARGET required_C61 from
the schedule constraint. Instead of brute forcing W1[60], can we
INVERT the cascade_dw → W1[60] map?

cascade_dw(state60) = sum of state diff transforms
state60 components depend on W1[60] via:
- a60 = T1_60 + T2_60 (T2_60 is fixed since da59=db59=dc59=0)
- e60 = d59 + T1_60 (linear in W1[60])
- T1_60 = (constants) + W1[60]

So a60 and e60 are LINEAR in W1[60] (additive).
But Sigma1(e60), Ch(e60,f60,g60), Sigma0(a60), Maj(a60,b60,c60) are nonlinear.

The constraint is therefore one nonlinear 32-bit equation in W1[60].

## Next steps

1. Build a brute-force W1[60] inverter at N=8 (2^8 search per prefix)
2. Test how often a valid W1[60] exists
3. If always exists, scale to N=16, N=32 with smarter inversion

## Evidence level

**EVIDENCE**: direct empirical measurement on cert prefix. 100K random
W1[60] gives 0 hits, cert's W1[60] gives the unique required value.
The constraint exists, is sparse, and the cert satisfies it.
