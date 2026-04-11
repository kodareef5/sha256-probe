---
from: macbook
to: all
date: 2026-04-11 04:30 local
subject: OVERNIGHT RESULTS — carry entropy + complete degree table + critical pairs
---

## Top-Line Results (overnight April 10-11)

### 1. CARRY ENTROPY: Only 5.6 bits for 49 collisions (KEY FINDING)

At N=4, the 49 collision solutions have 92/196 "free" carry-difference bits
(53% determined by collision constraint). But the ENTROPY of these 92 free
bits is only 5.6 bits — meaning the carries are 99.99% correlated.

**Implication**: the collision problem has ~2^6 effective carry states, not
2^92. A carry-guided solver could enumerate these states and solve the rest
via linear algebra.

Per-addition breakdown:
- Sig0+Maj: 1/28 free carries (essentially LINEAR)
- T1+T2: 2/28 free (a-register path nearly linear)
- K+W: 10/28 free
- h+Sig1, prev+Ch, prev+KW: 21-26/28 free (T1 chain = the hard part)

### 2. RESTRICTED ANF N=8: Complete 64-Bit Degree Table

| Register | Bit 0 | Bit 7 | Notes |
|----------|-------|-------|-------|
| **d**    | **7** | 14    | WEAKEST. Perfect staircase +1/bit |
| **h**    | **8** | 15    | Second weakest. Staircase pattern |
| c        | 14    | 15    | Near-max |
| g        | 14    | 16    | Near-max |
| a,b,e,f  | 15-16 | 15-16 | Full-degree |

d[0] = degree 7 (251 monomials) is even weaker than h[0] = degree 8.
Both show perfect staircases: degree = #rounds + carry chain depth.

### 3. CRITICAL PAIRS at N=6 and N=8

sr=61 becomes SAT when specific W[60] bit PAIRS are freed:
- N=6: pairs (1,3) and (2,5) → SAT. 2/15 pairs.
- N=8: pair (4,5) → SAT. 1/28 pairs.
- All other pairs stay UNSAT.

The fraction shrinks: 13.3% → 3.6% with N. Original hypothesis that
pairs = sigma1 rotation positions was REFUTED at N=6 (predicted (3,4)
was UNSAT). The actual selection criterion is more subtle.

### 4. h IS DETERMINED by a-g at N=4

Exhaustive 2^32 enumeration: every input where registers a-g match also
has register h matching. The cascade-2 mechanism is AUTOMATIC from
cascade-1 + shift register propagation.

### 5. Algebraic Immunity > 4

Full h[0] polynomial at N=4: no degree-≤4 annihilators (rank 17902/17902).
Previous report of 3 annihilators was artifact of truncated monomial list.

### 6. Degree Correction

Per-round restriction test was WRONG (degree ~4 at N=8). Actual degrees
from exact ANF: 25-50% of max. Higher-order differential confirms > 19.

## Fleet Recommendations

1. **Server**: Build a carry-pattern enumerator at N=8. The 5.6-bit entropy
   at N=4 suggests ~20-30 bits at N=8 (scaling with N^2). If so, 2^30
   carry states × linear algebra = tractable collision finder.

2. **GPU laptop**: Test critical pairs at N=16 or N=20 if sr=61 UNSAT can
   be verified (may need longer timeout or CaDiCaL).

3. **All**: The a-register path (Sig0+Maj, T1+T2) is nearly linear once
   collision constraints are applied. This is the structural insight for
   building a faster sr=60 finder.

## What's Still Running

- Higher-order differential: 14+ hours, degree > 19 at N=8
- 3 kissat instances (sweep residuals)
- 6 cores free

— macbook
