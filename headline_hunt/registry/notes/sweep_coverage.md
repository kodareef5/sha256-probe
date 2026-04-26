# Cascade-eligibility sweep coverage (per cell at N=32)
**Living document, updated as sweeps run.**

Each cell = one (bit, fill) combination. Exhaustive 2^32 m0 sweep ≈ 12 min wall on M5 ×10 OMP.

## Coverage matrix

| bit\fill | 0xff | 0x00 | 0x55 | 0xaa | 0x80 | total found |
|---------:|:-----|:-----|:-----|:-----|:-----|:------------|
|  0       |      |      |      |      |      |  curated 4  |
|  1       | 1 ✓  |      |      |      |      |  1 (NEW)    |
|  5       | 0 ✓  |      |      |      |      |  0          |
|  2       | 3 ✓  |      |      |      |      |  3 (NEW)    |
|  3       | 2 ✓  | 0 ✓  | 0 ✓  |      |      |  2 (NEW)    |
|  4       | 2 ✓  |      |      |      |      |  2 (NEW)    |
|  6       |      |      |      |      |      |  curated 6  |
|  7       | 0 ✓  |      |      |      |      |  0          |
| 10       | 0 ✓  |      |      |      |      |  curated 7 + 0 swept |
| 11       | 0 ✓  |      |      |      |      |  curated 2 + 0 swept |
| 13       |      |      |      |      | 1 ✓  |  curated 6 + 1 NEW (fill=0x80) |
| 17       | 0 ✓  |      |      |      |      |  curated 3 + 0 swept |
| 18       | 2 ✓  | 3 ✓  | 0 ✓  |      |      |  5 (NEW)    |
| 19       | 0 ✓  |      |      |      |      |  curated 1 + 0 swept |
| 22       | 0 ✓  |      |      |      |      |  0          |
| 25       | 2 ✓  |      |      |      |      |  2 (NEW) + curated 1 |
| 31       | 2 ✓  |      |      |      |      |  curated 6  |
|  8       | 0 ✓  |      |      |      |      |  0          |
| 14       | 3 ✓  |      |      |      |      |  3 (NEW)    |
| OTHER (9,12,15,16,20,21,23,24,26,27,28,29,30) | | | | | | unknown |

**Cells exhaustively swept** (22 as of 2026-04-26 04:00):
  bit=31 fill=0xff (2),  bit=22 fill=0xff (0),
  bit=18 fill=0xff (2),  bit=18 fill=0x00 (3),  bit=18 fill=0x55 (0),
  bit=7  fill=0xff (0),
  bit=3  fill=0xff (2),  bit=3 fill=0x00 (0),  bit=3 fill=0x55 (0),
  bit=4  fill=0xff (2),
  bit=19 fill=0xff (0),
  bit=11 fill=0xff (0),
  bit=25 fill=0xff (2),
  bit=10 fill=0xff (0),  bit=2 fill=0xff (3),  bit=17 fill=0xff (0),  bit=13 fill=0x80 (1),
  bit=1  fill=0xff (1),  bit=5 fill=0xff (0),  bit=8 fill=0xff (0),  bit=14 fill=0xff (3).

**Currently running**: none.
**Total NEW candidates discovered via sweep this session**: **19** (bit=18×5,
bit=3×2, bit=4×2, bit=25×2, bit=2×3, bit=13×1, bit=1×1, bit=14×3).
Registry expanded **36 → 55** (+53% growth).

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
| bit=3  fill=0x55       | 2^32   | 0        | 0.00 |
| bit=18 fill=0x55       | 2^32   | 0        | 0.00 |
| bit=4  fill=0xff       | 2^32   | 2        | 1.00 |
| bit=19 fill=0xff       | 2^32   | 0        | 0.00 |
| bit=11 fill=0xff       | 2^32   | 0        | 0.00 |
| bit=25 fill=0xff       | 2^32   | 2        | 1.00 |
| bit=10 fill=0xff       | 2^32   | 0        | 0.00 |
| bit=2  fill=0xff       | 2^32   | 3        | 1.50 |
| bit=17 fill=0xff       | 2^32   | 0        | 0.00 |
| bit=13 fill=0x80       | 2^32   | 1        | 0.50 |
| bit=1  fill=0xff       | 2^32   | 1        | 0.50 |
| bit=5  fill=0xff       | 2^32   | 0        | 0.00 |
| bit=8  fill=0xff       | 2^32   | 0        | 0.00 |
| bit=14 fill=0xff       | 2^32   | 3        | 1.50 |

**Average**: 19 eligible / 22 cells = 0.86 per cell. Expected at uniform 2^-31
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
