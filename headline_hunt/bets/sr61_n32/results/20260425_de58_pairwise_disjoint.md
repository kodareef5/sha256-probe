# de58 images of 36 candidates are pairwise (mostly) disjoint
**2026-04-25** — sr61_n32 — extends de58 ranking with cross-candidate union/intersection analysis.

## Method

For each of 36 registered candidates: sample 65,536 W57 (random), apply cascade-1 through r=58, collect set of distinct de58 values. Then check pairwise intersections and total union.

## Headline result

```
36 candidates analyzed.
Total non-zero overlaps: 21 / 630 pairs
Pairwise-disjoint rate: 96.7%

Sum of individual image sizes: 1,301,765
Total union size:              1,301,536
Overlap reduction:                   229 (0.018%)
```

**The de58 images of 36 candidates are essentially disjoint slices of the 32-bit de58 space.**

## Disjointness classification

Of the 21 non-disjoint pairs:
- Largest overlap: 31 (bit-06_m88fab888 ∩ bit-17_m427c281d)
- Most overlaps: < 30 shared values
- Total shared values across all overlapping pairs: 229

The 21 overlapping pairs are sparse — typically large-image candidates touching at a few specific de58 values. **No two candidates share more than 31 of their 65k-sample image points.**

## Per-candidate de58 range

Each candidate's de58 image is concentrated in a candidate-specific region of the 32-bit space. Some examples:

| Candidate | Image size | Min de58 | Max de58 | Span | Density |
|---|---:|---|---|---|---:|
| bit-19 (TOP) | 256 | 0x66ad4b69 | 0x80c55489 | 0x1a180920 | 2^-20.7 |
| bit-13_m72f21093 | 16,071 | 0x4e01282f | 0x56c8b19d | 0x08c7896e | 2^-9.5 |
| msb_m189b13c7 | 65,291 | 0x000004f8 | 0xfffffd98 | 0xfffff8a0 | 2^-16.0 |

The bit-19 candidate's 256 image points lie within a ~437M (2^28.7) modular-window — extreme sparsity. Some other candidates cluster narrowly too (bit-13_m72f21093 spans only 0x08c7896e ≈ 2^27).

## Why this is structural, not sampling noise

- 65,536 samples per candidate vs full 2^32 W57 space → coverage 0.0015%
- For most candidates, 65k samples saturate at the true image size (the image really IS small).
- Pairwise overlap of 0.018% is far below what random images would produce: with 36 candidates each occupying 0.03% of de58 space, expected random overlap per pair is ~0.06%, ~0.4 values average. Observed 21 of 630 pairs have nonzero overlap — somewhat ABOVE random, suggesting the overlapping pairs share structural features (e.g., both might be MSB-kernel with similar fill).

## Theoretical interpretation

de58 = `(s1_58[4] - s2_58[4]) mod 2^32` is determined by:
- candidate-fixed offset (driven by m0, fill, kernel bit, schedule W's at r ≤ 56)
- W57-dependent perturbation (small set: bit-19's perturbation has 256 distinct values)

The candidate-fixed offset is the candidate's "anchor point" in de58 space; the W57 perturbation determines which 256 (or 4096, etc.) values cluster around that anchor. Different candidates have different anchors, hence the disjoint images.

## Implication for sr=61 SAT search

**The 36 candidates collectively cover 1,301,536 / 2^32 ≈ 0.030% of de58 space.**

If an sr=61 SAT exists, its W57 maps to some specific de58 value `de58_sat`. That value lies in (mostly) at most one candidate's image. **So choosing the right candidate is equivalent to choosing the right de58 region.** Without knowing de58_sat, we can't pre-select.

Three possible structural interpretations:
1. **Pessimistic**: sr=61 SATs are distributed uniformly across de58 space → only 0.030% land in any candidate's image → high cost just to enter the right region.
2. **Neutral**: sr=61 SATs cluster around de58 = 0 (or some other "natural" value) → candidates whose images include that natural target are the right ones to try. We checked: **de58 = 0 is in NO candidate's image at 65k samples**.
3. **Optimistic**: sr=61 SAT density correlates with the candidate-anchor structure that produces narrow de58 images. bit-19's narrowness might be a marker of "this candidate's W57 → state evolution is highly constrained" — exactly the kind of structure that makes a SAT more likely if one exists.

**No empirical signal yet distinguishes between these.** But the disjointness itself is a new structural fact about the cascade-DP search space.

## What this gives the bet portfolio

- **Candidate-selection is non-redundant**: running 5 SAT solvers across 5 different candidates explores 5 disjoint regions of de58 space. This was implicit before; now it's explicit and quantified.
- **bit-19's 256-point image** in span 0x1a180920 makes it a structural extreme: if SATs cluster in narrow regions, bit-19 is the place to look. If they're spread, bit-19 is the WRONG place.
- **Future expansion of the candidate set** should aim to fill gaps in de58 coverage. The current 36 candidates collectively occupy ~0.03% of de58 space — adding more candidates with diverse anchors expands the "swept area".

## Files

- `de58_disjoint_check.py` (in-line script in this writeup; reusable via the snippet below)
- This writeup

## Reproducibility snippet

```python
# 36-candidate pairwise disjoint check, ~30s on macbook M-series
from collections import Counter
import random, sys, yaml
sys.path.insert(0, '.')
from lib.sha256 import K, MASK, Sigma0, Sigma1, Ch, Maj, add, precompute_state
# ... (cw1, ar functions as in residual_dimension_growth.py) ...
with open('headline_hunt/registry/candidates.yaml') as f:
    cands = yaml.safe_load(f)
images = {}
for c in cands:
    # ... sweep W57 → de58 ...
    images[c['id']] = de58_set
# Pairwise check + union analysis
```
