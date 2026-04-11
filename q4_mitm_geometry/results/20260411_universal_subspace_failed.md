# Universal Subspace Hypothesis: FALSIFIED

## Summary

Tested whether the cascade_dw image at round 61 (varying W[60]) lives in
the **same** F_2 affine subspace across different prefixes. **It does not.**
Each prefix has its own subspace structure.

## Method

For 5 prefixes (CERT + 4 random), enumerated all 2^32 W[60] values,
computed cascade_dw at round 61, built F_2 basis from the resulting image.
Compared bases pairwise and computed union dimension.

## Results

| Prefix | Image size | log2 | Rank |
|---|---|---|---|
| CERT | 1,179,648 | 20.17 | 27 |
| RAND1 | 1,327,104 | 20.34 | 27 |
| RAND2 | 327,680 | 18.32 | 24 |
| RAND3 | 1,048,576 | 20.00 | 26 |
| RAND4 | 524,288 | 19.00 | 25 |

### Pairwise comparison vs CERT (rank 27)
| Other | Other rank | Intersection | Union |
|---|---|---|---|
| RAND1 | 27 | 23 | 31 |
| RAND2 | 24 | 19 | 32 |
| RAND3 | 26 | 24 | 29 |
| RAND4 | 25 | 21 | 31 |

**Global union of all 5 bases**: 32 (full space). No global linear constraint.

### Coset check
v0 differences in cert subspace:
- RAND1: NO
- RAND2: NO
- RAND3: **YES** (same coset!)
- RAND4: NO

Only RAND3's image lies in the same coset as CERT.

## Important corrections

The previous "25-dim subspace" finding (commit 7e285fc) was for a
**simplified g(e) function** that ignored the dh, dT2, dSig1 terms in
cascade_dw. The actual cascade_dw lives in a **27-dim subspace**.

The simplified g(e) used same `e` argument for both Ch terms — it was
computing a hypothetical, not the real round-61 differential. The real
differential has e_61_M1 ≠ e_61_M2 (de_61 = T1_M1 - T1_M2 ≠ 0).

## Implications

- **No universal precomputable filter exists** at the linear-subspace level
- **Per-prefix structure varies**: ranks 24-27 for the 5 prefixes tested
- **Image sizes vary 5x** even with similar ranks (different "fillings"
  of the subspace)
- **Image quantization**: many prefixes give image = 9 * 2^k, suggesting
  discrete spectrum from a 3 × 3 substructure

## Where this leaves us

The cascade_dw image is per-prefix. For sr=60 viability scanning, we need
either:
1. A cheaper-than-2^32 sketch of each prefix's subspace
2. A bias in prefix selection to maximize hit rate
3. A different approach entirely (e.g., reverse search from image)

## Reproducibility

`cascade_image_universal.c` — 5 prefixes × ~7 sec each on 24 cores.
