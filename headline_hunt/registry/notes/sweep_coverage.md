# Cascade-eligibility sweep coverage (per cell at N=32)
**Living document, updated as sweeps run.**

Each cell = one (bit, fill) combination. Exhaustive 2^32 m0 sweep ≈ 12 min wall on M5 ×10 OMP.

## Coverage matrix

| bit\fill | 0xff | 0x00 | 0x55 | 0xaa | 0x80 | total found |
|---------:|:-----|:-----|:-----|:-----|:-----|:------------|
|  0       |      |      |      |      |      |  curated 4  |
|  3       | 2 ✓  | 0 ✓  | run  |      |      |  2 (NEW)    |
|  4       | run  |      |      |      |      |  ?          |
|  6       |      |      |      |      |      |  curated 6  |
|  7       | 0 ✓  |      |      |      |      |  0          |
| 10       |      |      |      |      |      |  curated 7  |
| 11       |      |      |      |      |      |  curated 2  |
| 13       |      |      |      |      |      |  curated 6  |
| 17       |      |      |      |      |      |  curated 3  |
| 18       | 2 ✓  | 3 ✓  | run  |      |      |  5 (NEW)    |
| 19       |      |      |      |      |      |  curated 1  |
| 22       | 0 ✓  |      |      |      |      |  0          |
| 25       |      |      |      |      |      |  curated 1  |
| 31       | 2 ✓  |      |      |      |      |  curated 6  |
| OTHER (1,2,5,8,9,12,14,15,16,20,21,23,24,26,27,28,29,30) | | | | | | unknown |

**Cells exhaustively swept**: 7 (bit=31, 22, 18-{0xff,0x00}, 7, 3-{0xff,0x00}).
**Currently running**: bit=3 fill=0x55, bit=18 fill=0x55, bit=4 fill=0xff.
**Total NEW candidates discovered via sweep this session**: 7 (across 4 productive cells).

## Per-cell statistics

| Cell                   | trials | eligible | rate (× 2^-31) |
|:-----------------------|-------:|---------:|---------------:|
| bit=31 fill=0xff       | 2^32   | 2        | 1.00 |
| bit=22 fill=0xff       | 2^32   | 0        | 0.00 |
| bit=18 fill=0xff       | 2^32   | 2        | 1.00 |
| bit=18 fill=0x00       | 2^32   | 3        | 1.50 |
| bit=7  fill=0xff       | 2^32   | 0        | 0.00 |
| bit=3  fill=0xff       | 2^32   | 2        | 1.00 |
| bit=3  fill=0x00       | 2^32   | 0        | 0.00 |

**Average**: 9 eligible / 7 cells = 1.29 per cell. Expected at uniform 2^-31
baseline = 2 per cell. Observed slightly LOWER, but consistent with Poisson(2)
variance which has 14% chance of 0 per cell.

**Empirical refinement to candidate-base expansion estimate**: Expected
total candidates per (bit, fill) cell = 1.29. With 32 bits × 5 fills = 160
cells, expected total ≈ 207 candidates (vs naive 320 estimate). The 36
already-registered cover ~17% of the space.

## Implications

1. The 36-candidate registry is consistent with covering ~28 cells out of 160
   total. Most cells are unprobed.
2. Full coverage at ~12 min/cell × 160 cells = ~32 hr compute on M5 ×10 threads.
3. Expected total post-full-sweep: ~207 candidates registered. Current: 43.
4. Per-bit expected: ~1.29 × 5 fills ≈ 6.5 candidates per bit on average.
   Variance: some bits will have 0-1, others 9-10.

## Update protocol

When a sweep finishes:
1. Update the matrix above with the eligible count.
2. Register each new m0 in candidates.yaml + generate CNF + audit.
3. Update kernels.yaml if a new bit position appears.
4. Commit with message `[registry] bit=X fill=Y sweep: N eligible (registry +K)`.
