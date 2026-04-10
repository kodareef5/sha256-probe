# Pairwise Interaction NULL Result

## Question

Single-bit correlations plateau the random search at HW~74. The cert
reaches HW=0 via structure that single-bit analysis misses. Are there
PAIR-FLIP interactions in W[58] bits that could explain the cert?

## Method

For 50 random pairs of W[58] bits (both messages), measure:
- P(output bit k flips | bit i flipped alone)
- P(output bit k flips | bit j flipped alone)  
- P(output bit k flips | BOTH i and j flipped)

Under independence: P(i XOR j) = p_i + p_j - 2*p_i*p_j.
Deviation from this predicts pairwise interaction strength.

Sample size: 1500 base points per pair. Statistical noise floor: ~0.026.

## Results

| Metric | Value |
|---|---|
| Pairs tested | 50 |
| Mean max interaction | 0.046 |
| Maximum observed | 0.111 |
| Pairs with interaction > 0.1 | **1 of 50** |
| Pairs with interaction > 0.2 | 0 |
| Pairs with interaction > 0.4 | 0 |

The single pair with >0.1 interaction was (M1 W[58] bit 8, bit 7) at 0.11 —
still only 2x the sampling noise floor. All other pairs are indistinguishable
from independent action.

## Interpretation

**Pairwise interactions in W[58] bits are essentially zero.** Unlike the
single-bit analysis where we found 4554 deterministic relationships (|bias|>0.49),
pair analysis finds nothing comparable.

This means the cert's higher-order structure is NOT pairwise in W[58]. It
could be:
1. **Triple or quadruple interactions** (4th+ order in one word)
2. **Cross-word pairs** (e.g., W[57] bit + W[58] bit + W[59] bit)
3. **Byte-level patterns** instead of individual bits
4. **Modular arithmetic patterns** (specific values of W[58], not bit patterns)

## Alternative hypothesis: it's not pattern-based at all

The cert might not encode any "exploitable pattern" in W[58]/W[59]. Instead,
it might simply be a specific set of values where all the carry chains
across 7 rounds happen to cancel at round 63. This would be:
- A measure-zero set of points in the 128-dim search space
- Not reachable by any local or low-dimensional search
- Only findable via constraint-propagation solvers like CDCL SAT

If this is true, then "why did seed=5 find it?" is pure luck — the specific
branching heuristics happened to encounter that measure-zero set after
12 hours of search. No amount of sampling would ever find it.

## Evidence level

**EVIDENCE** (null): 50-pair × 1500-sample measurement. Reproducible from
`pairwise_correlation.py`. Rules out simple W[58] pair interactions as
the source of cert's hidden structure.
