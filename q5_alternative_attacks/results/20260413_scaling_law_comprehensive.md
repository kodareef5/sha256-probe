# Comprehensive Scaling Law — Odd-Even Divergence Discovery

Date: 2026-04-13 03:30 UTC

## Complete Data (best kernel + fill per N)

| N | Best coll | log2 | Fill | Kernel bit | Parity |
|---|----------|------|------|-----------|--------|
| 4 | 146 | 7.19 | standard | 1 | even |
| **5** | **1024** | **10.00** | **alternating** | 0 | **ODD** |
| 6 | 83 | 6.38 | standard | 4 | even |
| **7** | **373** | **8.54** | standard | 1 | **ODD** |
| 8 | 1644 | 10.68 | standard | 6 | even |
| **9** | **14,263** | **13.80** | **alternating** | 1 | **ODD** |
| 10 | 1467 | 10.52 | standard | 8 | even |

## Scaling Laws

### Odd N: log2(C) = 0.950 × N + 4.13
- Growth: 2^0.95 ≈ 1.93 per unit N
- Predictions: N=11 → 24,509, N=33 → 4.8×10^10

### Even N: log2(C) = 0.715 × N + 3.69
- Growth: 2^0.715 ≈ 1.64 per unit N
- Predictions: N=12 → 4,923, N=32 → 9.9×10^7

### Divergence
- Odd slope 33% steeper than even slope
- At N=32/33: odd-N has ~500x more collisions
- The alternating fill pattern activates different collision mechanisms at odd N

## N mod 4 Hypothesis

N=5 (1 mod 4): alternating fill gives 27.7x boost
N=7 (3 mod 4): alternating fill gives NO boost
N=9 (1 mod 4): alternating fill gives 2.9x boost

**Prediction: alternating fill helps at N ≡ 1 mod 4 but NOT N ≡ 3 mod 4**

Testing: N=11 ≡ 3 mod 4 → predict alternating fill gives minimal boost.

## Implications for SHA-256 (N=32)

Even-N scaling predicts ~10^8 sr=60 collisions at N=32.

If correct, the collision search space is 2^26.6, not 2^128.
Combined with de-pruning (2^3 effective search), the actual
difficulty could be as low as 2^30 = ~10^9 evaluations.

At 2B/s GPU: ~0.5 seconds to find an sr=60 collision.

**Caveat**: These are EXTRAPOLATIONS from N≤10 mini-SHA data.
The scaling law may break at larger N due to structural changes
in SHA-256's rotation/schedule behavior.

## de-set Scaling (independent confirmation)

| N | |de58| | Effective search | Full search |
|---|--------|----------------|-------------|
| 4 | 2 | 2^1 | 2^16 |
| 6 | 8 | 2^3 | 2^24 |
| 8 | 8 | 2^3 | 2^32 |

de-set scaling predicts 2^3 effective search at ALL even N.
If true: collision finding is POLYNOMIAL TIME.

The de-set and collision-count scaling laws independently suggest
that sr=60 collision difficulty grows much slower than exponentially.
