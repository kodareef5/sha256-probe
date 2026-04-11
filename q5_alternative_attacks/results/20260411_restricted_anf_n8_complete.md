# Restricted ANF at N=8: Complete 64-Bit Degree Table

**Date**: 2026-04-11
**Evidence level**: VERIFIED (exact Moebius transform, 2^32 entries per bit)
**Fixed values**: W1[58]=0x42, W1[59]=0x7a, W2[58]=0x3f, W2[59]=0x91

## Key Finding: d[0] is the WEAKEST bit (degree 7, 251 monomials)

| Register | Deg[0] | Deg[7] | Mono[0] | Mono[7] | Pattern |
|----------|--------|--------|---------|---------|---------|
| d        | **7**  | 14     | **251** | 25,411  | Staircase +1/bit |
| h        | 8      | 15     | 266     | 27,648  | Staircase +1/bit |
| c        | 14     | 15     | 15,701  | 65,491  | Near-max |
| g        | 14     | 16     | 15,047  | 65,096  | Near-max |
| a,b,e,f  | 15-16  | 15-16  | 62K-66K | 65K-66K | Full-degree |

## The Staircase Pattern

d and h registers show a perfect staircase: degree increases by
exactly 1 per bit position. This is the carry chain signature —
bit k depends on k carry layers from the additions below it.

d[0] = degree 7 because it passes through 7 rounds of additions
at the LSB position where no carries propagate from below.

## Comparison with N=4 Full ANF

At N=4 (32 free vars, all words free):
  h[0] = degree 8, 1173 monomials
  d[0] = degree 9, 1782 monomials

At N=8 restricted (32 free vars, cascade words only):
  h[0] = degree 8, 266 monomials (SPARSER than N=4)
  d[0] = degree 7, 251 monomials (LOWER degree AND sparser)

Fixing W[58],W[59] to constants dramatically reduces monomials
without changing the degree scaling. The degree is determined by
the number of free variables and carry chain depth, not word width.

## Degree = 7 rounds of additions at LSB

d[0] degree = 7 = exactly the number of tail rounds (57-63).
This is NOT a coincidence — it means d[0] is degree-1 per round,
which is the minimum for a non-trivial function of addition carries.

h[0] degree = 8 = 7 rounds + 1 extra degree from the Ch/Maj
nonlinearity. The extra degree comes from the e-path injection.
