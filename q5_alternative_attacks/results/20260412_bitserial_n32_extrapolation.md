# Bitserial Collision Finder: N=32 Feasibility Analysis

## N=8 Bitserial Width Profile (macbook data)

| Bit | Survival | Width | Phase |
|-----|----------|-------|-------|
| 0-3 | ~3% each | 0.1-0.5 | STRONG pruning (carry chains short) |
| 4-7 | ~50% each | 0.4-260 | WEAK pruning (carry chains long) |

## Extrapolation to N=32

### Uniform model (11% per bit)
Total work: sum(2^{128-3.18k}) ≈ 2^128 (no speedup — first term dominates)

### Two-phase model (from N=8 pattern)
- Bits 0-9: ~3% survival each → 2^128 × 0.03^10 ≈ 2^{93}
- Bits 10-31: ~50% survival each → 2^{93} × 0.5^22 ≈ 2^{71}
- Total work: ~2^{93} (dominated by early bits)
- **Speedup over brute force: 2^{35} = 34 billion x**

### Optimistic model (from carry-diff invariants)
- 147/343 invariant at N=8 = 43% invariant
- At N=32: ~35% invariant (extrapolation) = ~480 invariant of ~1370
- Effective pruning per bit from invariants: ~15 invariants/bit
- If each prunes 50%: 2^{-15} per bit at bits 0-3 = 2^{-60} after 4 bits
- 2^128 × 2^{-60} = 2^{68} after 4 bits. Then 28 more bits at 50%: 2^{40}
- Total: ~2^{68}. **Speedup: 2^{60} = 10^18**

## What's needed to validate

1. N=12 bitserial width profile (macbook can compute once N=12 collisions known)
2. N=16 or N=20 partial bitserial data (would establish the two-phase pattern)
3. Carry-diff invariant count at N=12 (we can compute from our N=12 data)

## Bottom line

The bitserial approach is NOT polynomial-time at N=32 (still exponential
in the worst case). But it provides a potentially massive constant-factor
speedup (2^35 to 2^60) by pruning early bits aggressively.

Whether this makes N=32 TRACTABLE depends on the exact early-bit pruning
rates, which we need N=12+ bitserial data to estimate.

Evidence level: EXTRAPOLATION (from N=8 data + scaling assumptions)
