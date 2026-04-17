# BDD Completion Quotient: Bounded Width = #Collisions

**Date**: 2026-04-17
**Evidence level**: VERIFIED (N=8, 260 collisions)

## Discovery

The future-completion quotient width of the collision BDD is bounded by
the number of collisions at every prefix depth. It forms a perfect bell curve:

```
Depth  Width   VarName
  0       1    W57[0]
  1       2    W58[0]
  2       4    W59[0]
  3       8    W60[0]      ← doubling (2^depth)
  4      16    W57[1]
  5      32    W58[1]
  6      61    W59[1]      ← growth slows
  7     105    W60[1]
 ...
 14    255    W60[3]      ← PEAK (≈ #collisions = 260)
 ...
 28      17    W57[7]
 29       9    W58[7]
 30       5    W59[7]
 31       3    W60[7]      ← shrinks back
 32       2    (terminal)
```

**Peak quotient width: 255 ≈ #collisions (260)**

## What This Means

The BDD's completion quotient counts the number of distinct "futures"
at each prefix depth. The fact that it peaks at ~260 and never exceeds
the collision count means:

1. **A constructive automaton with ~260 states EXISTS for N=8**
2. The automaton processes bits LSB→MSB, maintaining at most 260 states
3. At the peak (middle of the word), each collision has a nearly-unique
   residual future
4. The carry automaton's permutation property (width = #collisions) is
   EXACTLY the completion quotient width

## Connection to Prior Results

This directly explains:
- **Carry entropy theorem**: each collision has unique carry state = unique BDD residual
- **Cascade tree linearity**: branching ≈1 because quotient width ≈ collision count
- **BDD polynomial scaling**: O(N^4.8) nodes because quotient width ≈ 2^N

## The Key Question (GPT-5.4's Build 3)

If we can build a DP solver that tracks these ~260 quotient states, we get
an O(2^N × poly(N)) collision finder instead of O(2^{4N}). At N=32 that's
2^32 ≈ 4B states — feasible with careful engineering.

BUT: the quotient states are BDD residual nodes, which are defined by the
collision function itself. Constructing them without first knowing the
collisions is the chicken-and-egg problem.

The chunk-mode DP approach (GPT-5.4 Build 3) attempts to construct these
states incrementally using mode variables + GF(2) closure + quotienting.

## Scaling Question

Need to verify: does peak quotient width = #collisions hold at N=10 and N=12?
If yes, the constructive automaton width grows as 2^N (polynomial for fixed N,
exponential in N but much better than 2^{4N}).

## Data

Full width profile at N=8 (260 collisions):
depths 0-31: 1,2,4,8,16,32,61,105,156,190,218,235,247,250,255,254,
253,253,251,250,244,237,222,206,159,108,64,35,17,9,5,3

Terminal: 2 (TRUE and FALSE)

## N=12 Confirmation (3671 collisions)

Peak quotient width: **3640** at depths 24-25 (ratio 0.992).
First 9 depths are EXACT powers of 2: 1,2,4,8,16,32,64,128,256,512.
92,975 BDD nodes, satcount matches.

Full profile:
1→2→4→8→16→32→64→128→256→512→998→1698→2411→2942→3240→3437→
3526→3571→3603→3616→3632→3637→3639→3639→3640→3640→3640→3637→
3635→3631→3613→3591→3543→3435→3270→2971→2418→1694→1004→521→
259→131→67→35→19→11→7→4→2

## Scaling Law (3 data points)

| N  | #Collisions | Peak Quotient | Ratio | First exact 2^k depths |
|----|-------------|---------------|-------|----------------------|
| 8  | 260         | 255           | 0.98  | 6 (up to 32)         |
| 10 | 946         | 925           | 0.98  | 8 (up to 128)        |
| 12 | 3671        | 3640          | 0.99  | 9 (up to 512)        |

The number of exact-power-of-2 initial depths grows with N:
approximately 2N/3 depths before saturation begins.
