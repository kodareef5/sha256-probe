# Prefix Viability Scan: 16 Random Prefixes, 0 Viable

## Summary

For 16 random prefixes, computed cascade_dw image at round 61 and tested
whether dW61_target ∈ image. **0/16 viable.** Mean image size 4.07M
(0.095% of 2^32). Expected viable rate per scan ≈ 0.1%.

## Method

For each prefix W[57..59]:
1. Compute round-60 state (s1c, s2c, C60)
2. Compute dW61_target = sigma1(W2[59]) - sigma1(W1[59]) + sched_const_diff
3. Enumerate all 2^32 W[60], compute cascade_dw at round 61
4. Check if any W[60] gives cascade_dw == target

## Results (cert verified first; image=1,179,648, matches=8192)

| # | W57, W58, W59 | Image | Matches |
|---|---|---|---|
| 0 | 0xa4214591, 0x3f3e435a, 0x5c03a95c | **1,179,648** | 0 |
| 1 | 0x2966790e, 0xb573367c, 0x583bcf10 | 737,280 | 0 |
| 2 | 0xba867c8e, 0x861393f7, 0x67a5a910 | **33,423,360** | 0 |
| 3 | 0xb3a6a642, 0xc0bc3b8e, 0x77b06079 | 196,608 | 0 |
| 4 | 0xe4ba3ef9, 0xb1abd4c4, 0xd47f326d | 608,256 | 0 |
| 5 | 0xbcc4f749, 0xd9a78ce7, 0x04171a3e | 2,515,456 | 0 |
| 6 | 0x098a7b8a, 0x7f8ccdfd, 0x09b30b26 | 1,048,576 | 0 |
| 7 | 0xc56664b0, 0x6b118479, 0x0b4b9931 | 884,736 | 0 |
| 8 | 0x901b6243, 0x0f25a447, 0x67441ecf | 524,288 | 0 |
| 9 | 0xe330c532, 0xac11a838, 0xc6f48568 | 1,036,800 | 0 |
| 10 | 0x38313662, 0xa3dc8c8e, 0x4407d617 | 345,600 | 0 |
| 11 | 0x9b4ebc7b, 0x03de5fc3, 0x20ce73bc | 524,288 | 0 |
| 12 | 0x11d2805b, 0x506c539b, 0x90530dfc | 294,912 | 0 |
| 13 | 0xd7c154e7, 0x81bb0f8e, 0x17a85a11 | **1,179,648** | 0 |
| 14 | 0x7719aee5, 0xcdb084f8, 0xab77dbf1 | 1,769,472 | 0 |
| 15 | 0x4ea5e806, 0x64ee6256, 0x55d1eb12 | **18,874,368** | 0 |

## Observations

1. **Image sizes span 170x range** (196,608 to 33,423,360)
2. **Cert image (1,179,648) replicated by 2 random prefixes** (#0, #13).
   Cert image = 9 × 2^17. Prefix #15 image = 18,874,368 = 16 × cert image.
3. **Discrete factorization**: many image sizes are small-integer multiples
   of powers of 2 (e.g., 9 × 2^k, 5 × 9 × 2^k)
4. **Mean image / 2^32 ≈ 0.095%** → expected 0/16 viable hits is consistent

## Implications

- To find one viable random prefix, need ~1000 prefixes scanned
  (~7 sec/prefix * 1000 = 2 hours)
- The discrete image-size spectrum hints at structure we don't yet understand
- Prefixes with image = exactly cert size are interesting — investigate if
  they're "cert-like" structurally

## Next experiments

1. Larger viability scan (~500 prefixes) to find ANY viable random prefix
2. Investigate why image sizes are quantized
3. Bias prefix sampling toward "cert-like" structure to increase hit rate
