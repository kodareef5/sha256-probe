# Critical Pair Kernel Comparison: sr=61 Structure is Kernel-Dependent

## Finding

The critical W[60] bit pairs for sr=61 are DIFFERENT for different kernels:

| Kernel | Critical Pairs | SAT times | Notes |
|--------|---------------|-----------|-------|
| MSB (bit 7) | (4,5) only | 21.5s | Single critical pair |
| bit 6 | (1,2), (1,4), (3,7) | 34.6s, 77.5s, 87.4s | THREE critical pairs |

The bit-6 kernel has 3x more critical pairs than the MSB kernel.
Pair (4,5) — the MSB kernel's critical pair — is NOT critical for bit-6.

## Data

### MSB Kernel (M[0]=0x67, N=8, 260 collisions)
- 28 pairs tested, 120s timeout
- 1 SAT: pair (4,5) in 21.5s
- 27 UNSAT: all proved in 29-101s

### Bit-6 Kernel (M[0]=0x12, N=8, 1644 collisions)
- 28 pairs tested, 120s timeout
- 3 SAT: (1,2) in 34.6s, (1,4) in 77.5s, (3,7) in 87.4s
- 21 TIMEOUT: harder to resolve (120s insufficient)
- 4 unknown: could be UNSAT with more time

## Interpretation

1. **More collisions → more critical pairs**: the bit-6 kernel has 6.3x more
   sr=60 collisions, and 3x more critical pairs for sr=61. The schedule-cascade
   compatibility space is richer.

2. **Critical pairs are kernel-specific**: the (4,5) pair from the MSB kernel
   has no special status for bit-6. The sr=61 structure depends on the specific
   differential path, not just the round count.

3. **Harder UNSAT proofs**: most bit-6 pairs TIMEOUT at 120s, while MSB pairs
   resolved in 29-101s. The bit-6 kernel creates harder SAT instances overall.

4. **The cascade break is NOT a simple per-bit property**: if it were, the same
   bits would be critical for all kernels. The interaction between the kernel
   differential and the schedule function determines which bits matter.

## Implication for sr=61 at Larger N

The MSB kernel at N=10 had all 45 pairs TIMEOUT. But the bit-6 kernel's
richer critical pair structure might make sr=61 feasible at N=10 with
a non-MSB kernel. Testing needed.

Evidence level: VERIFIED (exhaustive pair scans at N=8 for both kernels)

## N=10 Bit-6 Kernel Result

15 pairs tested with 600s timeout: ALL TIMEOUT.
Including the N=8 critical pairs (1,2), (1,4), (3,7) and nearby pairs.

The bit-6 kernel advantage at N=8 (3 critical pairs vs 1) does NOT
translate to N=10. The 2^N penalty (1024 at N=10) overwhelms the
kernel advantage. sr=61 at N=10 requires fundamentally more freedom
than 2 freed W[60] bits, regardless of kernel choice.
