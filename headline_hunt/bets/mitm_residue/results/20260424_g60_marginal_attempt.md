# g60 marginal-prediction attempt — partial / negative finding

The closed-form prediction for h60 (de57) and f60 (de59) works because Δ is a candidate constant. For g60 (de58), Δ varies with w1_57, so the prediction must operate on the marginal distribution.

## What was tried

For the MSB candidate: 100,000 random w1_57 samples → compute Δe58 = dd57 − dT2_58 for each.

Result: **69,981 distinct Δe58 values out of 100,000 samples**. The distribution is nearly uniform over a very large support. Top-5 most common Δs each occur 6-7 times — within sampling noise.

## What this rules out

**Mode-based prediction fails.** Picking the most common single Δe58 (e.g., 0x16aca34f at 7/100000 frequency = 0.01%) gives just 2 predicted hard bits via the standard formula, vs the empirical 18-21 g60 hard bits. The mode is unrepresentative of the distribution.

## What the right approach probably is

Each bit i of dg60 (= de58 propagated, hence g60 = R XOR (R - Δ) marginalized over Δ's distribution) has frequency:

```
P(bit i = 1) = E_Δ [ Δ[i] XOR carry_i(R, Δ) ]
            = E_Δ [ P_R(Δ[i] XOR carry = 1) ]
```

For Δ uniform over a "large enough" subset, the bit-i frequency is exactly 0.5 (uniformity) for most i. The "structured" bits at fixed cascade-determined positions are those where Δ's distribution is constrained — likely bits where dT2_58 (= dMaj(a57, b57, c57)) takes only finitely many values for the candidate.

dMaj depends on (a57 ∈ uniform, b57 = constant, c57 = constant). Maj(x, B, C) for fixed B, C and varying x has at most 4 distinct values modulo the 2 input bit positions. So dMaj actually has limited support (probably 2^N possibilities where N is determined by which b57/c57 bits agree).

This is the math to derive: the joint distribution of dMaj(a57, b57, c57) over uniform a57, then propagate into Δe58, then compute the per-bit marginal of (R XOR (R - Δe58)).

Estimated derivation time: ~2 days of focused analysis. Not a 1-hour result.

## Why this matters less than I thought

The g60 contribution to the joint hard-bit count (~18-21 bits) is large. But the algebraic prediction for h60 and f60 already gives ~9 bits in O(1). The remaining ~18 bits in g60 don't drastically change the bet's economics: a forward table over 28-bit signature is ~5-10 GB; over 9-bit signature is ~5KB. Either way, single-candidate MITM is feasible.

The g60 prediction is a polish item, not a blocker.

## Status

Open. No closed-form for g60 yet. Path forward documented above. Bet's main architecture remains: per-candidate forward table at 2^28 entries, h60 + f60 prescreenable in O(1) via predict_hard_bits.py, g60 needs empirical sampling per candidate (200k samples = ~10s of CPU = trivial).
