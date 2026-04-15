# Session Summary: April 16, 2026

## Major New Finding: sr=61 Triplet Landscape

Kernel bit 3 at N=8 has **11 SAT triplets** (3 freed W[60] bits) for sr=61,
out of 56 tested. Fastest: (2,5,7) in 6.8s. This is 20% SAT rate.

For comparison:
- Pair (2 freed bits): 4 SAT out of 28 (14% at N=8)
- Triplet (3 freed bits): 11 SAT out of 56 (20% at N=8)
- At N=10: all 11 SAT triplets TIMEOUT at 600s (2^N penalty too strong)

## Full Kernel Critical Pair Map

| Kernel | Pairs (2-bit) | Triplets (3-bit) |
|--------|--------------|------------------|
| Bit 1 | 1 | untested |
| **Bit 3** | **4** | **11** |
| Bit 4 | 0 | untested |
| Bit 5 | 1 | untested |
| Bit 6 | 3 | untested |
| Bit 7 (MSB) | 1 | untested |

Bit 3 is the optimal kernel for sr=61 at N=8.

## Rapid-Fire Experiments (15 tasks, ~4 hours)

### Positive
- Full kernel critical pair map: 6 kernels × 28 pairs
- 11 SAT triplets for kernel bit 3
- Bit 1 of W[60] is "universal repair coordinate"

### Negative (equally important)
- BDD marginals: flat (no SAT backbone)
- Pairwise correlations: near-zero
- Mode-DP: perfectly injective
- T1 carry compression: 31x at N=4, 1.2x at N=8
- SDD compilation: intermediate blowup
- Rank-defect predictor: random baseline
- N=32 kernel bit 10: no candidate in 2^32 scan
- N=10 all triplets: TIMEOUT at 600s

## Running Now
- 9 Kissat seeds racing on top 3 N=10 triplets (no timeout, indefinite)
  - (2,5,7) × 3 seeds, (1,5,7) × 3 seeds, (0,1,2) × 3 seeds
  - Kernel bit 3, N=10
  - If ANY is SAT → sr=61 at N=10!

## Inspiration v7 Results
- Gemini: multi-block not dead (HW=28 is Wang standard), sigma1-aligned kernels
- GPT-5.4: SDD/d-DNNF, mode-DP compiler, carry-conditioned linearization
- Both: our negative results are real, BDD is publication-grade
