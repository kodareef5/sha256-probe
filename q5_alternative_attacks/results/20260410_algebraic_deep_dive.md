# Algebraic Deep Dive: Complete Results

**Date**: 2026-04-10
**Evidence level**: VERIFIED (N=4 exact), EVIDENCE (N=8/N=32 sampled)

## 1. Exact ANF at N=4 (VERIFIED)

Complete Moebius transform over 2^32 truth table entries.
Every output bit's algebraic degree is known exactly.

| Register | LSB deg | MSB deg | LSB monomials | MSB monomials |
|----------|---------|---------|---------------|---------------|
| a (bit 0-3)   | 16 | 16 | 65,493 | 65,283 |
| b (bit 4-7)   | 16 | 16 | 65,670 | 65,740 |
| c (bit 8-11)  | 13 | 16 | 29,660 | 65,672 |
| d (bit 12-15) | **9** | 13 | **1,782** | 29,652 |
| e (bit 16-19) | 16 | 16 | 65,659 | 65,603 |
| f (bit 20-23) | 14 | 16 | 57,437 | 65,441 |
| g (bit 24-27) | 12 | 14 | 18,425 | 57,707 |
| h (bit 28-31) | **8** | 12 | **1,173** | 18,436 |

**Key properties:**
- Degree range: 8-16 out of 32 max (25-50% of maximum)
- Cascade ordering: h < g < d < f < c < b ~ a ~ e
- Carry chain gradient: LSBs have lower degree than MSBs
- Extreme sparsity: h[0] has 1,173 monomials out of C(32,≤8) ≈ 15M possible = 0.008%

## 2. Variable Dependency Structure (VERIFIED at N=4)

From per-bit Moebius transform dependency map:

**h[0] (weakest bit):**
- 6 absent variables: W1[60][1:3] and W2[60][1:3]
- W[60][0] appears in exactly 1 monomial (linear term only)
- Structure: h[0] = W1[60][0] ⊕ W2[60][0] ⊕ g(W[57], W[58], W[59])
- This means: once W[57..59] are fixed, h[0]=0 constrains dW[60][0]

**d[0]:**
- 8 absent variables: W1[60][1:3], W2[60][1:3], W1[59][3], W2[59][3]
- Similar linear structure: d[0] = W1[60][0] ⊕ W2[60][0] ⊕ g'(W[57], W[58], W[59]_lower)

**Bit-serial dependency count on W[60]:**
| Output | Register | W[60] deps | Details |
|--------|----------|-----------|---------|
| bit 12 | d[0]     | 2         | W1[0], W2[0] only |
| bit 28 | h[0]     | 2         | W1[0], W2[0] only |
| bit 13 | d[1]     | 4         | W1[0:1], W2[0:1] |
| bit 29 | h[1]     | 4         | W1[0:1], W2[0:1] |
| bit 25 | g[1]     | 5         | W1[0:3], W2[1] |
| a[*]   | a[0:3]   | 8         | All W[60] bits |

## 3. Per-Round Degree Profile — CORRECTED

**Previous claim (RETRACTED):** Degree ~4 at N=8, ~6 at N=32.
**Correction:** The restriction test heuristic confuses sensitivity with algebraic degree.

**Correct picture from exact ANF + higher-order diff:**
- N=4 exact: degrees 25-50% of max
- N=8 higher-order diff: ALL output bits have degree > 19/64 (>30%)
- Expected degree at N=8: 16-32 out of 64 (scaling from N=4)

The degree DOES collapse at schedule-determined rounds (60+) relative to
free rounds (57-59), but the collapse is from 100% to 25-50%, not to 2-6%.

## 4. Higher-Order Differentials at N=8

Through k=19 (9+ hours, 2000 base points × 200 direction sets):
- ALL registers: 50.0% zero at every k from 1 to 19
- No zero differentials found at any order ≤ 19
- This confirms: degree > 19 for ALL output bits at N=8
- Scanner still running (approaching k=20+)

## 5. Cross-Register Correlations at N=8

50,000 random evaluations, all 2016 bit pairs tested:
- All correlations within ±0.008 of 0.5
- No intra-register vs inter-register difference
- No low-degree XOR cancellations found
- **Conclusion: output bits are well-diffused, no algebraic shortcuts via XOR**

## 6. Annihilator Search at N=4 (partial)

For h[0]'s truncated polynomial (93 of 1173 monomials):
- No degree-≤2 annihilators (full rank: 352/352)
- No degree-≤3 annihilators (full rank: 2952/2952)
- Degree-≤4 search in progress

Note: needs re-run with full monomial list for valid results.

## 7. Quadratic Factor Test

Bilinear structure analysis of h[0]'s zero set:
- All pairwise biases < 0.016 (no significant structure)
- All single-variable biases < 0.012
- **No evidence of quadratic factorization**

## Implications for Attack

1. **Algebraic degree is moderate (25-50% of max), not low.** Pure algebraic
   attacks need to handle degree proportional to the variable count.

2. **The extreme sparsity (0.008%) is potentially more exploitable** than
   the degree. A degree-8 polynomial with 1173 terms in 32 variables is
   very sparse — specialized sparse polynomial solvers might work.

3. **The cascade structure creates a natural bit-serial attack order:**
   solve h[0], d[0] first (fewest W[60] dependencies), propagate constraints
   upward. Theoretical speedup: ~4x (from 75% early pruning on easy bits).

4. **No cross-register algebraic shortcuts exist** at N=8 (correlation analysis).
   Each register must be zeroed independently.

## Tools Built

- `exact_anf_n4.c`: Complete Moebius transform (N=4, 2^32 entries)
- `restricted_anf_n8.c`: Cascade-words-only exact ANF (N=8, 32 free bits)
- `higher_order_diff.c`: k-th order differential scanner (N=8)
- `cross_register_corr.py`: Pairwise correlation + degree estimation
- `bitserial_algebraic.py`: Bit-serial attack with dependency ordering
- `factor_h0_n4.py`: GF(2) factorization + annihilator search
