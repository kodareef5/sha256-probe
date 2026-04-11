# UNSAT Core: Bits (4,5) Are the Critical Pair at N=8

**Date**: 2026-04-11
**Evidence level**: VERIFIED (exhaustive test of all 28 pairs)

## Result

At N=8, the sr=61 UNSAT has a precise structure:
- Removing any SINGLE W[60] schedule bit: still UNSAT (all 8 tested)
- Removing any PAIR of bits: still UNSAT (27 of 28 pairs)
- **EXCEPT bits (4,5): SAT in 118s!**

| Pair removed | Result | Time |
|-------------|--------|------|
| (0,1) | UNSAT | 195s |
| (0,2) | UNSAT | 196s |
| ... (21 more UNSAT pairs) ... | | |
| **(4,5)** | **SAT** | **118s** |
| (4,6) | UNSAT | 95s |
| (4,7) | UNSAT | 124s |
| (5,6) | UNSAT | 70s |
| (5,7) | UNSAT | 65s |
| (6,7) | UNSAT | 81s |

## Interpretation

1. **The phase transition K* = N-2 = 6**: enforcing 6 of 8 schedule bits is the
   threshold between SAT and UNSAT (when the right 2 bits are freed).

2. **Bits 4 and 5 are special**: at N=8 with scaled rotations, these positions
   correspond to specific bit positions in the sigma1 output that create the
   critical constraint conflict.

3. **Positional information**: the obstruction IS positional at the pair level.
   Not all 2-bit freedoms are equal — only (4,5) breaks through.

4. **sigma1 connection**: bits 4-5 at N=8 correspond to middle-register positions
   in the sigma1 rotation structure. The sigma1 function at N=8 uses rotations
   {4,5,>>2}. Bits 4 and 5 are exactly at the rotation boundary.

## What This Means

The sr=60/61 boundary at N=8 is controlled by a **2-bit sigma1 constraint**
at positions 4-5. This is the first precise localization of the obstruction.

To test at N=32: the critical pair would be at scaled positions
(4×32/8, 5×32/8) = (16, 20). These are near the sigma1 rotation amounts
(17, 19, >>10).

## Next Steps

1. Verify at N=10, N=12, N=16 to see if the critical pair scales predictably
2. At N=32: test specific pairs near positions 16-20
3. Analyze WHY bits 4-5 create the irreconcilable constraint
