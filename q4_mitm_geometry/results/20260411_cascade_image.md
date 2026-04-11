# Cascade DW Image is 2^20 — Massive Information Loss

## Discovery

For the cert prefix, computed the image of `cascade_dw(state60(W1[60]))`
over all 2^32 W1[60] values. Result:

- **1,179,648 = ~2^20.2 distinct values** (0.0275% of 2^32)
- Each value in the image is hit by ~3500 W1[60] values on average
- The cert's target dW61 = 0x7a5ee60e is hit by exactly 8192 (cert family)

## Why this matters

The "round-61 closure" requires sched_dW61 to be IN the cascade_dw image.
For random sched_dW61 values, the probability of being in the image is:

**2^20.2 / 2^32 = 2^-11.8 ≈ 0.028%**

This explains the rarity of round-61-passing prefixes empirically:
- We expected 0.028% × 100 prefixes ≈ 0.03 hits
- We observed: 0 hits in ~100 random prefixes
- Both consistent with structural rarity, not zero

## Why the image is small

cascade_dw_60 = dh60 + dSigma1(e60) + dCh(e60, f60, g60) + dT2_61

where:
- dh60: constant (= dg59, doesn't depend on W1[60])
- dT2_61: constant (= 0, since cascade 1 holds)
- dSigma1(e60): depends on e60, which is a function of W1[60]
- dCh(e60, f60, g60): depends on e60 (varies) and f60, g60 (constants)

So cascade_dw is a function of e60 only (modulo the constants).
e60 = const + W1[60] (linear in W1[60]).

So cascade_dw factors as: `cascade_dw = const + g(e60)` where g is a
nonlinear function of e60.

The image of g (over 2^32 e60 values) is what we measured: 2^20 distinct
values. So **g compresses 12 bits of information** somewhere in its
nonlinear computation.

## Where the 12 bits go

g(e60) = dSigma1(e60) + dCh(e60, f60_const, g60_varies)

Both Sigma1 and Ch are bitwise operations, but their integer differences
introduce carry propagation. The 12-bit compression likely comes from:
- Sigma1's three rotations XOR'ing inputs that overlap
- Ch's MUX behavior with constants on the unchanging registers

## Structural implications

1. **Hash compression**: g is essentially a hash function from 32-bit
   e60 to 20-bit value. We've found a structural compression in the
   middle of SHA-256.

2. **Birthday potential**: If we're searching for sched_dW61 = g(e60)
   matches across multiple prefixes (each with their own g function),
   we have a 20-bit hash birthday problem. Birthday gives O(sqrt(2^20))
   = 2^10 = 1024 prefixes for collision. Combined with the prefix-level
   constraints, this could be efficient.

3. **Image overlap**: do different prefixes have overlapping images?
   If yes, we can search for sched_dW61 values that are in MANY
   prefix images simultaneously.

## Hypothesis

The cert's prefix happens to have its sched_dW61 in cascade_dw's image.
For random prefixes, sched_dW61 is uniform over 2^32, so it's in the
image with probability 2^-12.

Question: are sched_dW61 and cascade_dw's image CORRELATED across
prefixes? I.e., do prefixes that produce certain sched_dW61 values
also produce cascade_dw images that contain those values?

If yes (correlated), we have a structural attack: find prefixes where
the correlation gives a hit.

If no (independent), then 1 in 2^12 prefixes pass round-61 by random
chance, matching the empirical rarity.

## Next experiments

1. **Compute cascade_dw images for 10 prefixes**: are the images
   substantially different, or do they share most values?

2. **Cross-image intersection**: precompute one prefix's image, then
   for a different prefix's sched_dW61, check membership. This is
   a fast filter (O(1) per check after O(image size) setup).

3. **Bit-level structure of the image**: are there fixed bits in
   cascade_dw values (like the family fixed-bit structure)?

## Evidence level

**STRONG EVIDENCE**: Direct enumeration of 2^32 W1[60] values, exact
count of 1,179,648 distinct cascade_dw outputs. The 2^-11.8 image
fraction is exact, not statistical.
