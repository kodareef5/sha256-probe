# 256-Prefix Viability Scan: 0/256, Image Distribution Analysis

## Summary

Tested 256 random prefixes for sr=60 viability via cascade_dw round-61
closure check. **0/256 viable.** Image sizes span 13-26 powers of 2.
Hamming-weight features are weak predictors of image size (best |r|=0.215).

Image sizes show **discrete factorization**: all are products of small
primes (3, 5, 17, ...) and powers of 2.

## Method

For each prefix W[57..59]:
1. Compute round-60 state of M1, M2 (cert kernel: dM[0]=dM[9]=0x80000000)
2. Compute dW61_target from prefix W[59] and prefix-fixed schedule consts
3. Enumerate all 2^32 W[60], compute cascade_dw at round 61
4. Count distinct outputs (image size) and matches against target (viability)

`prefix_viability_scan.c` 256 prefixes, ~14 minutes on 24 cores.

## Results

| Statistic | Value |
|---|---|
| Viable prefixes | **0 / 256** |
| Mean image size | 1,599,060 (0.037% of 2^32) |
| Median image size | ~786,432 |
| Min image size | 8,192 (2^13) |
| Max image size | 48,660,480 (2^25.5) |
| Distinct image sizes | 106 |

### Top 10 most common image sizes
| Image | log2 | Factorization | Count |
|---|---|---|---|
| 786,432 | 19.58 | 3 × 2^18 | 10 |
| 196,608 | 17.58 | 3 × 2^16 | 10 |
| 524,288 | 19.00 | 2^19 | 9 |
| 1,572,864 | 20.58 | 3 × 2^19 | 9 |
| 131,072 | 17.00 | 2^17 | 9 |
| 1,048,576 | 20.00 | 2^20 | 8 |
| 589,824 | 19.17 | 9 × 2^16 | 7 |
| 294,912 | 18.17 | 9 × 2^15 | 7 |
| 2,097,152 | 21.00 | 2^21 | 7 |
| 1,179,648 | 20.17 | **9 × 2^17 ← cert** | **7** |

7 of 256 random prefixes (2.7%) have EXACTLY cert's image size of
1,179,648 = 9 × 2^17. This is much higher than expected from a continuous
distribution — suggests structural quantization.

## Discrete factorization

All 106 distinct image sizes have form `2^k × odd_part`. The distribution
of odd_parts:

| odd_part | count | factorization |
|---|---|---|
| 1 | 9 | 1 |
| 3 | 9 | 3 |
| 5 | 9 | 5 |
| 9 | 8 | 3² |
| 15 | 7 | 3·5 |
| 17 | 5 | **17 (Fermat prime)** |
| 25 | 4 | 5² |
| 27 | 6 | 3³ |
| 33 | 1 | 3·11 |
| 45 | 6 | 3²·5 |
| 65 | 2 | 5·13 |
| 75 | 6 | 3·5² |
| 81 | 4 | 3⁴ |
| 85 | 2 | 5·17 |
| ... | | |
| 8481 | 1 | 3·11·257 (257 = Fermat prime) |

The dominant primes are **3, 5, 17, 257** — all Fermat primes (or 3).
This strongly suggests cascade_dw at round 61 has a structural
relationship to **multiplicative groups mod Fermat primes** — possibly
arising from sigma1's rotation pattern (17, 19, 10) interacting with
mod-2^32 arithmetic.

## Hamming weight correlations

Linear correlation of log2(image) vs HW features at round 60:

| Feature | Range | r | Notes |
|---|---|---|---|
| hw_de60 | 12-27 | +0.215 | Mild positive (gpu-laptop's hw(f_xor)) |
| hw_df60 | 9-25 | +0.052 | Negligible |
| hw_dg60 | 7-20 | -0.151 | Mild negative |
| hw_dh60 | 16 const | 0.000 | Constant (h60 = e_57 fixed by prefix-pre) |
| hw_C60 | 10-23 | +0.054 | Negligible |

Best single predictor (hw_de60) explains only ~5% of variance. Image
size is determined by deeper structure than HW features.

### Mean log2(image) by hw_de60

| hw_de60 | n | mean log2 |
|---|---|---|
| 14 | 24 | 18.53 |
| 16 | 47 | 19.22 |
| 18 | 47 | 19.72 |
| 20 | 16 | 20.26 |
| 22 | 4 | 19.62 |
| 24 | 2 | 18.67 |
| 27 | 1 | **25.54 ← largest in scan** |

Mild upward trend but huge within-bucket variance (4-8 powers of 2).

## Largest images (top 10)

| Image | log2 | hw_de60 | hw_df60 | hw_dg60 |
|---|---|---|---|---|
| 48,660,480 | 25.54 | 27 | 16 | 10 |
| 11,796,480 | 23.49 | 18 | 22 | 10 |
| 11,141,120 | 23.41 | 18 | 18 | 11 |
| 10,485,760 | 23.32 | 19 | 18 | 11 |
| 10,485,760 | 23.32 | 16 | 16 | 11 |
| 9,437,184 | 23.17 | 20 | 15 | 9 |
| 9,437,184 | 23.17 | 16 | 19 | 13 |
| 8,847,360 | 23.08 | 21 | 17 | 11 |
| 8,684,544 | 23.05 | 18 | 17 | 11 |
| 8,388,608 | 23.00 | 17 | 14 | 8 |

Largest image (48M) has unique features (hw_de60=27). Worth investigating
this specific prefix.

## Implications

1. **Viable rate is low (~0.04%)**: need ~2500 random prefixes for 1
   viable. 1024-prefix scan running, ETA ~1 hour.

2. **No simple HW predictor**: hw alone doesn't predict image size; need
   structural analysis.

3. **Image quantization is striking**: factor of 17 (Fermat prime) appears
   in some image sizes — investigate WHY structurally.

4. **Cert image size (9 × 2^17) is COMMON**: 7/256 prefixes share it.
   These prefixes might form a "cert-equivalence class" — investigate
   their structural relationship.

5. **vs gpu-laptop's claim**: their finding that "lower hw(f_xor) → smaller
   image" applies to SIMPLIFIED Ch-only model. For FULL cascade_dw,
   correlation is weak (r=-0.15 for hw_dg60, +0.21 for hw_de60). Smaller
   image = LESS viable (not more) for sr=60.

## Reproducibility

- `prefix_viability_scan.c` (full enumeration version)
- `prefix_image_correlator.c` (extracts features from scan output)
- Raw data: `/tmp/correlator_full.txt`

## Next experiments

1. Wait for 1024 scan (in progress) — find any viable random prefix
2. Investigate the 7 cert-image-size prefixes — what makes them equivalent?
3. Compute basis structure of the largest-image prefix (48M) — what's
   different about it?
4. Test bit-2 kernel candidate (gpu-laptop's HW=103 finding) for image
   structure
5. Investigate the Fermat prime connection to image factorization
