# W1[57] Hotspot Analysis: N=8 vs N=12

## N=8 (260 collisions, exhaustive)
- 152/256 W1[57] values produce collisions (59.4%)
- Count range: 1-5 per value (uniform)
- Correlation with upper bits: r ≈ 0.07 (NEGLIGIBLE)
- No predictive power from W1[57] bit patterns

## N=12 (303+ collisions so far, 13% complete)
- 33/34 tested W1[57] values produce collisions (97%)
- Count range: 0-21 per batch (highly skewed)
- Correlation with upper 6 bits: r = +0.745 (STRONG)
- Upper bits of W1[57] strongly predict collision count

## Interpretation

The hotspot structure EMERGES at larger N:
- N=8: relatively uniform distribution
- N=12: highly skewed, upper bits matter

This likely reflects carry chain effects: at larger N, the upper bits
interact with more carry positions through Sigma1 rotations, creating
structural coupling that makes some W1[57] values much more productive.

The predictor is N-specific, NOT transferable across widths.
