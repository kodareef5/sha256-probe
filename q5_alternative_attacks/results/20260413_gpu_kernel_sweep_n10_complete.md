# GPU Kernel Sweep — N=10 Complete (First-Found Candidates)

Date: 2026-04-13 00:00 UTC
Device: NVIDIA GeForce RTX 4070 Laptop GPU (torch.compile, 2.8B eval/s)
Total time: 67 min (10 bits × ~400s)

## Results

| Bit | M[0] | Fill | Collisions | log2 | Time |
|-----|------|------|-----------|------|------|
| 0 | 0xa5 | 0x3ff | 1098 | 10.10 | 407s |
| 1 | 0x1b2 | 0x3ff | 957 | 9.90 | 394s |
| 2 | 0x84 | 0x3ff | 604 | 9.24 | 394s |
| 3 | 0x63 | 0x3ff | **1316** | **10.36** | 407s |
| 4 | 0x27 | 0x55 | 923 | 9.85 | 410s |
| 5 | 0x3d5 | 0x1ff | 884 | 9.79 | 410s |
| 6 | 0x11 | 0x3ff | 1064 | 10.06 | 400s |
| **7** | **0x1a2** | **0x3ff** | **1443** | **10.49** | 417s |
| 8 | 0x345 | 0x3ff | 1226 | 10.26 | 395s |
| 9 (MSB) | 0x34c | 0x3ff | 946 | 9.89 | 405s |

## Key Findings

1. **Best kernel: bit 7** (1443 collisions, 1.53x over MSB)
2. **Bit 3 is strong**: 1316 collisions (1.39x over MSB)
3. **MSB (bit 9) gives 946** — matches known result exactly
4. **Worst: bit 2** with 604 collisions

## Optimal kernel evolution

| N | Best bit | Best coll | MSB coll | Improvement |
|---|---------|----------|---------|-------------|
| 4 | 1 | 146 | 49 | 3.0x |
| 5 | 0 | 37 | 0 | ∞ |
| 6 | 4 | 83 | 50 | 1.7x |
| 7 | 1 | 373 | 0 | ∞ |
| 8 | 6 | 1644 | 260 | 6.3x |
| **10** | **7** | **1443** | **946** | **1.5x** |

**The optimal kernel bit position depends on N.** No single bit is universally best.
At N=10, the improvement from kernel optimization (1.5x) is much smaller than
at N=8 (6.3x), suggesting the optimal-kernel advantage may diminish with N.

## Caveats

- These are FIRST-FOUND candidates. Multi-candidate sweep (testing all da56=0
  candidates) could change rankings. At N=8, candidate choice caused 22x
  variation for bit 4.
- N=10 multi-candidate sweep (~10 min per candidate × ~5 candidates × 10 bits
  = ~8 hours) would give definitive results.

## Best-kernel scaling law (updated)

With N=10 data point (first-found, not necessarily optimal):

| N | Best coll (1st-found) | log2 |
|---|----------------------|------|
| 4 | 146 | 7.19 |
| 6 | 83 | 6.37 |
| 8 | 1644 | 10.68 |
| 10 | 1443 | 10.49 |

Note: N=10 first-found (1443) is LESS than N=8 best-of-all (1644).
This suggests N=10 multi-candidate could reveal significantly more collisions.
