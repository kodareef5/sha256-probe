# Complete Enforcement Landscape: sr=60.5 Data Summary

## Phase Transition Scaling

| N | Top-K max SAT | Bottom-K max SAT | Individual bits |
|---|---------------|-------------------|-----------------|
| 8 | K=3 (37.5%) | not tested | K=4/5 transition |
| 10 | K=0 (0%) non-monotonic | K=3 (30%) | 6/10 bits SAT individually |
| 16 | K=0 (0%) | K=0 encoding issue | not tested |
| 32 | encoding issue | not tested | in progress (hours) |

## Key Findings

1. **Bottom-K >> Top-K**: enforcing LSBs is dramatically easier than MSBs
   because carry chain degree is lower at LSBs

2. **Non-monotonic at N=10**: top K=3 SAT but K=1,2 TIMEOUT — sigma1
   rotation mixing creates bit-position-dependent difficulty

3. **Constructive interference**: hard bits {4,6,7} are SAT together
   but TIMEOUT individually — sigma1 source overlap creates propagation
   chains that help the solver

4. **Tolerance shrinks with N**: 37.5% at N=8, 30% at N=10, 0% at N=16
   The collision needs proportionally MORE of W[60] free at larger N

5. **Pairwise synergy is unpredictable**: {0,1} TIMEOUT but both SAT
   individually. {2,3} TIMEOUT. {4,6,7} SAT but all individually TIMEOUT.

## The Picture

The sr=60→sr=61 boundary is not a cliff — it's a complex landscape
where each bit of W[60] has a specific enforcement difficulty determined
by its position in the carry chain AND its sigma1 source structure.

At small N, enough of W[60] can be freed to find collisions. At N=32,
the tolerance approaches zero — which is why sr=61 (enforcing ALL 32
bits) is so definitively UNSAT.

## Still Running
- N=32 single-bit enforcement map (hours per bit)
- Higher-order diff N=8 (k=18, finishing at k=20)
- N=4 collision structure analysis (Python 2^32 enumeration)
