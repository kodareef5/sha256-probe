# Carry-Diff Structural Decomposition: The T2 Path is Near-Linear

## The a-path (T2) carries are 88% invariant

| Addition | Invariant carries | Fraction |
|----------|-------------------|----------|
| Sig0+Maj | 43/49 | **88%** |
| T1+T2 | 37/49 | **76%** |
| d+T1 | 30/49 | **61%** |

These three additions form the **a-path** (T2 computation → new a register
→ new e register via d+T1). The carry DIFFERENCES in this path are almost
entirely predetermined by the cascade structure.

## The T1 path carries are mostly FREE

| Addition | Invariant carries | Fraction |
|----------|-------------------|----------|
| +W (message) | 2/49 | **4%** |
| h+Sig1 | 5/49 | 10% |
| +Ch | 6/49 | 12% |
| +K (constant) | 12/49 | 24% |

Message word addition (+W) is the FREEST operation — 96% of its carry
diffs vary across collisions. This is where the collision's degrees of
freedom concentrate.

## Connection to macbook's findings

This confirms macbook's "a-path near-linearity" result from a completely
different angle:
- Macbook (algebraic): Sig0+Maj has degree 7 at N=8 (lowest)
- **Us (carry structure): Sig0+Maj carry diffs are 88% invariant**

Both say the same thing: the a-path is NEARLY LINEAR. The nonlinearity
concentrates in the T1 path through message word addition.

## Implication for collision finding

A carry-guided solver should:
1. FIX the 135 invariant carry-diff bits (free constraints)
2. Only SEARCH over the ~208 variable carry-diff bits
3. Of those 208, most are in the T1 path (+W, h+Sig1, +Ch)
4. The a-path (Sig0+Maj, T1+T2, d+T1) can be COMPUTED, not searched

This reduces the search dimension from 343 to ~208 carry-diff bits,
with the a-path essentially determined for free.

## Evidence level: VERIFIED (exact, all 260 N=8 collisions)
