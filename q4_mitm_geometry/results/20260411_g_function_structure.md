# g(e) Function Structure: 12-bit Compression Decomposed

## The g function

g(e) := Ch(e, f60_M1, g60_M1) - Ch(e, f60_M2, g60_M2)

Where for cert prefix:
- f60_M1 = 0x04d3f862, f60_M2 = 0x8f843b05 (XOR diff: 0x8b57c367, hw=18)
- g60_M1 = 0xcffab9f4, g60_M2 = 0xc1ce1538 (XOR diff: 0x0e34accc, hw=14)

g is the "varying part" of cascade_dw at round 60. The constant part
(dh60 + dT2_61) only translates the image, not its structure.

## Image structure (cert prefix)

| Property | Value |
|---|---|
| Total distinct g(e) values | 1,179,648 = 2^20.2 |
| Image fraction | 0.0275% of 2^32 |
| Information loss | ~12 bits |
| Always-1 bits | 2 (positions 18, 19) |
| Always-0 bits | 2 (positions 20, 23) |

So 4 bits are hard-fixed. The other 8 bits of compression come from
NON-INJECTIVITY in the variable bits.

## Low 24-bit subset

Tested: how many distinct values does g(e) take when projected to
its low 24 bits?

**Result: 49,152 = 3 × 2^14 distinct low-24-bit values**

That's 2^15.6 of 2^24 = 0.29% — even MORE concentrated than the full
image's 0.0275%.

## Average preimage size

- Full image: 2^32 / 2^20.2 = 2^11.8 ≈ 3640 preimages per value
- Low 24 bits: 2^32 / 49152 ≈ 87381 e values per low-24 bucket
- Each low-24 bucket contains ~87381 / 3640 = 24 distinct full g values

So each low-24-bit value corresponds to ~24 distinct upper-8-bit
extensions in the image.

## Why 49152 = 3 × 2^14?

3 × 2^14 is unusual — not a power of 2. This suggests the image is
NOT a linear subspace (which would give 2^k cardinality), but has
some additive/affine structure with a multiplicative factor of 3.

Possibilities:
1. **3-element symmetry**: g's image has a Z/3 symmetry somewhere
2. **2-of-3 majority**: like a partial sum that takes 3 distinct values
3. **Sigma1/Ch interaction**: the rotation count 17 might create the 3

This is the kind of algebraic peculiarity that hints at exploitable
structure. Need to look at specific values.

## Where the 12-bit compression comes from

Total info loss: 12 bits (from 32 → 20)
- 4 bits: hard-fixed (forced 0 or 1)
- 8 bits: variable but correlated (multiple e map to same g)

The 8 bits of correlation are spread across the bit positions. Need
deeper analysis (e.g., XOR-rank of g over many e values) to find
the exact linear subspace structure.

## What this means

cascade_dw is fundamentally a **2^20-element hash function** at round 60.
Round-61 closure requires sched_dW61 to be in this 2^20 set.

If we can characterize the 2^20 set ALGEBRAICALLY (not just by
enumeration), we have a precomputable filter that bypasses the
expensive prefix sweep.

The 4 fixed bits give us a 16x filter for free. The 8-bit correlation
structure could give another 256x if we find it.

Combined: a 4096x speedup over brute force enumeration would make
the search ~250x more efficient than current.

## Evidence level

**STRONG EVIDENCE**: Direct exhaustive computation. The 49152 low-24
buckets, 1.18M total distinct values, and 4 fixed bits are exact.
Reproducible from `cascade_image.c` and `g_func2.c`.

## Next experiments

1. Compute the low-16 subset: how many distinct low-16 values?
2. Look for a generating set for the low-24 subset
3. Test if the 49152 = 3 × 2^14 structure factors into a 3-symmetry
4. Compute the AND/OR mask of the low-16 image
